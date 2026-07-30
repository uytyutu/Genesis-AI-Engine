"""Lightweight website analysis for Business Acquisition Studio.

Stealth Mode: robots.txt, rate limit, browser UA, read-only GET.
Issue copy is localized by generation language (not hardcoded German).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from app.integration.lead_qualification_gate import extract_emails_from_text
from app.integration.site_analysis_i18n import (
    analysis_lang_base,
    issue_message,
    localize_analysis_issues,
    strength_message,
)
from app.integration.stealth_crawl_service import stealth_fetch_get, stealth_preflight
from app.integration.stealth_http import UnauthorizedOperation

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"
_CACHE_TTL_HOURS = 72


def _stealth_issue_message(err: str, lang: str) -> list[str]:
    # Keep operational stealth messages short; prefer English outside DE.
    if err == "Unauthorized Operation":
        if lang == "de":
            return ["Unauthorized Operation — nur GET/HEAD erlaubt"]
        return ["Unauthorized Operation — only GET/HEAD allowed"]
    if err == "robots_txt_disallowed":
        if lang == "de":
            return ["robots.txt verbietet Zugriff — Genesis geht vorbei"]
        return ["robots.txt disallows access — skipping"]
    if err == "forbidden_target":
        if lang == "de":
            return ["Geschützter Bereich (admin/login) — nur öffentliche Seiten"]
        return ["Protected section (admin/login) — public pages only"]
    if lang == "de":
        return ["Scan übersprungen — Stealth Mode"]
    return ["Scan skipped — Stealth Mode"]


class SiteAnalysisService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _cache_path(self, url: str, language: str = "en") -> Path:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return self._memory / "site_analysis_cache" / f"{key}_{language}.json"

    def _legacy_cache_path(self, url: str) -> Path:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return self._memory / "site_analysis_cache" / f"{key}.json"

    def _load_cache(self, url: str, language: str) -> dict | None:
        for path in (self._cache_path(url, language), self._legacy_cache_path(url)):
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    continue
                analyzed = str(data.get("analyzed_at") or "")
                if analyzed:
                    from datetime import datetime, timezone, timedelta

                    dt = datetime.fromisoformat(analyzed.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if datetime.now(timezone.utc) - dt > timedelta(hours=_CACHE_TTL_HOURS):
                        continue
                # Re-localize if cache language differs / legacy DE blob.
                cached_lang = str(data.get("analysis_language") or "").lower()
                codes = data.get("issue_codes")
                if isinstance(codes, list) and codes:
                    data["issues"] = localize_analysis_issues(
                        None, language=language, codes=codes
                    )
                elif cached_lang != language:
                    data["issues"] = localize_analysis_issues(
                        list(data.get("issues") or []), language=language
                    )
                data["analysis_language"] = language
                data["from_cache"] = True
                return data
            except (json.JSONDecodeError, OSError, ValueError):
                continue
        return None

    def _save_cache(self, url: str, result: dict, language: str) -> None:
        path = self._cache_path(url, language)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    def analyze(
        self,
        url: str,
        *,
        use_cache: bool = True,
        language: str | None = None,
        market: str | None = None,
    ) -> dict:
        lang = analysis_lang_base(language, market)
        normalized = self._normalize_url(url)
        if not normalized:
            return self._empty_result(url, error="invalid_url", language=lang)

        if use_cache:
            cached = self._load_cache(normalized, lang)
            if cached:
                return cached

        try:
            started = stealth_fetch_get(normalized)
            gate = stealth_preflight(normalized, skip_throttle=True)
        except ValueError as exc:
            err = str(exc)
            gate = stealth_preflight(normalized, skip_throttle=True)
            return {
                **self._empty_result(normalized, error=err, language=lang),
                "issues": _stealth_issue_message(err, lang),
                "stealth": {
                    "mode": "stealth",
                    "robots_checked": gate.robots_checked,
                    "robots_allowed": gate.robots_allowed,
                    "read_only": True,
                },
            }
        except UnauthorizedOperation:
            gate = stealth_preflight(normalized, skip_throttle=True)
            return {
                **self._empty_result(
                    normalized, error="Unauthorized Operation", language=lang
                ),
                "issues": ["Unauthorized Operation — Stealth Force-Read-Only"],
                "stealth": {
                    "mode": "stealth",
                    "robots_checked": gate.robots_checked,
                    "robots_allowed": gate.robots_allowed,
                    "read_only": False,
                },
            }
        except Exception as exc:
            return self._empty_result(
                normalized,
                error=f"fetch_failed:{type(exc).__name__}",
                language=lang,
            )

        html = started.text or ""
        final_url = str(started.url)
        issue_codes: list[str] = []
        strength_codes: list[tuple[str, dict]] = []

        if not final_url.startswith("https://"):
            issue_codes.append("no_https")
        else:
            strength_codes.append(("https_ok", {}))

        if started.status_code >= 400:
            issue_codes.append(f"http_error:{started.status_code}")
        elif started.status_code == 200:
            strength_codes.append(("reachable", {}))

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
            issue_codes.append("no_viewport")
        else:
            strength_codes.append(("viewport_ok", {}))

        content_thin = len(html) < 1500
        if content_thin:
            issue_codes.append("thin_content")

        if any(x in lower for x in ("jquery-1.", "flash", "under construction", "coming soon")):
            issue_codes.append("outdated_tech")

        has_form = bool(
            re.search(r"<form\b|type=[\"']email[\"']|name=[\"']email[\"']", lower)
        )
        has_mailto = bool(re.search(r"mailto:", lower))
        has_phone = bool(re.search(r"tel:|whatsapp|wa\.me", lower))
        has_contact = has_mailto or has_phone or has_form

        if not has_form and not has_mailto:
            issue_codes.append("no_contact_form")
        if not has_phone:
            issue_codes.append("no_call_whatsapp")
        if has_contact:
            strength_codes.append(("contact_ok", {}))

        has_cta = bool(
            re.search(
                r"(?:jetzt|anrufen|anfragen|buchen|termin|bestellen|kontakt|"
                r"order|book|call|contact|запис|заказ|звон|заявк)",
                lower,
            )
            and re.search(r"<a\b|<button\b", lower)
        )
        if has_cta:
            strength_codes.append(("cta_ok", {}))
        else:
            issue_codes.append("no_cta")

        has_maps = bool(
            re.search(
                r"google\.(?:com|de)/maps|maps\.google|googleapis\.com/maps|"
                r"openstreetmap|mapbox",
                lower,
            )
        )
        if has_maps:
            strength_codes.append(("maps_ok", {}))
        else:
            issue_codes.append("no_maps")

        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
        title = title_match.group(1).strip() if title_match else ""
        if not title:
            issue_codes.append("no_title")

        if "og:" not in lower and "twitter:" not in lower:
            issue_codes.append("no_social_meta")

        load_ms = int(started.elapsed.total_seconds() * 1000) if started.elapsed else 0
        if load_ms > 3000:
            issue_codes.append(f"slow_response:{load_ms}")
        elif load_ms > 0:
            strength_codes.append(("load_ok", {"ms": load_ms}))

        issues = localize_analysis_issues(None, language=lang, codes=issue_codes)
        strengths = [
            strength_message(code, lang, **fmt) for code, fmt in strength_codes
        ]

        emails_found = extract_emails_from_text(html)
        for m in re.findall(r"mailto:([^\s\"'?]+)", html, re.I):
            emails_found.extend(extract_emails_from_text(m))
        emails_found = list(dict.fromkeys(emails_found))[:5]

        confirmed_needs: list[dict] = []
        try:
            from app.recommendation_engine.needs import detect_confirmed_needs

            confirmed_needs = detect_confirmed_needs(
                html=html,
                flags={
                    "has_contact": has_contact,
                    "has_form": has_form,
                    "has_cta": has_cta,
                },
                fetch_ok=started.status_code < 400,
            )
        except Exception:
            confirmed_needs = []

        score = self._score(issues, strengths)
        niche_info = None
        try:
            from app.integration.engine_ai_service import EngineAIService

            niche_info = EngineAIService().classify_niche(
                analysis={
                    "issues": issues,
                    "strengths": strengths,
                    "title": title,
                    "tech_stack": tech_stack,
                },
                company=title or normalized,
                url=final_url,
            )
        except Exception:
            niche_info = None

        result = {
            "url": normalized,
            "final_url": final_url,
            "status_code": started.status_code,
            "title": title,
            "load_ms": load_ms,
            "has_https": final_url.startswith("https://"),
            "has_viewport": "viewport" in lower,
            "flags": {
                "has_contact": has_contact,
                "has_form": has_form,
                "has_cta": has_cta,
                "has_maps": has_maps,
                "content_thin": content_thin,
            },
            "confirmed_needs": confirmed_needs,
            "issues": issues,
            "issue_codes": issue_codes,
            "strengths": strengths,
            "issue_count": len(issues),
            "improvement_score": score,
            "tech_stack": tech_stack,
            "detected_lang": detected_lang,
            "analysis_language": lang,
            "emails_found": emails_found,
            "classified_niche": niche_info,
            "analyzed_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "error": None,
            "from_cache": False,
            "stealth": {
                "mode": "stealth",
                "robots_checked": gate.robots_checked,
                "robots_allowed": gate.robots_allowed,
                "read_only": True,
            },
        }
        self._save_cache(normalized, result, lang)
        return result

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

    def _empty_result(self, url: str, *, error: str, language: str = "en") -> dict:
        return {
            "url": url,
            "final_url": url,
            "status_code": 0,
            "title": "",
            "load_ms": 0,
            "has_https": False,
            "has_viewport": False,
            "flags": {},
            "confirmed_needs": [],
            "issues": [issue_message("unreachable", language)],
            "issue_codes": ["unreachable"],
            "strengths": [],
            "issue_count": 1,
            "improvement_score": 80,
            "tech_stack": [],
            "detected_lang": "",
            "analysis_language": language,
            "emails_found": [],
            "classified_niche": None,
            "analyzed_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "error": error,
            "from_cache": False,
            "stealth": {"mode": "stealth", "read_only": True},
        }
