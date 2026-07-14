"""Lightweight website analysis for Business Acquisition Studio.

No external APIs — fetches HTML and checks honest heuristics only.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx


class SiteAnalysisService:
    _USER_AGENT = "Genesis-AcquisitionStudio/1.5 (+https://genesis-ai-engine.com)"

    def analyze(self, url: str) -> dict:
        normalized = self._normalize_url(url)
        if not normalized:
            return self._empty_result(url, error="invalid_url")

        try:
            with httpx.Client(
                timeout=12.0,
                follow_redirects=True,
                headers={"User-Agent": self._USER_AGENT},
            ) as client:
                started = client.get(normalized)
        except httpx.HTTPError as exc:
            return self._empty_result(normalized, error=f"fetch_failed:{type(exc).__name__}")

        html = started.text or ""
        final_url = str(started.url)
        issues: list[str] = []
        strengths: list[str] = []

        if not final_url.startswith("https://"):
            issues.append("Kein HTTPS — unsicher für Besucher")
        else:
            strengths.append("HTTPS aktiv")

        if started.status_code >= 400:
            issues.append(f"Seite antwortet mit HTTP {started.status_code}")
        elif started.status_code == 200:
            strengths.append("Seite erreichbar")

        lower = html.lower()
        tech_stack: list[str] = []
        if "wp-content" in lower or "wordpress" in lower:
            tech_stack.append("wordpress")
        if "joomla" in lower:
            tech_stack.append("joomla")
        if "drupal" in lower:
            tech_stack.append("drupal")
        if "wix.com" in lower:
            tech_stack.append("wix")
        if "squarespace" in lower:
            tech_stack.append("squarespace")

        lang_match = re.search(r'<html[^>]+lang=["\']([a-zA-Z-]{2,8})', html, re.I)
        detected_lang = lang_match.group(1).lower() if lang_match else ""
        if not detected_lang and re.search(r"[\u0400-\u04FF]", html):
            detected_lang = "ru"
        elif not detected_lang and re.search(r"[\u0900-\u097F]", html):
            detected_lang = "hi"

        if "viewport" not in lower:
            issues.append("Kein viewport — oft schlecht auf dem Handy")
        else:
            strengths.append("Viewport für Mobilgeräte")

        if len(html) < 1500:
            issues.append("Sehr wenig Inhalt — möglicherweise veraltet oder Platzhalter")

        if any(x in lower for x in ("jquery-1.", "flash", "under construction", "coming soon")):
            issues.append("Anzeichen veralteter Technik oder Baustelle")

        if not re.search(r"mailto:|type=[\"']email[\"']", lower):
            issues.append("Kein sichtbares Kontaktformular / E-Mail-Feld")

        if not re.search(r"tel:|whatsapp|wa\.me", lower):
            issues.append("Kein direkter Anruf / WhatsApp-Link")

        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
        title = title_match.group(1).strip() if title_match else ""
        if not title:
            issues.append("Kein Seitentitel — schlecht für SEO")

        if "og:" not in lower and "twitter:" not in lower:
            issues.append("Keine Social-Meta-Tags — schwache Vorschau in Messengern")

        load_ms = int(started.elapsed.total_seconds() * 1000) if started.elapsed else 0
        if load_ms > 3000:
            issues.append(f"Langsame Antwort (~{load_ms} ms)")
        elif load_ms > 0:
            strengths.append(f"Ladezeit ~{load_ms} ms")

        score = self._score(issues, strengths)
        return {
            "url": normalized,
            "final_url": final_url,
            "status_code": started.status_code,
            "title": title,
            "load_ms": load_ms,
            "has_https": final_url.startswith("https://"),
            "has_viewport": "viewport" in lower,
            "issues": issues,
            "strengths": strengths,
            "issue_count": len(issues),
            "improvement_score": score,
            "tech_stack": tech_stack,
            "detected_lang": detected_lang,
            "analyzed_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "error": None,
        }

    def _normalize_url(self, url: str) -> str:
        raw = (url or "").strip()
        if not raw:
            return ""
        if not raw.startswith(("http://", "https://")):
            raw = f"https://{raw}"
        parsed = urlparse(raw)
        if not parsed.netloc:
            return ""
        return raw

    def _score(self, issues: list[str], strengths: list[str]) -> int:
        """Higher = more room for Genesis to help."""
        base = min(100, len(issues) * 12)
        base = max(base, 20 if issues else 5)
        return min(100, base + (10 if len(issues) >= 3 else 0))

    def _empty_result(self, url: str, *, error: str) -> dict:
        return {
            "url": url,
            "final_url": url,
            "status_code": 0,
            "title": "",
            "load_ms": 0,
            "has_https": False,
            "has_viewport": False,
            "issues": ["Website nicht erreichbar oder ungültige URL"],
            "strengths": [],
            "issue_count": 1,
            "improvement_score": 80,
            "analyzed_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "error": error,
        }
