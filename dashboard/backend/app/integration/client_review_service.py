"""Client reviews after Delivered — token-gated submit, CEO moderate, public published only."""

from __future__ import annotations

import json
import re
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_URL_RE = re.compile(r"(https?://|www\.|\S+\.(com|de|ru|net|org|io)\b)", re.I)
_MIN_LEN = 20
_MAX_LEN = 1000

# Compact RU/DE/EN insult / spam markers — flag only, never auto-delete.
_PROFANITY = frozenset(
    {
        "fuck",
        "shit",
        "idiot",
        "bastard",
        "arschloch",
        "scheisse",
        "scheiße",
        "hurensohn",
        "blyat",
        "блять",
        "сука",
        "пидор",
        "мудак",
        "ебан",
        "хуй",
    }
)

_EMPTY_PUBLIC_MESSAGE_RU = "Отзывы появятся после выполнения первых заказов."
_EMPTY_PUBLIC_MESSAGE_DE = "Bewertungen erscheinen nach den ersten abgeschlossenen Aufträgen."
_EMPTY_PUBLIC_MESSAGE_EN = "Reviews will appear after the first completed orders."
_EMPTY_PUBLIC_MESSAGE_UK = "Відгуки з’являться після виконання перших замовлень."


def new_review_token() -> str:
    return secrets.token_urlsafe(24)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def screen_review_text(text: str) -> list[str]:
    """Heuristic screen — returns flags; never auto-rejects publish eligibility alone."""
    flags: list[str] = []
    body = _normalize_text(text)
    if len(body) < _MIN_LEN:
        flags.append("too_short")
    if len(body) > _MAX_LEN:
        flags.append("too_long")
    if _URL_RE.search(body):
        flags.append("contains_url")
    lower = body.lower()
    if any(w in lower for w in _PROFANITY):
        flags.append("profanity")
    letters = sum(1 for c in body if c.isalpha())
    if body and letters < max(8, len(body) // 4):
        flags.append("low_signal")
    return flags


class ClientReviewService:
    def __init__(self, memory_dir: Path, sales: Any) -> None:
        self._memory = memory_dir
        self._sales = sales
        self._memory.mkdir(parents=True, exist_ok=True)

    def _path(self) -> Path:
        return self._memory / "client_reviews.jsonl"

    def _load_all(self) -> list[dict[str, Any]]:
        path = self._path()
        if not path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
        except OSError:
            return []
        return rows

    def _append(self, row: dict[str, Any]) -> None:
        path = self._path()
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _rewrite(self, rows: list[dict[str, Any]]) -> None:
        path = self._path()
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )

    def find_by_order(self, order_id: str) -> dict[str, Any] | None:
        oid = (order_id or "").strip()
        for row in reversed(self._load_all()):
            if str(row.get("order_id") or "") == oid:
                return row
        return None

    def order_review_flags(self, order: dict[str, Any] | None) -> dict[str, Any]:
        if not order:
            return {
                "review_eligible": False,
                "review_submitted": False,
                "review_token": None,
                "review_url": None,
            }
        oid = str(order.get("order_id") or "")
        existing = self.find_by_order(oid)
        eligible = bool(order.get("review_eligible")) and str(order.get("status") or "") == "delivered"
        token = str(order.get("review_token") or "") if eligible and not existing else ""
        return {
            "review_eligible": eligible and existing is None,
            "review_submitted": existing is not None,
            "review_status": (existing or {}).get("status"),
            "review_url": f"/order/review/{oid}?token={token}" if token else None,
        }

    def submit(
        self,
        *,
        order_id: str,
        token: str,
        stars: int,
        text: str,
        show_company_name: bool = True,
        show_logo: bool = False,
        company_display_name: str | None = None,
    ) -> dict[str, Any]:
        order = self._sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if str(order.get("status") or "") != "delivered" or not order.get("review_eligible"):
            raise ValueError("not_eligible")
        expected = str(order.get("review_token") or "")
        if not expected or not secrets.compare_digest(expected, (token or "").strip()):
            raise ValueError("bad_token")
        if self.find_by_order(order_id):
            raise ValueError("already_submitted")
        try:
            star_n = int(stars)
        except (TypeError, ValueError) as exc:
            raise ValueError("bad_stars") from exc
        if star_n < 1 or star_n > 5:
            raise ValueError("bad_stars")
        body = _normalize_text(text)
        if len(body) > _MAX_LEN:
            raise ValueError("too_long")
        if len(body) < _MIN_LEN:
            raise ValueError("too_short")
        flags = screen_review_text(body)
        company = _normalize_text(company_display_name or "") or str(order.get("business_name") or "").strip()
        row = {
            "review_id": f"REV-{uuid.uuid4().hex[:10].upper()}",
            "order_id": order_id,
            "stars": star_n,
            "text": body,
            "show_company_name": bool(show_company_name),
            "show_logo": bool(show_logo),
            "company_display_name": company,
            "logo_url": order.get("logo_url") if show_logo else None,
            # Always true: submit is only allowed after Delivered + review_token.
            "verified_purchase": True,
            "status": "pending",
            "flags": flags,
            "created_at": _now(),
            "published_at": None,
            "rejected_at": None,
            "moderation_note": "",
        }
        self._append(row)
        order["review_submitted"] = True
        order["review_submitted_at"] = row["created_at"]
        order["updated_at"] = row["created_at"]
        self._sales._save_order(order)
        return {
            "ok": True,
            "review_id": row["review_id"],
            "status": "pending",
            "flags": flags,
            "message_ru": "Спасибо. Отзыв отправлен на проверку перед публикацией.",
            "message_de": "Danke. Die Bewertung wird vor der Veröffentlichung geprüft.",
        }

    def list_pending(self) -> list[dict[str, Any]]:
        return [r for r in self._load_all() if r.get("status") == "pending"]

    def list_published(self) -> list[dict[str, Any]]:
        return [r for r in self._load_all() if r.get("status") == "published"]

    def moderate(self, review_id: str, *, action: str, note: str = "") -> dict[str, Any]:
        rid = (review_id or "").strip()
        act = (action or "").strip().lower()
        if act not in ("publish", "reject"):
            raise ValueError("bad_action")
        rows = self._load_all()
        found = None
        for row in rows:
            if str(row.get("review_id") or "") == rid:
                found = row
                break
        if not found:
            raise ValueError("not_found")
        if found.get("status") not in ("pending", "published", "rejected"):
            raise ValueError("bad_status")
        now = _now()
        if act == "publish":
            found["status"] = "published"
            found["published_at"] = now
            found["rejected_at"] = None
        else:
            found["status"] = "rejected"
            found["rejected_at"] = now
        found["moderation_note"] = (note or "").strip()[:500]
        found["moderated_at"] = now
        self._rewrite(rows)
        return found

    def public_feed(self, *, lang: str = "de") -> dict[str, Any]:
        published = self.list_published()
        cards = []
        for r in published:
            company = None
            if r.get("show_company_name"):
                company = r.get("company_display_name")
            cards.append(
                {
                    "review_id": r.get("review_id"),
                    "stars": int(r.get("stars") or 0),
                    "text": r.get("text"),
                    "company_display_name": company,
                    "show_logo": bool(r.get("show_logo") and r.get("logo_url")),
                    "logo_url": r.get("logo_url") if r.get("show_logo") else None,
                    "verified_purchase": bool(r.get("verified_purchase", True)),
                    "published_at": r.get("published_at"),
                }
            )
        if not cards:
            msg = {
                "ru": _EMPTY_PUBLIC_MESSAGE_RU,
                "de": _EMPTY_PUBLIC_MESSAGE_DE,
                "en": _EMPTY_PUBLIC_MESSAGE_EN,
                "uk": _EMPTY_PUBLIC_MESSAGE_UK,
            }.get((lang or "de")[:2], _EMPTY_PUBLIC_MESSAGE_DE)
            return {
                "has_reviews": False,
                "count": 0,
                "average_stars": None,
                "recommend_pct": None,
                "empty_message": msg,
                "reviews": [],
            }
        avg = round(sum(int(c["stars"]) for c in cards) / len(cards), 1)
        recommend = round(100 * sum(1 for c in cards if int(c["stars"]) >= 4) / len(cards))
        return {
            "has_reviews": True,
            "count": len(cards),
            "average_stars": avg,
            "recommend_pct": recommend,
            "empty_message": None,
            "reviews": cards,
        }
