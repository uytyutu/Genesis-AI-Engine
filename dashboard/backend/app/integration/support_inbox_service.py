"""Support Inbox — Resend Inbound threads, templates, identical auto-reply."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.integration.genesis_brain.public_brand import BRAND_NAME

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

ThreadStatus = str  # needs_reply | waiting | closed


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_fingerprint(subject: str, body: str) -> str:
    """Stable fingerprint for identical-question matching."""
    text = f"{subject or ''}\n{body or ''}"
    lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(">"):
            continue
        if re.match(r"^on .+ wrote:$", s, re.I):
            break
        if re.match(r"^am .+ schrieb:$", s, re.I):
            break
        if s in ("--", "—"):
            break
        if s.lower().startswith("from:"):
            break
        lines.append(line)
    cleaned = " ".join(" ".join(lines).lower().split())
    cleaned = re.sub(r"[^\w\s@.+-]", "", cleaned, flags=re.UNICODE)
    cleaned = " ".join(cleaned.split())
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:32]


class SupportInboxService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        raw = os.getenv("GENESIS_MEMORY_DIR", "").strip()
        if memory_dir is not None:
            self._memory = memory_dir
        elif raw:
            self._memory = Path(raw).expanduser()
        else:
            self._memory = _DEFAULT_MEMORY
        self._memory.mkdir(parents=True, exist_ok=True)
        self._threads_path = self._memory / "support_threads.json"
        self._templates_path = self._memory / "support_templates.json"
        self._rules_path = self._memory / "support_auto_rules.json"

    # --- persistence ---------------------------------------------------------

    def _load_list(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def _save_list(self, path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    def configuration_status(self) -> dict[str, Any]:
        has_key = bool(os.getenv("RESEND_API_KEY", "").strip())
        has_from = bool(os.getenv("GENESIS_EMAIL_FROM", "").strip())
        has_inbound_secret = bool(os.getenv("RESEND_INBOUND_WEBHOOK_SECRET", "").strip())
        return {
            "configured": has_key and has_from,
            "has_api_key": has_key,
            "has_from_address": has_from,
            "inbound_webhook_secret_set": has_inbound_secret,
            "inbound_ready": has_key and has_from and has_inbound_secret,
            "support_email": (
                os.getenv("GENESIS_SUPPORT_EMAIL", "").strip()
                or "hello@genesis-ai-engine.com"
            ),
        }

    # --- threads -------------------------------------------------------------

    def list_threads(self, *, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._load_list(self._threads_path)
        if status and status != "inbox":
            rows = [r for r in rows if str(r.get("status") or "") == status]
        rows.sort(key=lambda r: str(r.get("updated_at") or ""), reverse=True)
        return rows[: max(1, limit)]

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        tid = str(thread_id or "").strip()
        for row in self._load_list(self._threads_path):
            if str(row.get("id")) == tid:
                return row
        return None

    def set_status(self, thread_id: str, status: str) -> dict[str, Any]:
        if status not in ("needs_reply", "waiting", "closed"):
            raise ValueError("invalid_status")
        rows = self._load_list(self._threads_path)
        for row in rows:
            if str(row.get("id")) == str(thread_id):
                row["status"] = status
                row["updated_at"] = utc_now()
                self._save_list(self._threads_path, rows)
                return row
        raise ValueError("not_found")

    def ingest_inbound(
        self,
        *,
        from_email: str,
        subject: str,
        text: str,
        html_body: str = "",
        to_email: str = "",
        external_id: str = "",
        auto_reply: bool = True,
    ) -> dict[str, Any]:
        from_addr = (from_email or "").strip()
        if not from_addr or "@" not in from_addr:
            raise ValueError("invalid_from")
        subj = (subject or "").strip() or "(no subject)"
        body = (text or "").strip() or re.sub(r"<[^>]+>", " ", html_body or "")
        body = " ".join(body.split())
        fp = normalize_fingerprint(subj, body)
        now = utc_now()
        msg = {
            "id": str(uuid.uuid4()),
            "direction": "inbound",
            "from": from_addr,
            "to": (to_email or "").strip(),
            "subject": subj,
            "text": body,
            "html": html_body or "",
            "fingerprint": fp,
            "external_id": (external_id or "").strip(),
            "created_at": now,
            "auto_replied": False,
        }

        rows = self._load_list(self._threads_path)
        thread: dict[str, Any] | None = None
        # Match open thread by same sender + similar subject
        subj_key = re.sub(r"^(re|fw|fwd):\s*", "", subj, flags=re.I).strip().lower()
        for row in rows:
            if str(row.get("from") or "").lower() != from_addr.lower():
                continue
            if str(row.get("status") or "") == "closed":
                continue
            existing_subj = re.sub(
                r"^(re|fw|fwd):\s*", "", str(row.get("subject") or ""), flags=re.I
            ).strip().lower()
            if existing_subj == subj_key or not existing_subj:
                thread = row
                break

        if thread is None:
            thread = {
                "id": str(uuid.uuid4()),
                "from": from_addr,
                "to": (to_email or "").strip(),
                "subject": subj,
                "status": "needs_reply",
                "messages": [],
                "created_at": now,
                "updated_at": now,
                "last_fingerprint": fp,
            }
            rows.insert(0, thread)

        messages = list(thread.get("messages") or [])
        messages.append(msg)
        thread["messages"] = messages
        thread["updated_at"] = now
        thread["last_fingerprint"] = fp
        thread["subject"] = thread.get("subject") or subj

        auto_result: dict[str, Any] | None = None
        if auto_reply:
            auto_result = self._try_auto_reply(thread, inbound_msg=msg)
            if auto_result and auto_result.get("ok"):
                thread["status"] = "waiting"
                msg["auto_replied"] = True

        if thread["status"] not in ("waiting", "closed"):
            thread["status"] = "needs_reply"

        # upsert thread in list
        out_rows: list[dict[str, Any]] = []
        replaced = False
        for row in rows:
            if str(row.get("id")) == str(thread["id"]):
                out_rows.append(thread)
                replaced = True
            else:
                out_rows.append(row)
        if not replaced:
            out_rows.insert(0, thread)
        self._save_list(self._threads_path, out_rows)
        return {
            "ok": True,
            "thread": thread,
            "message": msg,
            "auto_reply": auto_result,
        }

    def reply(
        self,
        thread_id: str,
        *,
        text: str,
        save_as_template: bool = False,
        template_name: str = "",
        create_auto_rule: bool = False,
    ) -> dict[str, Any]:
        body = (text or "").strip()
        if len(body) < 2:
            raise ValueError("empty_reply")
        rows = self._load_list(self._threads_path)
        thread: dict[str, Any] | None = None
        for row in rows:
            if str(row.get("id")) == str(thread_id):
                thread = row
                break
        if not thread:
            raise ValueError("not_found")

        to = str(thread.get("from") or "").strip()
        subj = str(thread.get("subject") or "Virtus Core")
        if not subj.lower().startswith("re:"):
            subj = f"Re: {subj}"

        send = self._send_email(to=to, subject=subj, text=body)
        now = utc_now()
        out_msg = {
            "id": str(uuid.uuid4()),
            "direction": "outbound",
            "from": "ceo",
            "to": to,
            "subject": subj,
            "text": body,
            "html": "",
            "fingerprint": normalize_fingerprint(subj, body),
            "created_at": now,
            "send": send,
        }
        messages = list(thread.get("messages") or [])
        messages.append(out_msg)
        thread["messages"] = messages
        thread["updated_at"] = now
        thread["status"] = "waiting" if send.get("ok") else "needs_reply"
        self._save_list(self._threads_path, rows)

        template_id = None
        rule_id = None
        if save_as_template:
            # fingerprint from last inbound
            inbound_fp = ""
            for m in reversed(messages):
                if m.get("direction") == "inbound":
                    inbound_fp = str(m.get("fingerprint") or "")
                    break
            tpl = self.create_template(
                name=template_name or f"Reply · {thread.get('subject', '')[:40]}",
                subject=subj,
                body=body,
                source_fingerprint=inbound_fp,
            )
            template_id = tpl.get("id")
            if create_auto_rule and inbound_fp and template_id:
                rule = self.create_auto_rule(
                    fingerprint=inbound_fp,
                    template_id=str(template_id),
                    enabled=True,
                    label=str(tpl.get("name") or ""),
                )
                rule_id = rule.get("id")

        return {
            "ok": bool(send.get("ok")),
            "thread": thread,
            "message": out_msg,
            "send": send,
            "template_id": template_id,
            "rule_id": rule_id,
        }

    # --- templates / rules ---------------------------------------------------

    def list_templates(self) -> list[dict[str, Any]]:
        return self._load_list(self._templates_path)

    def create_template(
        self,
        *,
        name: str,
        subject: str,
        body: str,
        source_fingerprint: str = "",
    ) -> dict[str, Any]:
        rows = self._load_list(self._templates_path)
        row = {
            "id": str(uuid.uuid4()),
            "name": (name or "Template").strip()[:120],
            "subject": (subject or "").strip()[:200],
            "body": (body or "").strip(),
            "source_fingerprint": (source_fingerprint or "").strip(),
            "created_at": utc_now(),
        }
        rows.insert(0, row)
        self._save_list(self._templates_path, rows)
        return row

    def list_auto_rules(self) -> list[dict[str, Any]]:
        return self._load_list(self._rules_path)

    def create_auto_rule(
        self,
        *,
        fingerprint: str,
        template_id: str,
        enabled: bool = True,
        label: str = "",
    ) -> dict[str, Any]:
        fp = (fingerprint or "").strip()
        tid = (template_id or "").strip()
        if not fp or not tid:
            raise ValueError("invalid_rule")
        rows = self._load_list(self._rules_path)
        # upsert by fingerprint
        for row in rows:
            if str(row.get("fingerprint")) == fp:
                row["template_id"] = tid
                row["enabled"] = bool(enabled)
                row["label"] = (label or row.get("label") or "").strip()[:120]
                row["updated_at"] = utc_now()
                self._save_list(self._rules_path, rows)
                return row
        row = {
            "id": str(uuid.uuid4()),
            "fingerprint": fp,
            "template_id": tid,
            "enabled": bool(enabled),
            "label": (label or "").strip()[:120],
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "hit_count": 0,
        }
        rows.insert(0, row)
        self._save_list(self._rules_path, rows)
        return row

    def delete_auto_rule(self, rule_id: str) -> bool:
        rows = self._load_list(self._rules_path)
        nxt = [r for r in rows if str(r.get("id")) != str(rule_id)]
        if len(nxt) == len(rows):
            return False
        self._save_list(self._rules_path, nxt)
        return True

    def set_auto_rule_enabled(self, rule_id: str, enabled: bool) -> dict[str, Any]:
        rows = self._load_list(self._rules_path)
        for row in rows:
            if str(row.get("id")) == str(rule_id):
                row["enabled"] = bool(enabled)
                row["updated_at"] = utc_now()
                self._save_list(self._rules_path, rows)
                return row
        raise ValueError("not_found")

    def find_rule_for_fingerprint(self, fingerprint: str) -> dict[str, Any] | None:
        fp = (fingerprint or "").strip()
        for row in self._load_list(self._rules_path):
            if not row.get("enabled", True):
                continue
            if str(row.get("fingerprint")) == fp:
                return row
        return None

    def _try_auto_reply(
        self, thread: dict[str, Any], *, inbound_msg: dict[str, Any]
    ) -> dict[str, Any] | None:
        fp = str(inbound_msg.get("fingerprint") or "")
        rule = self.find_rule_for_fingerprint(fp)
        if not rule:
            return None
        tpl_id = str(rule.get("template_id") or "")
        template = next(
            (t for t in self.list_templates() if str(t.get("id")) == tpl_id), None
        )
        if not template:
            return {"ok": False, "reason": "template_missing"}

        to = str(thread.get("from") or "").strip()
        subj = str(template.get("subject") or thread.get("subject") or "Virtus Core")
        if not subj.lower().startswith("re:"):
            subj = f"Re: {subj}"
        body = str(template.get("body") or "")
        send = self._send_email(to=to, subject=subj, text=body)
        now = utc_now()
        out_msg = {
            "id": str(uuid.uuid4()),
            "direction": "outbound",
            "from": "auto",
            "to": to,
            "subject": subj,
            "text": body,
            "html": "",
            "fingerprint": normalize_fingerprint(subj, body),
            "created_at": now,
            "auto": True,
            "rule_id": rule.get("id"),
            "template_id": tpl_id,
            "send": send,
        }
        messages = list(thread.get("messages") or [])
        messages.append(out_msg)
        thread["messages"] = messages
        thread["updated_at"] = now

        # bump hit_count
        rules = self._load_list(self._rules_path)
        for r in rules:
            if str(r.get("id")) == str(rule.get("id")):
                r["hit_count"] = int(r.get("hit_count") or 0) + 1
                r["updated_at"] = now
                break
        self._save_list(self._rules_path, rules)

        return {"ok": bool(send.get("ok")), "send": send, "message": out_msg, "rule": rule}

    def fetch_received_email(self, email_id: str) -> dict[str, Any]:
        """GET /emails/receiving/{id} — Resend inbound body (webhook has metadata only)."""
        email_id = (email_id or "").strip()
        if not email_id:
            return {"ok": False, "reason": "missing_email_id"}
        api_key = os.getenv("RESEND_API_KEY", "").strip()
        if not api_key:
            return {"ok": False, "reason": "not_configured"}
        try:
            res = httpx.get(
                f"https://api.resend.com/emails/receiving/{email_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            return {"ok": False, "reason": "network_error", "detail": str(exc)[:160]}
        if res.status_code >= 400:
            return {
                "ok": False,
                "reason": f"resend_error:{res.status_code}",
                "detail": res.text[:200],
            }
        data = res.json() if res.content else {}
        return {"ok": True, "email": data if isinstance(data, dict) else {}}

    def _send_email(self, *, to: str, subject: str, text: str) -> dict[str, Any]:
        if not to:
            return {"ok": False, "skipped": True, "reason": "no_email"}
        api_key = os.getenv("RESEND_API_KEY", "").strip()
        from_addr = os.getenv("GENESIS_EMAIL_FROM", "").strip()
        if not api_key or not from_addr:
            return {"ok": False, "skipped": True, "reason": "not_configured"}

        intro = text.split("\n\n")[0][:280] if text else subject
        safe_text = html.escape(text).replace("\n", "<br>")
        html_body = (
            f"<div style='font-family:system-ui,sans-serif;color:#111'>"
            f"<p>{html.escape(intro)}</p>"
            f"<div style='margin-top:16px;line-height:1.5'>{safe_text}</div>"
            f"<p style='margin-top:24px;color:#666;font-size:12px'>{html.escape(BRAND_NAME)}</p>"
            f"</div>"
        )
        payload = {
            "from": from_addr,
            "to": [to],
            "subject": subject,
            "text": text,
            "html": html_body,
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}"},
                )
        except Exception as exc:
            return {"ok": False, "reason": "network_error", "detail": str(exc)[:160]}
        if res.status_code >= 400:
            return {
                "ok": False,
                "reason": f"resend_error:{res.status_code}",
                "detail": res.text[:200],
            }
        return {
            "ok": True,
            "provider": "resend",
            "id": (res.json() or {}).get("id"),
        }

    @staticmethod
    def parse_resend_inbound_payload(payload: dict[str, Any]) -> dict[str, str]:
        """Normalize Resend email.received / test payloads into flat fields."""
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if not isinstance(data, dict):
            data = {}

        from_raw = data.get("from") or data.get("sender") or payload.get("from") or ""
        if isinstance(from_raw, dict):
            from_email = str(from_raw.get("address") or from_raw.get("email") or "")
        else:
            from_email = str(from_raw)
        # "Name <a@b.com>" → a@b.com
        m = re.search(r"<([^>]+)>", from_email)
        if m:
            from_email = m.group(1)
        from_email = from_email.strip()

        to_raw = data.get("to") or payload.get("to") or ""
        if isinstance(to_raw, list) and to_raw:
            first = to_raw[0]
            to_email = str(first.get("address") if isinstance(first, dict) else first)
        elif isinstance(to_raw, dict):
            to_email = str(to_raw.get("address") or "")
        else:
            to_email = str(to_raw)
        m2 = re.search(r"<([^>]+)>", to_email)
        if m2:
            to_email = m2.group(1)

        subject = str(data.get("subject") or payload.get("subject") or "")
        text = str(
            data.get("text")
            or data.get("text_body")
            or payload.get("text")
            or ""
        )
        html_body = str(
            data.get("html")
            or data.get("html_body")
            or payload.get("html")
            or ""
        )
        external_id = str(
            data.get("email_id")
            or data.get("id")
            or payload.get("email_id")
            or payload.get("id")
            or ""
        )
        return {
            "from_email": from_email,
            "to_email": to_email.strip(),
            "subject": subject,
            "text": text,
            "html": html_body,
            "external_id": external_id,
        }
