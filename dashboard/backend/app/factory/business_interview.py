"""Smart AI Business Interview — understand the owner before generating.

Supports structured answers and free-text dialogue parsing.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


STYLE_OPTIONS: tuple[str, ...] = (
    "modern",
    "premium",
    "minimal",
    "friendly",
    "strict",
    "technological",
    "luxury",
    "natural",
    "german_classic",
    "youthful",
)

SITE_JOB_OPTIONS: tuple[str, ...] = (
    "leads",
    "booking",
    "sell",
    "portfolio",
    "faq",
    "services",
)


@dataclass
class BusinessInterview:
    """Normalized interview answers."""

    company_name: str = ""
    about: str = ""
    city: str = ""
    founded: str = ""
    team: str = ""
    clients_who: str = ""
    style: str = ""
    site_jobs: tuple[str, ...] = ()
    differentiator: str = ""
    top_services: tuple[str, ...] = ()
    wishes: str = ""
    free_text: str = ""
    niche_hint: str = ""
    source: str = "form"  # form | dialogue | hybrid
    # Adaptive clarifying answers (business questions — never technical)
    clarify_answers: dict[str, str] = field(default_factory=dict)
    dream_vision: str = ""  # Dream Mode — 5-year aspiration
    business_scale: str = ""  # solo | small_team | company | franchise

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["site_jobs"] = list(self.site_jobs)
        d["top_services"] = list(self.top_services)
        d["clarify_answers"] = dict(self.clarify_answers or {})
        return d


_NICHE_WORDS: dict[str, tuple[str, ...]] = {
    "dachreinigung": ("dach", "dächer", "daech", "moos", "dachrinne", "roof"),
    "handwerk": ("renovier", "handwerk", "meister", "fliese", "küche", "kueche", "maler", "reparatur", "dächer", "dach"),
    "restaurant": ("restaurant", "küche", "speisekarte", "gast", "pizza", "sushi", "café", "cafe"),
    "psychology": ("psycholog", "therapie", "cbt", "angst", "beratung", "sitzung"),
    "dental": ("zahn", "dental", "praxis"),
    "law": ("anwalt", "kanzlei", "recht", "jura"),
    "beauty": ("friseur", "kosmetik", "beauty", "salon"),
    "fitness": ("fitness", "trainer", "studio", "gym"),
    "auto": ("auto", "werkstatt", "reifen", "abschlepp", "autohaus"),
    "cleaning": ("reinigung", "putz", "clean"),
    "realestate": ("immobilie", "makler", "wohnung", "hausverkauf"),
    "gartenpflege": ("garten", "hecke", "rasen"),
}


def infer_niche_from_text(text: str) -> str:
    blob = (text or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    scores: dict[str, int] = {}
    for niche, words in _NICHE_WORDS.items():
        scores[niche] = sum(
            1
            for w in words
            if w.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue") in blob
            or w in (text or "").lower()
        )
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0] if best[1] > 0 else ""


def parse_dialogue(text: str) -> BusinessInterview:
    """Parse free-language owner story into interview fields."""
    raw = (text or "").strip()
    lower = raw.lower()
    iv = BusinessInterview(free_text=raw, source="dialogue")

    # City (simple DE patterns)
    m_city = re.search(
        r"\b(?:in|aus|bei)\s+([A-ZÄÖÜ][a-zäöüß]+(?:[\s-][A-ZÄÖÜ][a-zäöüß]+)?)",
        raw,
    )
    if m_city:
        iv.city = m_city.group(1)

    m_years = re.search(r"(\d+)\s*Jahre", raw, re.I)
    if m_years:
        iv.founded = f"{m_years.group(1)} years experience"

    if any(w in lower for w in ("bruder", "familie", "family", "team")):
        iv.team = "family_or_small_team"
    if any(w in lower for w in ("allein", "solo", "selbständig", "einzel")):
        iv.team = "solo"

    if any(w in lower for w in ("nicht die günstig", "premium", "qualität", "teuer")):
        iv.style = "premium"
        iv.clients_who = "quality_seekers"
    elif any(w in lower for w in ("modern", "zeitgemäß")):
        iv.style = "modern"
    elif any(w in lower for w in ("ruhig", "vertrauen", "calm", "trust")):
        iv.style = "minimal"
    elif any(w in lower for w in ("luxus", "luxury", "exklusiv")):
        iv.style = "luxury"

    if "vertrauen" in lower or "trust" in lower:
        iv.differentiator = "Vertrauen durch nachweisbare Qualität"
    if "modern" in lower and not iv.differentiator:
        iv.differentiator = "Modernes Auftreten mit handfester Substanz"

    # Differentiator: last strong sentence often carries wish
    wish_m = re.search(
        r"(?:möchte|will|want|хочу)[^.!\n]{8,160}",
        raw,
        re.I,
    )
    if wish_m:
        iv.wishes = wish_m.group(0).strip()

    iv.niche_hint = infer_niche_from_text(raw)
    iv.about = raw[:500]

    jobs: list[str] = ["leads", "services"]
    if any(w in lower for w in ("termin", "buch", "reserv", "booking")):
        jobs.append("booking")
    if any(w in lower for w in ("shop", "verkauf", "produkt")):
        jobs.append("sell")
    if any(w in lower for w in ("portfolio", "galerie", "referenz", "projekt")):
        jobs.append("portfolio")
    if any(w in lower for w in ("lieferung", "delivery", "liefern")):
        jobs.append("delivery")
        jobs.append("sell")
    if any(w in lower for w in ("online", "video-sitzung", "videosprech")):
        jobs.append("booking")
    iv.site_jobs = tuple(dict.fromkeys(jobs))

    from app.factory.interview_clarify import detect_business_scale

    iv.business_scale = detect_business_scale(text=raw, team=iv.team)

    return iv


def interview_from_payload(data: dict[str, Any] | None) -> BusinessInterview:
    """Build interview from API / form payload; merge free_text dialogue."""
    d = data if isinstance(data, dict) else {}
    free = str(d.get("free_text") or d.get("dialogue") or d.get("story") or "").strip()
    base = parse_dialogue(free) if free else BusinessInterview(source="form")

    def pick(*keys: str, default: str = "") -> str:
        for k in keys:
            v = d.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
        return default

    services = d.get("top_services") or d.get("services") or d.get("services_list") or ()
    if isinstance(services, str):
        services_t = tuple(s.strip() for s in re.split(r"[,;\n]", services) if s.strip())
    else:
        services_t = tuple(str(s).strip() for s in services if str(s).strip())

    jobs = d.get("site_jobs") or d.get("goals") or base.site_jobs
    if isinstance(jobs, str):
        jobs_t = tuple(j.strip() for j in re.split(r"[,;|]", jobs) if j.strip())
    else:
        jobs_t = tuple(str(j).strip() for j in jobs if str(j).strip()) or base.site_jobs

    style = pick("style", "brand_style", default=base.style)
    if style and style.lower() not in {s.lower() for s in STYLE_OPTIONS}:
        # keep custom style string — dream_brief maps what it can
        pass

    clarify_raw = d.get("clarify_answers") or d.get("clarifying_answers") or {}
    if not isinstance(clarify_raw, dict):
        clarify_raw = {}
    clarify = {str(k): str(v) for k, v in clarify_raw.items() if str(v).strip()}

    dream = pick("dream_vision", "dream", "five_year_dream", default="")
    if not dream and base.wishes and "jahr" in base.wishes.lower():
        dream = base.wishes

    from app.factory.interview_clarify import (
        apply_clarify_to_site_jobs,
        detect_business_scale,
    )

    scale = pick("business_scale", "scale", default=base.business_scale)
    if clarify.get("business_scale") in (
        "solo",
        "small_team",
        "company",
        "franchise",
    ):
        scale = clarify["business_scale"]
    if not scale:
        scale = detect_business_scale(
            text=free or base.free_text,
            team=pick("team", default=base.team),
            clarify_answers=clarify,
        )
    jobs_merged = apply_clarify_to_site_jobs(jobs_t, clarify)

    return BusinessInterview(
        company_name=pick("company_name", "business_name", default=base.company_name),
        about=pick("about", "company_about", default=base.about),
        city=pick("city", default=base.city),
        founded=pick("founded", "opened", default=base.founded),
        team=pick("team", default=base.team),
        clients_who=pick("clients_who", "clients", default=base.clients_who),
        style=style,
        site_jobs=jobs_merged or jobs_t,
        differentiator=pick(
            "differentiator", "why_choose_us", "usp", default=base.differentiator
        ),
        top_services=services_t or base.top_services,
        wishes=pick("wishes", "notes", "special_wishes", default=base.wishes),
        free_text=free or base.free_text,
        niche_hint=pick("niche", "niche_id", default=base.niche_hint),
        source="hybrid" if free and d.get("about") else ("dialogue" if free else "form"),
        clarify_answers=clarify,
        dream_vision=dream,
        business_scale=scale,
    )


def interview_to_contacts(iv: BusinessInterview, contacts: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge interview into factory contacts + dream_brief shape."""
    c = dict(contacts or {})
    if iv.company_name:
        c["business_name"] = iv.company_name
    if iv.city:
        c["city"] = iv.city
    if iv.style:
        c["brand_style"] = iv.style
        c["style"] = iv.style
    if iv.top_services:
        c["services_list"] = list(iv.top_services)
    if iv.site_jobs:
        c["site_jobs"] = list(iv.site_jobs)
    if iv.differentiator:
        c["why_choose_us"] = iv.differentiator
        c["main_promise"] = iv.differentiator
    if iv.about:
        c["who_is_company"] = iv.about
        if not str(c.get("client_story") or "").strip():
            c["client_story"] = iv.about
    if iv.clients_who:
        c["clients_who"] = iv.clients_who
    if iv.wishes:
        c["dream_wishes"] = iv.wishes
    if iv.team:
        c["team_note"] = iv.team
    if iv.niche_hint and not c.get("niche"):
        c["niche"] = iv.niche_hint
    if iv.clarify_answers:
        c["clarify_answers"] = dict(iv.clarify_answers)
    if iv.dream_vision:
        c["dream_vision"] = iv.dream_vision
    if iv.business_scale:
        c["business_scale"] = iv.business_scale

    from app.factory.interview_clarify import build_clarify_session

    session = build_clarify_session(
        niche_id=iv.niche_hint or str(c.get("niche") or ""),
        answered=iv.clarify_answers,
        free_text=iv.free_text or iv.about,
        team=iv.team,
        dream=iv.dream_vision,
        site_jobs=iv.site_jobs,
    )
    c["clarify_session"] = session.as_dict()
    c["technical_decisions"] = session.technical

    c["business_interview"] = iv.as_dict()
    prev_dream = c.get("dream_brief") if isinstance(c.get("dream_brief"), dict) else {}
    # Never wipe gallery / CEO dream_brief stories with empty interview free_text
    story = (
        (iv.free_text or "").strip()
        or (iv.about or "").strip()
        or str(prev_dream.get("client_story") or "").strip()
        or str(c.get("client_story") or "").strip()
    )
    dream_brief = {
        **prev_dream,
        "who_is_company": iv.about or prev_dream.get("who_is_company") or c.get("who_is_company") or "",
        "clients_who": iv.clients_who or prev_dream.get("clients_who") or "",
        "why_choose_us": iv.differentiator
        or prev_dream.get("why_choose_us")
        or "",
        "brand_feeling": iv.style or prev_dream.get("brand_feeling") or "",
        "style": iv.style or prev_dream.get("style") or "",
        "main_promise": iv.differentiator
        or prev_dream.get("main_promise")
        or "",
        "client_story": story,
        "problem_before": prev_dream.get("problem_before") or c.get("problem_before") or "",
        "admired_companies": iv.wishes or prev_dream.get("admired_companies") or "",
        "services": list(iv.top_services)
        or list(prev_dream.get("services") or []),
        "city": iv.city or prev_dream.get("city") or "",
        "niche": iv.niche_hint or c.get("niche") or prev_dream.get("niche") or "",
        "dream_vision": iv.dream_vision or prev_dream.get("dream_vision") or "",
        "business_scale": iv.business_scale
        or prev_dream.get("business_scale")
        or session.scale,
    }
    if story and not str(c.get("client_story") or "").strip():
        c["client_story"] = story
    if session.dream_signals.get("ambition"):
        dream_brief["ambition"] = session.dream_signals["ambition"]
        dream_brief["hero_bias"] = session.dream_signals.get("hero_bias") or ""
    c["dream_brief"] = dream_brief
    return c


__all__ = [
    "BusinessInterview",
    "SITE_JOB_OPTIONS",
    "STYLE_OPTIONS",
    "infer_niche_from_text",
    "interview_from_payload",
    "interview_to_contacts",
    "parse_dialogue",
]
