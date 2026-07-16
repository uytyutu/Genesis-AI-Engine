"""Inbound lead intake — unstructured chat → qualified opportunity (Model 3)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.integration.opportunity_service import OpportunityService
from app.integration.owner_notification_service import OwnerNotificationService

_NICHE_PROFILES: dict[str, dict[str, Any]] = {
    "autoservice": {
        "label": "Автосервис",
        "lead_value_eur": 20.0,
        "keywords": ("авто", "машин", "тормоз", "двигател", "то ", "шин", "диагност"),
    },
    "laptop_repair": {
        "label": "Ремонт ноутбуков",
        "lead_value_eur": 18.0,
        "keywords": ("ноутбук", "laptop", "компьютер", "экран", "клавиат", "ssd", "windows"),
    },
    "plumber": {
        "label": "Сантехник",
        "lead_value_eur": 22.0,
        "keywords": ("сантех", "труб", "кран", "протеч", "канализ", "водопров"),
    },
    "generic": {
        "label": "Услуга",
        "lead_value_eur": 15.0,
        "keywords": (),
    },
}

_GAP_LABELS = {
    "problem": "в чём проблема",
    "location": "где вы находитесь",
    "contact": "телефон или email",
    "urgency": "насколько срочно",
}

_EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}(?:[\s-]?\d{2,4})?"
)


def _clean(text: str, max_len: int = 160) -> str:
    t = (text or "").replace("\n", " ").strip()
    if len(t) <= max_len:
        return t
    return f"{t[: max_len - 1]}…"


def _extract_problem(text: str) -> str | None:
    t = text.strip()
    patterns = (
        r"(?:проблема|сломал\w*|не\s+работ\w*|нужен?\s+[^.!\n]{4,80})",
        r"(?:ремонт|почин\w*|замен\w*|диагност\w*)[^.!\n]{0,60}",
        r"(?:need|broken|repair|fix)\s+[^.!\n]{4,80}",
    )
    for pat in patterns:
        m = re.search(pat, t, re.I)
        if m:
            return _clean(m.group(0), 120)
    if len(t) > 24 and re.search(r"(срочно|помог|нужно|хочу)", t, re.I):
        return _clean(t, 120)
    return None


def _extract_urgency(text: str) -> str | None:
    if re.search(r"(срочно|сегодня|завтра|как\s+можно\s+скорее|asap|urgent)", text, re.I):
        m = re.search(
            r"(срочно[^.!\n]{0,40}|сегодня[^.!\n]{0,40}|завтра[^.!\n]{0,40})",
            text,
            re.I,
        )
        return _clean(m.group(0), 60) if m else "Срочно"
    return None


def _extract_location(text: str) -> str | None:
    m = (
        re.search(
            r"(?:я\s+в|нахожусь\s+в|город[:\s]+|в\s+г\.?\s*)([A-Za-zА-Яа-яЁё\s-]{2,40})",
            text,
            re.I,
        )
        or re.search(r"\b(?:в|in)\s+([A-ZА-ЯЁ][a-zа-яё-]{2,24})\b", text, re.I)
    )
    if m:
        loc = m.group(1).strip()
        if loc.lower() not in {"нужен", "хочу", "срочно", "привет", "здравствуйте"}:
            return _clean(loc, 60)
    return None


def _extract_name(text: str) -> str | None:
    m = re.search(r"(?:меня\s+зовут|я\s+[-—]\s*|my\s+name\s+is)\s*([A-Za-zА-Яа-яЁё\s-]{2,40})", text, re.I)
    return _clean(m.group(1), 40) if m else None


def extract_lead_facts(message: str) -> dict[str, str | None]:
    text = (message or "").strip()
    if not text:
        return {}
    email = _EMAIL_RE.search(text)
    phone = _PHONE_RE.search(text)
    return {
        "customer_name": _extract_name(text),
        "problem": _extract_problem(text),
        "urgency": _extract_urgency(text),
        "location": _extract_location(text),
        "phone": phone.group(0).strip() if phone else None,
        "email": email.group(0).strip() if email else None,
    }


def merge_lead_known(prev: dict[str, str], facts: dict[str, str | None]) -> dict[str, str]:
    out = dict(prev)
    for key, value in facts.items():
        v = (value or "").strip()
        if not v:
            continue
        if not out.get(key):
            out[key] = v
        elif key == "problem" and v not in out[key]:
            out[key] = _clean(f"{out[key]}. {v}", 200)
    return out


def lead_gaps(known: dict[str, str]) -> list[str]:
    gaps: list[str] = []
    if not known.get("problem", "").strip():
        gaps.append("problem")
    if not known.get("location", "").strip():
        gaps.append("location")
    if not (known.get("phone", "").strip() or known.get("email", "").strip()):
        gaps.append("contact")
    if known.get("problem") and not known.get("urgency"):
        gaps.append("urgency")
    return gaps


def lead_follow_up(gap: str, niche: str) -> str:
    profile = _NICHE_PROFILES.get(niche) or _NICHE_PROFILES["generic"]
    label = profile["label"]
    prompts = {
        "problem": f"Расскажите, что случилось — я подберу {label.lower()} под вашу ситуацию.",
        "location": "В каком городе или районе вам нужна помощь?",
        "contact": "Оставьте телефон или email — передам мастеру, когда заявка будет готова.",
        "urgency": "Насколько срочно — сегодня, завтра или можно подождать?",
    }
    return prompts.get(gap, "Расскажите чуть подробнее, чтобы я оформил заявку.")


def score_lead(known: dict[str, str]) -> int:
    score = 0
    if known.get("problem"):
        score += 30
    if known.get("location"):
        score += 20
    if known.get("phone"):
        score += 25
    elif known.get("email"):
        score += 20
    if known.get("urgency"):
        score += 15
    if known.get("customer_name"):
        score += 10
    return min(100, score)


def is_hot_lead(known: dict[str, str]) -> bool:
    has_contact = bool(known.get("phone", "").strip() or known.get("email", "").strip())
    return bool(known.get("problem", "").strip() and known.get("location", "").strip() and has_contact)


class LeadIntakeService:
    def __init__(
        self,
        opportunity: OpportunityService,
        notifications: OwnerNotificationService | None = None,
    ) -> None:
        self._opportunity = opportunity
        self._notifications = notifications

    def niche_profile(self, niche: str) -> dict[str, Any]:
        return _NICHE_PROFILES.get(niche) or _NICHE_PROFILES["generic"]

    def build_context(self, *, niche: str, known: dict[str, str]) -> dict[str, Any]:
        gaps = lead_gaps(known)
        return {
            "mode": "lead_capture",
            "niche": niche,
            "niche_label": self.niche_profile(niche)["label"],
            "known": known,
            "missing": gaps,
            "follow_up": lead_follow_up(gaps[0], niche) if gaps else None,
            "score": score_lead(known),
            "hot": is_hot_lead(known),
        }

    def intake(
        self,
        *,
        niche: str,
        known: dict[str, str],
        visitor_id: str = "",
        transcript: str = "",
    ) -> dict[str, Any]:
        niche_key = niche if niche in _NICHE_PROFILES else "generic"
        profile = self.niche_profile(niche_key)
        gaps = lead_gaps(known)
        score = score_lead(known)
        hot = is_hot_lead(known)

        if not hot:
            return {
                "hot": False,
                "score": score,
                "gaps": gaps,
                "follow_up": lead_follow_up(gaps[0], niche_key) if gaps else None,
                "lead_id": None,
                "message": "Продолжайте диалог — заявка ещё не готова.",
            }

        contact = known.get("phone") or known.get("email") or ""
        existing = self._find_recent_duplicate(contact, visitor_id)
        if existing:
            notes = self._format_notes(known, transcript, visitor_id)
            updated = self._opportunity.update(
                existing["id"],
                {
                    "notes": notes,
                    "score": max(int(existing.get("score") or 0), score),
                    "status": "qualified",
                    "fit_reason": self._fit_reason(known, niche_key),
                },
            )
            return {
                "hot": True,
                "score": int(updated.get("score") or score),
                "gaps": [],
                "follow_up": None,
                "lead_id": updated["id"],
                "message": "Заявка обновлена — мастер увидит свежие детали.",
                "duplicate": True,
            }

        company = (
            known.get("customer_name")
            or _clean(known.get("problem", ""), 80)
            or f"Лид: {profile['label']}"
        )
        notes = self._format_notes(known, transcript, visitor_id)
        from app.integration.lead_pipeline_service import ingest_lead

        ingested = ingest_lead(
            self._opportunity,
            {
                "source_id": "inbound_chat",
                "opportunity_type": "lead",
                "company_name": company,
                "contact": contact,
                "fit_reason": self._fit_reason(known, niche_key),
                "score": score,
                "notes": notes,
                "potential_value_eur": float(profile["lead_value_eur"]),
                "meta": {
                    "niche": niche_key,
                    "visitor_id": visitor_id,
                    "urgency": known.get("urgency", ""),
                    "location": known.get("location", ""),
                    "problem": known.get("problem", ""),
                },
            },
        )
        if ingested.get("blocked"):
            return {
                "hot": False,
                "score": score,
                "gaps": [],
                "follow_up": None,
                "lead_id": None,
                "message": "Источник отклонён политикой качества.",
                "duplicate": False,
            }
        row = ingested["row"]
        if ingested.get("duplicate"):
            return {
                "hot": True,
                "score": score,
                "gaps": [],
                "follow_up": None,
                "lead_id": row["id"],
                "message": "Заявка уже в журнале (дубликат).",
                "duplicate": True,
            }
        qualified = self._opportunity.update(row["id"], {"status": "qualified"})
        self._notify_owner(qualified, profile)
        return {
            "hot": True,
            "score": score,
            "gaps": [],
            "follow_up": None,
            "lead_id": qualified["id"],
            "message": "Горячая заявка принята — передам партнёру.",
            "duplicate": False,
        }

    def inbox(self, *, today_only: bool = True, limit: int = 50) -> list[dict]:
        return self._opportunity.list_opportunities(
            source_id="inbound_chat",
            status="qualified",
            today_only=today_only,
            limit=limit,
        )

    def _fit_reason(self, known: dict[str, str], niche: str) -> str:
        profile = self.niche_profile(niche)
        parts = [profile["label"]]
        if known.get("problem"):
            parts.append(known["problem"])
        if known.get("location"):
            parts.append(f"Локация: {known['location']}")
        if known.get("urgency"):
            parts.append(f"Срочность: {known['urgency']}")
        return " · ".join(parts)

    def _format_notes(self, known: dict[str, str], transcript: str, visitor_id: str) -> str:
        lines = [
            f"Проблема: {known.get('problem', '—')}",
            f"Локация: {known.get('location', '—')}",
            f"Контакт: {known.get('phone') or known.get('email') or '—'}",
            f"Срочность: {known.get('urgency', '—')}",
        ]
        if visitor_id:
            lines.append(f"Visitor: {visitor_id}")
        if transcript.strip():
            lines.append(f"Диалог: {_clean(transcript, 400)}")
        return "\n".join(lines)

    def _find_recent_duplicate(self, contact: str, visitor_id: str) -> dict | None:
        if not contact and not visitor_id:
            return None
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        rows = self._opportunity.list_opportunities(source_id="inbound_chat", limit=200)
        for row in rows:
            found_at = row.get("found_at")
            if not found_at:
                continue
            try:
                ts = datetime.fromisoformat(str(found_at).replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts < cutoff:
                continue
            row_contact = str(row.get("contact") or "").strip()
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            row_visitor = str(meta.get("visitor_id") or "").strip()
            if contact and row_contact and contact == row_contact:
                return row
            if visitor_id and row_visitor and visitor_id == row_visitor:
                return row
        return None

    def _notify_owner(self, row: dict, profile: dict[str, Any]) -> None:
        if not self._notifications:
            return
        self._notifications.notify(
            title=f"Горячий лид · {profile['label']}",
            message=(
                f"{row.get('company_name', 'Лид')} — {row.get('fit_reason', '')}\n"
                f"Контакт: {row.get('contact', '—')} · €{profile['lead_value_eur']:.0f}"
            ),
        )
