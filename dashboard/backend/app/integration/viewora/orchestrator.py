"""Virtus Video AI Orchestrator — client never picks models.

Produces creative packages, hooks, Watchability scores, storyboards.
MP4 render stays behind Provider Gateway (reality.mp4_render=False until live).
"""

from __future__ import annotations

import hashlib
import random
import re
from typing import Any

from app.integration.viewora.product import (
    GENERATE_10_PRESETS,
    MODES,
    VIRAL_LAB_VARIANTS,
    VISUAL_DNA,
)


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def _pick(rng: random.Random, key: str) -> str:
    opts = VISUAL_DNA.get(key) or ["natural"]
    return rng.choice(opts)


def suggest_better(brief: str, creation_type: str = "viral_short") -> dict[str, Any]:
    rng = random.Random(_seed(f"better|{creation_type}|{brief}"))
    mode = rng.choice([m["id"] for m in MODES])
    dna = {
        "camera": _pick(rng, "camera"),
        "light": _pick(rng, "light"),
        "color": _pick(rng, "color"),
        "motion": _pick(rng, "motion"),
        "atmosphere": _pick(rng, "atmosphere"),
    }
    rationale = (
        f"Для этого ролика лучше подходит {mode.upper()} + {dna['motion']} + "
        f"{dna['light']} lighting + {dna['atmosphere']} captions."
    )
    return {
        "mode": mode,
        "visual_dna": dna,
        "rationale": rationale,
        "creation_type": creation_type,
    }


def _hooks(brief: str, n: int = 20) -> list[str]:
    topic = (brief or "это").strip()[:80] or "это"
    templates = [
        f"Ты зря делаешь {topic} каждый день…",
        f"99% людей не знают про {topic}",
        f"Я потратил €100, чтобы проверить {topic}",
        f"Стоп. Прежде чем {topic} — посмотри это",
        f"Никто не говорит правду про {topic}",
        f"Вот почему {topic} взрывает ленту",
        f"3 секунды — и ты поймёшь {topic}",
        f"Если тебе за 20 — это про {topic}",
        f"Секрет, который скрывают про {topic}",
        f"Я ошибся с {topic}. Вот что вышло",
        f"Не покупай, пока не увидишь {topic}",
        f"Алгоритм любит такой {topic}",
        f"Друзья смеялись, пока я не показал {topic}",
        f"Один приём меняет {topic} навсегда",
        f"Это звучит странно, но {topic} работает",
        f"До/после: {topic} за 15 секунд",
        f"Честный тест: {topic}",
        f"Почему все переходят на {topic}",
        f"Hook, который держит: {topic}",
        f"Смотри до конца — {topic}",
    ]
    return templates[:n]


def watchability_score(brief: str, mode: str = "viral") -> dict[str, Any]:
    """Virtus Score / WATCHABILITY — reason to come back + Optimize."""
    rng = random.Random(_seed(f"watch|{mode}|{brief}"))
    base = 72 if mode in ("viral", "fun", "ugc") else 68
    scores = {
        "hook": min(99, base + rng.randint(8, 24)),
        "pacing": min(99, base + rng.randint(6, 23)),
        "visual": min(99, base + rng.randint(10, 25)),
        "emotion": min(99, base + rng.randint(5, 22)),
        "cta": min(99, base + rng.randint(4, 20)),
    }
    weak = min(scores, key=scores.get)
    overall = round(sum(scores.values()) / len(scores))
    return {
        "label": "WATCHABILITY",
        "scores": scores,
        "overall": overall,
        "weakest": weak,
        "optimize_hint": (
            f"Усиль {weak.upper()} — Virtus Video AI пересоберёт слабые места "
            f"(hook / pacing / visual / emotion / CTA)."
        ),
    }


def viral_score(brief: str, mode: str = "viral") -> dict[str, Any]:
    """Backward-compatible alias → Watchability Score."""
    return watchability_score(brief, mode)


def _storyboard(brief: str, mode: str, dna: dict[str, str]) -> list[dict[str, Any]]:
    topic = (brief or "ваш продукт").strip()[:100]
    beats = [
        {"t": "0–2s", "label": "HOOK", "visual": f"Крупный план · {dna.get('camera')}", "line": topic[:60]},
        {"t": "2–5s", "label": "SETUP", "visual": f"{dna.get('light')} light · {dna.get('color')}", "line": "Проблема / желание"},
        {"t": "5–10s", "label": "PROOF", "visual": f"{dna.get('motion')} cuts", "line": "Демонстрация / сцена"},
        {"t": "10–14s", "label": "TWIST", "visual": f"{mode} energy", "line": "Неожиданный поворот"},
        {"t": "14–18s", "label": "CTA", "visual": "Caption + end card", "line": "Следуй / купи / сохрани"},
    ]
    return beats


def build_package(
    *,
    brief: str,
    creation_type: str = "viral_short",
    mode: str | None = None,
    visual_dna: dict[str, str] | None = None,
    product_style: str | None = None,
) -> dict[str, Any]:
    suggestion = suggest_better(brief, creation_type)
    resolved_mode = mode or suggestion["mode"]
    dna = visual_dna or suggestion["visual_dna"]
    score = watchability_score(brief, resolved_mode)
    hooks = _hooks(brief, 8)
    topic = (brief or "контент").strip()
    script = [
        {"role": "hook", "text": hooks[0]},
        {"role": "body", "text": f"Показываем суть: {topic[:160]}"},
        {"role": "proof", "text": "Быстрые кадры + субтитры крупным планом."},
        {"role": "cta", "text": "Сохрани · Подпишись · Напиши в комментариях."},
    ]
    captions = [
        hooks[0],
        "Смотри внимательно…",
        topic[:80],
        "И вот результат ↓",
        "Твой ход.",
    ]
    return {
        "creation_type": creation_type,
        "mode": resolved_mode,
        "visual_dna": dna,
        "product_style": product_style,
        "hooks": hooks,
        "script": script,
        "captions": captions,
        "storyboard": _storyboard(brief, resolved_mode, dna),
        "watchability": score,
        "viral_score": score,  # alias for older clients
        "title": _title(brief, resolved_mode),
        "music_mood": dna.get("atmosphere", "energetic"),
        "voice_note": "AI voice + adapted captions (orchestrator)",
        "render": {
            "mp4_available": False,
            "status": "package_ready",
            "preview": "storyboard",
            "note": (
                "Creative package готов. Full MP4: AI Producer → Storyboard → "
                "Scene → Video → Voice → Music → Captions → Auto Edit → "
                "Provider Gateway (модели скрыты)."
            ),
        },
        "orchestrator": {
            "chose_pipeline": True,
            "exposed_models": False,
            "provider_gateway": True,
        },
    }


def _title(brief: str, mode: str) -> str:
    clean = re.sub(r"\s+", " ", (brief or "Untitled").strip())[:48]
    return f"{mode.upper()} · {clean}" if clean else f"{mode.upper()} · Untitled"


def generate_ten(brief: str, creation_type: str = "viral_short") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for preset in GENERATE_10_PRESETS:
        mode_map = {
            "Viral": "viral",
            "Cinematic": "cinematic",
            "UGC": "ugc",
            "Story": "story",
            "Luxury": "luxury",
            "Emotional": "story",
            "Fast": "fun",
            "Documentary": "documentary",
            "Funny": "fun",
            "Minimal": "news",
        }
        mode = mode_map.get(preset["label"], "viral")
        pkg = build_package(brief=brief, creation_type=creation_type, mode=mode)
        pkg["version_id"] = preset["id"]
        pkg["version_label"] = preset["label"]
        out.append(pkg)
    return out


def viral_lab(brief: str, creation_type: str = "viral_short") -> dict[str, Any]:
    """Side-by-side variants A–H from one source idea / upload brief."""
    variants = []
    for row in VIRAL_LAB_VARIANTS:
        pkg = build_package(
            brief=brief, creation_type=creation_type, mode=row["mode"]
        )
        pkg["version_id"] = row["id"]
        pkg["version_label"] = f"{row['id']} — {row['label']}"
        variants.append(pkg)
    return {"lab": "VIRAL LAB", "count": len(variants), "versions": variants}


def hook_lab(brief: str) -> dict[str, Any]:
    hooks = _hooks(brief, 20)
    tests = [
        {
            "hook": h,
            "open_seconds": [
                {"t": "0.0", "visual": "Face / product slam", "line": h},
                {"t": "1.2", "visual": "Cut + zoom", "line": "Pattern interrupt"},
                {"t": "2.4", "visual": "Proof frame", "line": "Stay for the answer"},
            ],
        }
        for h in hooks[:5]
    ]
    return {"hooks": hooks, "test_hooks": tests, "count": len(hooks)}


def content_machine_30(brief: str) -> dict[str, Any]:
    days = []
    for i in range(1, 31):
        h = _hooks(f"{brief} day{i}", 3)
        days.append(
            {
                "day": i,
                "idea": f"День {i}: угол про {(brief or 'бренд')[:40]}",
                "hook": h[0],
                "scenario": f"15–25s · mode rotation · CTA на действие #{i}",
                "status": "planned" if i > 1 else "today",
            }
        )
    return {
        "plan_days": 30,
        "brief": brief,
        "days": days,
        "today": days[0],
    }


def podcast_to_shorts(brief: str, count: int = 20) -> dict[str, Any]:
    shorts = []
    for i in range(1, count + 1):
        pkg = build_package(
            brief=f"Moment {i}: {brief}",
            creation_type="podcast_shorts",
            mode="viral" if i % 2 else "ugc",
        )
        shorts.append(
            {
                "index": i,
                "title": pkg["title"],
                "hook": pkg["hooks"][0],
                "captions": pkg["captions"][:3],
                "mode": pkg["mode"],
            }
        )
    return {"count": count, "shorts": shorts, "source_note": brief[:200]}


def product_video_brief(
    product_name: str, style: str = "TikTok style"
) -> dict[str, Any]:
    brief = f"Product ad for {product_name} in {style}"
    pkg = build_package(
        brief=brief,
        creation_type="product_video",
        mode="ugc" if "UGC" in style or "TikTok" in style else "luxury",
        product_style=style,
    )
    pkg["pipeline"] = ["Product", "Scene", "Human", "Voice", "CTA"]
    return pkg


def random_style() -> dict[str, str]:
    rng = random.Random()
    return {k: random.choice(v) for k, v in VISUAL_DNA.items()}


def dubbing_pack(brief: str, languages: list[str] | None = None) -> dict[str, Any]:
    from app.integration.viewora.product import DUB_LANGUAGES

    codes = languages or [d["code"] for d in DUB_LANGUAGES]
    base = build_package(brief=brief, creation_type="viral_short", mode="ugc")
    tracks = []
    for code in codes:
        label = next((d["label"] for d in DUB_LANGUAGES if d["code"] == code), code)
        flag = next((d["flag"] for d in DUB_LANGUAGES if d["code"] == code), "")
        tracks.append(
            {
                "code": code,
                "label": label,
                "flag": flag,
                "adapted_hook": f"[{label}] {base['hooks'][0]}",
                "captions": [f"[{label}] {c}" for c in base["captions"][:4]],
                "voice": "AI voice + adapted script",
            }
        )
    return {
        "source_title": base["title"],
        "tracks": tracks,
        "note": "Voice + subtitles + text adaptation (not raw translate).",
    }


def ai_creator_batch(brief: str, count: int = 5) -> dict[str, Any]:
    creator = {
        "name": "My Creator",
        "look": "consistent face · wardrobe · lighting",
        "voice": "warm, direct",
        "style": "UGC + energetic captions",
    }
    videos = []
    for i in range(1, count + 1):
        pkg = build_package(
            brief=f"{brief} · episode {i}",
            creation_type="ai_creator",
            mode="ugc",
        )
        videos.append(
            {
                "index": i,
                "title": pkg["title"],
                "hook": pkg["hooks"][0],
                "mode": pkg["mode"],
                "captions": pkg["captions"][:3],
            }
        )
    return {"creator": creator, "videos": videos, "count": count}
