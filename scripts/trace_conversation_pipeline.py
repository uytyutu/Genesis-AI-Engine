#!/usr/bin/env python3
"""Multi-message trace — drafts must survive finalize+critique without template pools."""

from __future__ import annotations

import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.integration.genesis_brain.layers import GenesisPersonalityLayer, GenesisSelfCritiqueLayer
from app.integration.genesis_brain.layers.conversation_style import ConversationStyleEngine
from app.integration.genesis_brain.brain import GenesisBrain
from app.integration.genesis_brain.response_variation import _POOLS

TEST_MESSAGES = (
    "Привет",
    "Как дела?",
    "Спасибо",
    "Мне грустно",
    "Расскажи о себе",
    "Помоги придумать бизнес",
    "Я ничего не понимаю",
    "Сколько будет 2+2?",
)

_BANNED_MARKERS = (
    "на связи. давайте поговорим",
    "универсальный искусственный интеллект",
    "расскажите о задаче",
    "я — genesis",
)


def _norm(text: str) -> str:
    return " ".join((text or "").split())


def _pool_lines() -> set[str]:
    out: set[str] = set()
    for pool in _POOLS.values():
        for line in pool:
            out.add(_norm(line.lower()))
    return out


def _is_exact_pool(text: str, pools: set[str]) -> bool:
    return _norm(text.lower()) in pools


def _has_banned(text: str) -> str | None:
    low = text.lower()
    for m in _BANNED_MARKERS:
        if m in low:
            return m
    return None


def run_local() -> list[dict]:
    brain = GenesisBrain()
    personality = GenesisPersonalityLayer(mode="public")
    critique = GenesisSelfCritiqueLayer()
    style = ConversationStyleEngine()
    pools = _pool_lines()
    rows: list[dict] = []

    for msg in TEST_MESSAGES:
        messages = [{"role": "user", "content": msg}]
        result = brain.chat(system="You are Vector.", messages=messages, visitor_id=f"trace-{hash(msg)}")
        intent = brain._reasoning.analyze(messages, {}).intent
        after_finalize = personality.finalize(
            result.answer,
            messages=messages,
            visitor_id="trace",
            cloud_llm_used=False,
        )
        after_critique = critique.polish(
            after_finalize,
            intent=intent,
            messages=messages,
            visitor_id="trace",
            provider_id=result.provider_id,
            cloud_llm_used=False,
        )
        banned = _has_banned(result.answer)
        pool_hit = _is_exact_pool(result.answer, pools)
        small_talk_swap = False
        if style.is_small_talk_message(msg):
            pick = style.pick_small_talk(style.build_context({}, "trace"), msg)
            small_talk_swap = _norm(result.answer) == _norm(pick)
        rows.append(
            {
                "message": msg,
                "provider": result.provider_id,
                "answer": result.answer,
                "banned": banned,
                "exact_pool": pool_hit,
                "small_talk_pool_match": small_talk_swap,
                "len": len(result.answer),
                "ok": bool(result.answer.strip()) and not banned and not pool_hit and len(result.answer) >= 8,
            }
        )
    return rows


def run_remote(base_url: str) -> list[dict]:
    pools = _pool_lines()
    rows: list[dict] = []
    for msg in TEST_MESSAGES:
        payload = json.dumps({"question": msg, "history": []}).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/api/public/genesis-ai",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            answer = (body.get("answer") or body.get("response") or "").strip()
        except urllib.error.HTTPError as exc:
            answer = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:200]}"
        except Exception as exc:
            answer = f"ERROR: {exc}"
        banned = _has_banned(answer)
        pool_hit = _is_exact_pool(answer, pools)
        rows.append(
            {
                "message": msg,
                "answer": answer,
                "banned": banned,
                "exact_pool": pool_hit,
                "len": len(answer),
                "ok": bool(answer) and not answer.startswith("HTTP") and not answer.startswith("ERROR") and not banned and not pool_hit and len(answer) >= 8,
            }
        )
    return rows


def print_rows(label: str, rows: list[dict]) -> bool:
    print(f"\n=== {label} ===")
    all_ok = True
    for row in rows:
        status = "OK" if row["ok"] else "FAIL"
        if not row["ok"]:
            all_ok = False
        extra = []
        if row.get("banned"):
            extra.append(f"banned={row['banned']!r}")
        if row.get("exact_pool"):
            extra.append("exact_pool=True")
        if row.get("small_talk_pool_match"):
            extra.append("small_talk_pool_match=True")
        if row.get("provider"):
            extra.append(f"provider={row['provider']}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        preview = (row["answer"] or "")[:120].replace("\n", " ")
        print(f"[{status}] {row['message']!r}: {preview}{suffix}")
    print(f"\n{label} PASS: {all_ok} ({sum(1 for r in rows if r['ok'])}/{len(rows)})")
    return all_ok


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "local"
    if mode == "remote":
        base = sys.argv[2] if len(sys.argv) > 2 else "https://beta.genesis-ai-engine.com"
        ok = print_rows(f"REMOTE {base}", run_remote(base))
    else:
        ok = print_rows("LOCAL offline pipeline", run_local())
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
