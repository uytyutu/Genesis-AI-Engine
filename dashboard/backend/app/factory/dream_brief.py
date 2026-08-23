"""Dream Brief — client buys the future company, not HTML sections.

Law №3: Deliver the Dream, Not the HTML.
Commercial Reality: answer «Who is this company?» before «How should it look?»
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


DREAM_STYLE_TO_APPROACH: dict[str, str] = {
    "modern": "minimal",
    "premium": "luxury",
    "minimal": "minimal",
    "minimalistisch": "minimal",
    "technological": "technology",
    "technologisch": "technology",
    "tech": "technology",
    "warm": "editorial",
    "family": "editorial",
    "warm_family": "editorial",
    "familial": "editorial",
    "industrial": "craftsman",
    "craft": "craftsman",
    "corporate": "corporate",
    "editorial": "editorial",
    "luxury": "luxury",
    "boutique": "editorial",
    "magazine": "magazine",
    "immersive": "immersive",
    "restaurant": "restaurant",
    "culinary": "restaurant",
    "legal": "legal",
    "clinic": "clinic",
    "commerce": "commerce",
}


@dataclass
class DreamBrief:
    """What the client is really buying — the felt future of their company."""

    # Who + client story first
    who_is_company: str = ""
    commercial_idea: str = ""
    client_story: str = ""
    problem_before: str = ""
    clients_who: str = ""
    why_choose_us: str = ""
    brand_feeling: str = ""
    admired_companies: str = ""
    style: str = ""
    client_fear: str = ""
    main_promise: str = ""
    # Legacy
    niche: str = ""
    city: str = ""
    services: tuple[str, ...] = field(default_factory=tuple)

    def approach(self) -> str:
        key = (self.style or "").strip().lower().replace(" ", "_")
        return DREAM_STYLE_TO_APPROACH.get(key, "")

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["services"] = list(self.services)
        d["approach"] = self.approach()
        d["law"] = "Deliver the Dream, Not the HTML"
        d["order"] = "Who is this company? → How should it look?"
        return d


def dream_brief_from_contacts(contacts: dict | None) -> DreamBrief:
    c = contacts if isinstance(contacts, dict) else {}
    dream = c.get("dream_brief") if isinstance(c.get("dream_brief"), dict) else {}
    services = c.get("services_list") or dream.get("services") or ()
    if isinstance(services, str):
        services = tuple(s.strip() for s in services.split(",") if s.strip())
    else:
        services = tuple(str(s) for s in services if str(s).strip())
    return DreamBrief(
        who_is_company=str(
            dream.get("who_is_company") or c.get("who_is_company") or ""
        ),
        commercial_idea=str(
            dream.get("commercial_idea") or c.get("commercial_idea") or ""
        ),
        client_story=str(dream.get("client_story") or c.get("client_story") or ""),
        problem_before=str(
            dream.get("problem_before") or c.get("problem_before") or ""
        ),
        clients_who=str(dream.get("clients_who") or c.get("clients_who") or ""),
        why_choose_us=str(dream.get("why_choose_us") or c.get("why_choose_us") or ""),
        brand_feeling=str(dream.get("brand_feeling") or c.get("brand_feeling") or ""),
        admired_companies=str(
            dream.get("admired_companies") or c.get("admired_companies") or ""
        ),
        style=str(dream.get("style") or c.get("style") or c.get("brand_style") or ""),
        client_fear=str(dream.get("client_fear") or c.get("client_fear") or ""),
        main_promise=str(dream.get("main_promise") or c.get("main_promise") or ""),
        niche=str(c.get("niche") or dream.get("niche") or ""),
        city=str(c.get("city") or dream.get("city") or ""),
        services=services,
    )


def portfolio_export_allowed(*, portfolio_test_yes: bool) -> bool:
    """PORTFOLIO TEST — if studio would not put it in portfolio, no export."""
    return bool(portfolio_test_yes)


__all__ = [
    "DREAM_STYLE_TO_APPROACH",
    "DreamBrief",
    "dream_brief_from_contacts",
    "portfolio_export_allowed",
]
