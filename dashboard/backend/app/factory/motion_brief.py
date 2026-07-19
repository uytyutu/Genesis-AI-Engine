"""Vector / Factory motion brief — CSS vs 3D premium gate.

motion_level:
  none         — Classic Path A (default)
  css          — deterministic CSS-motion (free production; Lighthouse-friendly)
  3d_premium   — waitlist / paid contour (not enabled in Path A checkout)
"""

from __future__ import annotations

from typing import Any, Literal

MotionLevel = Literal["none", "css", "3d_premium"]

ALLOWED_MOTION_LEVELS: frozenset[str] = frozenset({"none", "css", "3d_premium"})

_MOTION_CLARIFY = {
    "ru": (
        "Вам достаточно стильного лендинга с плавной анимацией (рекомендуем) "
        "или вам критически важны 3D-модели?"
    ),
    "de": (
        "Reicht Ihnen ein stilvolles Landing mit flüssiger Animation (empfohlen), "
        "oder sind 3D-Modelle zwingend nötig?"
    ),
    "en": (
        "Is a polished landing with smooth CSS motion enough (recommended), "
        "or do you critically need real 3D models?"
    ),
    "uk": (
        "Вам достатньо стильного лендингу з плавною анімацією (рекомендуємо), "
        "чи критично потрібні 3D-моделі?"
    ),
}

_WAITLIST_MSG = {
    "ru": (
        "Для настоящего 3D нужен премиум-контур (платные кредиты и контроль скорости). "
        "Сейчас доступен CSS-motion — лёгкий и быстрый. Могу поставить 3D в waitlist "
        "или сразу собрать живой лендинг на CSS."
    ),
    "de": (
        "Echtes 3D braucht den Premium-Kontur (Credits + Performance-Check). "
        "Aktuell verfügbar: CSS-Motion — leicht und schnell. "
        "Ich kann 3D auf die Waitlist setzen oder sofort ein lebendiges CSS-Landing bauen."
    ),
    "en": (
        "Real 3D requires the premium contour (paid credits + performance control). "
        "Available now: CSS motion — light and fast. "
        "I can waitlist 3D or build a live CSS landing right away."
    ),
    "uk": (
        "Справжній 3D потребує преміум-контуру (платні кредити і контроль швидкості). "
        "Зараз доступний CSS-motion — легкий і швидкий. "
        "Можу поставити 3D у waitlist або одразу зібрати живий лендинг на CSS."
    ),
}


def normalize_motion_level(value: str | None) -> MotionLevel:
    raw = (value or "none").strip().lower().replace("-", "_")
    aliases = {
        "css_motion": "css",
        "animated": "css",
        "animation": "css",
        "3d": "3d_premium",
        "three": "3d_premium",
        "threejs": "3d_premium",
        "webgl": "3d_premium",
        "premium_3d": "3d_premium",
    }
    raw = aliases.get(raw, raw)
    if raw not in ALLOWED_MOTION_LEVELS:
        return "none"
    return raw  # type: ignore[return-value]


def detect_motion_intent(text: str) -> MotionLevel | None:
    """Infer motion intent from user wording. None = not mentioned yet."""
    t = (text or "").casefold()
    if not t:
        return None
    three_d = (
        "3d",
        "3д",
        "three.js",
        "threejs",
        "webgl",
        "критически важн",
        "критично важ",
        "real 3d",
        "echte 3d",
        "настоящий 3d",
        "настоящий 3д",
    )
    if any(x in t for x in three_d):
        return "3d_premium"
    css_hits = (
        "анимац",
        "animat",
        "motion",
        "живой сайт",
        "живую анимац",
        "плавн",
        "css-motion",
        "css motion",
        "scroll reveal",
        "reveal",
        "динамичн",
        "lebendig",
        "flüssig",
    )
    if any(x in t for x in css_hits):
        return "css"
    return None


def empty_vector_brief(
    *,
    market: str = "DE",
    niche: str = "",
    cta: str = "",
    project_type: str = "landing",
) -> dict[str, Any]:
    return {
        "project_type": project_type,
        "motion_level": "none",
        "motion_clarified": False,
        "business_niche": niche,
        "market": (market or "DE").upper(),
        "cta": cta,
        "legal_reqs": "",
        "engine_route": "classic",
        "status": "ok",
    }


def merge_motion_into_brief(
    brief: dict[str, Any] | None,
    *,
    motion_level: str | None = None,
    text: str | None = None,
    clarify: bool = False,
) -> dict[str, Any]:
    """Update brief with motion_level and routing status."""
    out = dict(brief or empty_vector_brief())
    detected = detect_motion_intent(text or "") if text else None
    level = normalize_motion_level(motion_level if motion_level is not None else detected or out.get("motion_level"))
    out["motion_level"] = level

    if level == "3d_premium":
        out["status"] = "WAITLIST_REQUIRED"
        out["engine_route"] = "reject_3d"
        out["motion_clarified"] = True
        return out

    if level == "css":
        out["status"] = "ok"
        out["engine_route"] = "classic_css_motion"
        out["motion_clarified"] = True
        return out

    # none — maybe need Vector clarification if user asked for "animated" vaguely
    if clarify and detected is None and text and any(
        x in (text or "").casefold() for x in ("сайт", "landing", "website", "лендинг")
    ):
        out["status"] = "NEEDS_MOTION_CLARIFY"
        out["engine_route"] = "classic"
        out["motion_clarified"] = False
        return out

    out["status"] = "ok"
    out["engine_route"] = "classic"
    if motion_level is not None or detected is not None:
        out["motion_clarified"] = True
    return out


def gate_motion_level(level: str | None) -> dict[str, Any]:
    """Factory/research gate: allow css/none, reject 3d_premium."""
    ml = normalize_motion_level(level)
    if ml == "3d_premium":
        return {
            "ok": False,
            "code": "WAITLIST_REQUIRED",
            "motion_level": ml,
            "message_key": "3d_premium_waitlist",
        }
    return {"ok": True, "code": "ok", "motion_level": ml}


def vector_motion_clarify_question(lang: str | None = "ru") -> str:
    code = (lang or "ru")[:2].lower()
    return _MOTION_CLARIFY.get(code) or _MOTION_CLARIFY["en"]


def vector_3d_waitlist_message(lang: str | None = "ru") -> str:
    code = (lang or "ru")[:2].lower()
    return _WAITLIST_MSG.get(code) or _WAITLIST_MSG["en"]


def apply_text_to_project_brief(brief: dict[str, Any] | None, text: str) -> dict[str, Any]:
    """Merge user reply into brief (yes to CSS / insist on 3D)."""
    t = (text or "").casefold().strip()
    base = dict(brief or empty_vector_brief())
    if any(x in t for x in ("3d", "3д", "webgl", "three.js", "threejs")):
        return merge_motion_into_brief(base, motion_level="3d_premium", text=text)
    # Clarification answers — only when Vector asked about motion
    if base.get("status") == "NEEDS_MOTION_CLARIFY" or not base.get("motion_clarified"):
        css_yes = (
            "css",
            "плавн",
            "достаточно",
            "рекоменд",
            "enough",
            "reicht",
            "анимац",
            "живой",
            "motion",
            "без 3d",
            "ohne 3d",
            "no 3d",
        )
        if any(x in t for x in css_yes) or t in {"да", "ok", "хорошо", "yes", "ja", "так"}:
            return merge_motion_into_brief(base, motion_level="css", text=text)
    detected = detect_motion_intent(text)
    if detected:
        return merge_motion_into_brief(base, motion_level=detected, text=text)
    return merge_motion_into_brief(base, text=text)
