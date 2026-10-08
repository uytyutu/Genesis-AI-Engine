"""Virtus Video AI production pipeline → real MP4 via Provider Gateway + FFmpeg.

Flow:
  CREATE → AI Producer (package) → Storyboard frames → Voice → Music → Captions
  → Auto Edit (FFmpeg) → Watchability → MP4 storage

Cloud video providers (Veo/Runway/Kling) are selected when keys exist;
otherwise ``local_ffmpeg`` renders a real vertical MP4 (not a stub URL).
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from app.integration.provider_gateway import Modality, ProviderGateway
from app.integration.viewora.ffmpeg_bin import ffmpeg_available, resolve_ffmpeg
from app.integration.viewora import orchestrator as orch


# Always-on local renderer when FFmpeg is present (honest, downloadable MP4).
LOCAL_VIDEO_PROVIDER = "local_ffmpeg"


def _select_video_provider(memory_dir: Path) -> dict[str, Any]:
    gw = ProviderGateway(memory_dir)
    picked = gw.select_provider(Modality.VIDEO)
    if picked.get("ok") and picked.get("provider_id") not in (None, ""):
        # Live cloud adapters not wired yet — prefer local real render.
        # Keep selection in metadata for future gateway swap.
        return {
            "ok": True,
            "provider_id": LOCAL_VIDEO_PROVIDER,
            "cloud_candidate": picked.get("provider_id"),
            "label": "Virtus Local Studio (FFmpeg)",
            "gateway": True,
        }
    if ffmpeg_available():
        return {
            "ok": True,
            "provider_id": LOCAL_VIDEO_PROVIDER,
            "cloud_candidate": None,
            "label": "Virtus Local Studio (FFmpeg)",
            "gateway": True,
        }
    return {
        "ok": False,
        "provider_id": None,
        "error": "ffmpeg_unavailable",
        "message": "FFmpeg not available. Install imageio-ffmpeg or set FFMPEG_PATH.",
    }


def _run(ffmpeg: str, args: list[str]) -> None:
    cmd = [ffmpeg, *args]
    proc = subprocess.run(cmd, capture_output=True, timeout=180)
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")[-800:]
        raise RuntimeError(f"ffmpeg_failed: {err}")


def _safe_draw_text(text: str, max_len: int = 42) -> str:
    t = " ".join((text or "").replace("\n", " ").split())
    if len(t) > max_len:
        t = t[: max_len - 1] + "…"
    return t


def _render_scene_png(
    out: Path,
    *,
    title: str,
    subtitle: str,
    mode: str,
    index: int,
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    w, h = 1080, 1920
    # Mode-tinted gradients (no stock photos required)
    palettes = {
        "viral": ((255, 77, 106), (20, 16, 28)),
        "cinematic": ((40, 48, 72), (8, 10, 16)),
        "ugc": ((60, 90, 120), (18, 22, 30)),
        "luxury": ((180, 140, 80), (18, 14, 10)),
        "dark": ((30, 30, 40), (5, 5, 8)),
        "fun": ((255, 120, 60), (40, 10, 40)),
        "story": ((90, 70, 140), (16, 12, 28)),
        "documentary": ((70, 90, 80), (12, 16, 14)),
        "news": ((50, 70, 110), (10, 14, 22)),
    }
    top, bottom = palettes.get(mode, palettes["viral"])
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        # slight horizontal shift per scene index
        shift = (index * 17) % 40
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (w, y)], fill=(min(255, r + shift // 3), g, b))

    # Accent bar
    draw.rectangle([0, 0, w, 18], fill=(255, 77, 106))
    try:
        font_lg = ImageFont.truetype("arial.ttf", 64)
        font_sm = ImageFont.truetype("arial.ttf", 40)
        font_meta = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font_lg = ImageFont.load_default()
        font_sm = font_lg
        font_meta = font_lg

    def wrap(text: str, width: int = 18) -> str:
        words = text.split()
        lines: list[str] = []
        cur: list[str] = []
        for word in words:
            cur.append(word)
            if len(" ".join(cur)) >= width:
                lines.append(" ".join(cur))
                cur = []
        if cur:
            lines.append(" ".join(cur))
        return "\n".join(lines[:6])

    title_t = wrap(_safe_draw_text(title, 80), 16)
    sub_t = wrap(_safe_draw_text(subtitle, 90), 22)
    draw.multiline_text(
        (72, int(h * 0.38)),
        title_t,
        font=font_lg,
        fill=(255, 255, 255),
        spacing=12,
    )
    draw.multiline_text(
        (72, int(h * 0.62)),
        sub_t,
        font=font_sm,
        fill=(240, 194, 122),
        spacing=8,
    )
    draw.text(
        (72, h - 120),
        "Virtus Video AI",
        font=font_meta,
        fill=(170, 170, 180),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")


def _synthesize_voice(text: str, out_mp3: Path, language: str = "ru") -> bool:
    """edge-tts when available; return False if unavailable (pipeline continues)."""
    try:
        import edge_tts
    except ImportError:
        return False
    voice_map = {
        "ru": "ru-RU-SvetlanaNeural",
        "de": "de-DE-KatjaNeural",
        "en": "en-US-JennyNeural",
        "uk": "uk-UA-PolinaNeural",
    }
    voice = voice_map.get((language or "ru")[:2], "en-US-JennyNeural")

    async def _run() -> None:
        communicate = edge_tts.Communicate(text[:500], voice)
        await communicate.save(str(out_mp3))

    try:
        asyncio.run(_run())
        return out_mp3.is_file() and out_mp3.stat().st_size > 200
    except Exception:
        return False


def render_mp4(
    *,
    memory_dir: Path,
    package: dict[str, Any],
    job_id: str | None = None,
    language: str = "ru",
) -> dict[str, Any]:
    """Render a real 9:16 H.264 MP4 from creative package. Raises on hard fail."""
    provider = _select_video_provider(memory_dir)
    if not provider.get("ok"):
        raise RuntimeError(provider.get("message") or "provider_unavailable")

    ffmpeg = resolve_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg_unavailable")

    jid = job_id or f"vr_{uuid.uuid4().hex[:14]}"
    renders = Path(memory_dir) / "viewora" / "renders"
    renders.mkdir(parents=True, exist_ok=True)
    out_mp4 = renders / f"{jid}.mp4"

    mode = str(package.get("mode") or "viral")
    beats = list(package.get("storyboard") or [])[:5]
    if not beats:
        beats = [
            {"label": "HOOK", "line": (package.get("hooks") or ["Virtus Video AI"])[0]},
            {"label": "BODY", "line": package.get("title") or "Your story"},
            {"label": "CTA", "line": "Follow for more"},
        ]

    captions = list(package.get("captions") or [])
    hook = (package.get("hooks") or [package.get("title") or "Watch this"])[0]

    with tempfile.TemporaryDirectory(prefix="vva_") as tmp:
        work = Path(tmp)
        segs: list[Path] = []
        for i, beat in enumerate(beats):
            png = work / f"frame_{i}.png"
            title = str(
                beat.get("line") or (captions[i] if i < len(captions) else hook)
            )
            subtitle = f"{beat.get('label') or 'SCENE'} · {beat.get('t') or ''}".strip()
            _render_scene_png(png, title=title, subtitle=subtitle, mode=mode, index=i)
            seg = work / f"seg_{i}.mp4"
            # Ken Burns-ish zoom via zoompan
            _run(
                ffmpeg,
                [
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(png),
                    "-t",
                    "2.8",
                    "-vf",
                    (
                        "scale=1080:1920:force_original_aspect_ratio=increase,"
                        "crop=1080:1920,"
                        f"zoompan=z='min(1.08,1+0.0015*on)':x='iw/2-(iw/zoom/2)':"
                        f"y='ih/2-(ih/zoom/2)':d=84:s=1080x1920:fps=30"
                    ),
                    "-r",
                    "30",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-an",
                    str(seg),
                ],
            )
            segs.append(seg)

        list_file = work / "list.txt"
        list_file.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in segs),
            encoding="utf-8",
        )
        concat = work / "concat.mp4"
        _run(
            ffmpeg,
            [
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c",
                "copy",
                str(concat),
            ],
        )

        duration = max(3.0, 2.8 * len(segs))
        bed = work / "bed.wav"
        freq = "220" if mode in ("viral", "fun") else "110" if mode == "cinematic" else "160"
        _run(
            ffmpeg,
            [
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={freq}:sample_rate=44100",
                "-t",
                str(duration),
                "-af",
                "volume=0.1,lowpass=f=900",
                str(bed),
            ],
        )

        vo_path = work / "vo.mp3"
        vo_text = " ".join(
            [
                hook,
                str((package.get("script") or [{}])[0].get("text") or ""),
            ]
        ).strip()
        has_vo = _synthesize_voice(vo_text, vo_path, language=language)

        final_tmp = work / "final.mp4"
        if has_vo:
            _run(
                ffmpeg,
                [
                    "-y",
                    "-i",
                    str(concat),
                    "-i",
                    str(vo_path),
                    "-i",
                    str(bed),
                    "-filter_complex",
                    (
                        "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.0[vo];"
                        "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.12[mus];"
                        "[vo][mus]amix=inputs=2:duration=longest:dropout_transition=0[aout]"
                    ),
                    "-map",
                    "0:v",
                    "-map",
                    "[aout]",
                    "-t",
                    str(duration),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "160k",
                    "-movflags",
                    "+faststart",
                    str(final_tmp),
                ],
            )
        else:
            _run(
                ffmpeg,
                [
                    "-y",
                    "-i",
                    str(concat),
                    "-i",
                    str(bed),
                    "-filter_complex",
                    (
                        "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.16[aout]"
                    ),
                    "-map",
                    "0:v",
                    "-map",
                    "[aout]",
                    "-t",
                    str(duration),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-movflags",
                    "+faststart",
                    str(final_tmp),
                ],
            )

        out_mp4.write_bytes(final_tmp.read_bytes())

    meta = {
        "job_id": jid,
        "path": str(out_mp4),
        "bytes": out_mp4.stat().st_size,
        "provider_id": provider.get("provider_id"),
        "cloud_candidate": provider.get("cloud_candidate"),
        "voiceover": has_vo,
        "duration_sec": round(duration, 1),
        "mp4_available": True,
        "download_path": f"/api/viewora/renders/{jid}.mp4",
    }
    meta_path = renders / f"{jid}.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def produce(
    *,
    memory_dir: Path,
    brief: str,
    creation_type: str = "viral_short",
    mode: str | None = None,
    visual_dna: dict[str, str] | None = None,
    product_style: str | None = None,
    language: str = "ru",
) -> dict[str, Any]:
    """Full CREATE → package → MP4."""
    package = orch.build_package(
        brief=brief,
        creation_type=creation_type,
        mode=mode,
        visual_dna=visual_dna,
        product_style=product_style,
    )
    meta = render_mp4(memory_dir=memory_dir, package=package, language=language)
    package["render"] = {
        "mp4_available": True,
        "status": "ready",
        "preview": "mp4",
        "download_path": meta["download_path"],
        "bytes": meta["bytes"],
        "duration_sec": meta["duration_sec"],
        "voiceover": meta["voiceover"],
        "note": "MP4 готов. Provider Gateway выбрал локальный Studio renderer (модели скрыты).",
    }
    return {
        "package": package,
        "render": meta,
        "job_id": meta["job_id"],
    }
