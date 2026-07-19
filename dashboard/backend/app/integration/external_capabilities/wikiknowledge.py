"""Wikipedia + Wikidata enrichment for internal briefs only. Not final truth."""

from __future__ import annotations

from typing import Any

from app.integration.external_capabilities.http_util import http_get_json, url_with_query
from app.integration.external_capabilities.models import AdapterResult
from app.integration.external_capabilities.registry import is_enabled

_WIKI_API = "https://de.wikipedia.org/api/rest_v1/page/summary/{title}"
_WIKI_SEARCH = "https://de.wikipedia.org/w/rest.php/v1/search/title"
_WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"


def enrich_brief(
    *,
    niche_label: str | None = None,
    city: str | None = None,
    query: str | None = None,
) -> AdapterResult:
    """Public knowledge hints for order insights. Always cite source; never claim verified."""
    topic = (query or niche_label or "").strip()
    if not topic:
        return AdapterResult(
            ok=True,
            capability_id="wikipedia",
            data={"snippets": []},
            used_fallback=True,
            error="empty_query",
        )

    wiki_on = is_enabled("wikipedia")
    wd_on = is_enabled("wikidata")
    if not wiki_on and not wd_on:
        return AdapterResult(
            ok=True,
            capability_id="wikipedia",
            data={"snippets": [], "note": "enrichment_disabled"},
            used_fallback=True,
            error="capability_disabled",
        )

    snippets: list[dict[str, Any]] = []
    errors: list[str] = []

    if wiki_on:
        search_url = url_with_query(_WIKI_SEARCH, {"q": topic, "limit": "1"})
        search, err = http_get_json(search_url, timeout=4.0)
        if err or not isinstance(search, dict):
            errors.append(err or "wiki_search_failed")
        else:
            pages = search.get("pages") or []
            title = None
            if pages and isinstance(pages[0], dict):
                title = str(pages[0].get("title") or pages[0].get("key") or "").strip()
            if title:
                from urllib.parse import quote

                summary_url = _WIKI_API.format(title=quote(title.replace(" ", "_")))
                summary, err2 = http_get_json(summary_url, timeout=4.0)
                if err2 or not isinstance(summary, dict):
                    errors.append(err2 or "wiki_summary_failed")
                else:
                    extract = str(summary.get("extract") or "").strip()[:400]
                    page_url = str(
                        (summary.get("content_urls") or {}).get("desktop", {}).get("page")
                        or f"https://de.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
                    )
                    if extract:
                        snippets.append(
                            {
                                "kind": "wikipedia",
                                "title": title,
                                "extract": extract,
                                "source_url": page_url,
                                "license": "CC BY-SA",
                                "disclaimer_de": (
                                    "Öffentliche Enzyklopädie — kein geprüfter Firmenstatus."
                                ),
                            }
                        )

    if wd_on and city:
        wd_url = url_with_query(
            _WIKIDATA_SEARCH,
            {
                "action": "wbsearchentities",
                "search": city,
                "language": "de",
                "format": "json",
                "limit": "1",
                "type": "item",
            },
        )
        wd, err = http_get_json(wd_url, timeout=4.0)
        if err or not isinstance(wd, dict):
            errors.append(err or "wikidata_failed")
        else:
            hits = wd.get("search") or []
            if hits and isinstance(hits[0], dict):
                qid = str(hits[0].get("id") or "")
                label = str(hits[0].get("label") or city)
                desc = str(hits[0].get("description") or "")[:200]
                if qid:
                    snippets.append(
                        {
                            "kind": "wikidata",
                            "title": label,
                            "extract": desc or label,
                            "source_url": f"https://www.wikidata.org/wiki/{qid}",
                            "license": "CC0",
                            "disclaimer_de": (
                                "Wikidata — strukturierter Hinweis, keine Bestätigung der Firma."
                            ),
                        }
                    )

    return AdapterResult(
        ok=True,
        capability_id="wikipedia",
        data={
            "snippets": snippets,
            "topic": topic,
            "verified": False,
            "errors": errors,
        },
        used_fallback=len(snippets) == 0,
        source=snippets[0]["source_url"] if snippets else None,
        error=";".join(errors) if errors and not snippets else None,
    )
