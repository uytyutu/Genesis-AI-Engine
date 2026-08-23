"""Adaptive clarifying questions + Dream Mode + business scale.

Law: Factory never asks the owner about sticky headers, renderers, or widgets.
It asks about the business — then decides the digital solution itself.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


BusinessScale = str  # solo | small_team | company | franchise


@dataclass(frozen=True)
class ClarifyOption:
    id: str
    label: str
    label_de: str = ""

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if not d.get("label_de"):
            d["label_de"] = d["label"]
        return d


@dataclass(frozen=True)
class ClarifyQuestion:
    id: str
    prompt: str
    prompt_de: str
    options: tuple[ClarifyOption, ...]
    why: str
    # Which business fields this answer unlocks
    unlocks: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "prompt_de": self.prompt_de,
            "why": self.why,
            "unlocks": list(self.unlocks),
            "options": [o.as_dict() for o in self.options],
        }


# —— Niche clarifying banks (adaptive; not a fixed 10-question form) ——
_CLARIFY_BANKS: dict[str, tuple[ClarifyQuestion, ...]] = {
    "psychology": (
        ClarifyQuestion(
            id="session_mode",
            prompt="Do you work online, in a practice, or both?",
            prompt_de="Arbeiten Sie online, in der Praxis oder beides?",
            why="Online vs. Praxis ändert Hero, Termin und Vertrauen.",
            unlocks=("booking", "map", "video_session"),
            options=(
                ClarifyOption("online", "Online only", "Nur online"),
                ClarifyOption("practice", "In practice", "Nur Praxis"),
                ClarifyOption("hybrid", "Both", "Beides"),
            ),
        ),
        ClarifyQuestion(
            id="therapy_focus",
            prompt="What is your main focus?",
            prompt_de="Was ist Ihr Schwerpunkt?",
            why="Unterschätzt: CBT, Angst, Paar — unterschiedliche Atmosphäre.",
            unlocks=("directions",),
            options=(
                ClarifyOption("anxiety", "Anxiety / stress", "Angst / Stress"),
                ClarifyOption("cbt", "CBT", "Kognitive Verhaltenstherapie"),
                ClarifyOption("family", "Couples / family", "Paar / Familie"),
                ClarifyOption("general", "General counseling", "Allgemeine Beratung"),
            ),
        ),
    ),
    "restaurant": (
        ClarifyQuestion(
            id="delivery",
            prompt="Do you offer delivery?",
            prompt_de="Gibt es Lieferung?",
            why="Ja → Delivery zones, order CTA, Zeitfenster.",
            unlocks=("delivery", "delivery_zones", "order_cta"),
            options=(
                ClarifyOption("yes", "Yes", "Ja"),
                ClarifyOption("no", "No — dine-in only", "Nein — nur vor Ort"),
                ClarifyOption("pickup", "Pickup only", "Nur Abholung"),
            ),
        ),
        ClarifyQuestion(
            id="cuisine_mood",
            prompt="What kind of place is it?",
            prompt_de="Welche Art von Lokal ist es?",
            why="Italienisch abends ≠ Burger-Youth ≠ Sushi-Minimal.",
            unlocks=("menu", "gallery"),
            options=(
                ClarifyOption("italian", "Italian / trattoria", "Italienisch"),
                ClarifyOption("cafe", "Café", "Café"),
                ClarifyOption("fine", "Fine dining", "Fine Dining"),
                ClarifyOption("casual", "Casual / family", "Casual / Familie"),
                ClarifyOption("asian", "Asian / sushi", "Asiatisch / Sushi"),
            ),
        ),
        ClarifyQuestion(
            id="reservations",
            prompt="Do guests book tables?",
            prompt_de="Können Gäste Tische reservieren?",
            why="Reservierung wird zum Haupt-CTA.",
            unlocks=("reservation",),
            options=(
                ClarifyOption("yes", "Yes", "Ja"),
                ClarifyOption("no", "Walk-in only", "Nur spontan"),
            ),
        ),
    ),
    "handwerk": (
        ClarifyQuestion(
            id="property_type",
            prompt="Mostly apartments, houses, or commercial?",
            prompt_de="Hauptsächlich Wohnungen, Häuser oder Gewerbe?",
            why="Wohnen vs. Gewerbe ändert Cases, Fotos und Ton.",
            unlocks=("projects", "before_after"),
            options=(
                ClarifyOption("apartments", "Apartments", "Wohnungen"),
                ClarifyOption("houses", "Private houses", "Einfamilienhäuser"),
                ClarifyOption("commercial", "Commercial", "Gewerbe / Büro"),
                ClarifyOption("mixed", "Mixed", "Gemischt"),
            ),
        ),
        ClarifyQuestion(
            id="urgency",
            prompt="Do you take emergency / same-week jobs?",
            prompt_de="Nehmen Sie Notfälle / kurzfristige Einsätze?",
            why="Notdienst → Call CTA + WhatsApp prominent.",
            unlocks=("emergency_call", "whatsapp"),
            options=(
                ClarifyOption("yes", "Yes", "Ja"),
                ClarifyOption("planned", "Planned projects only", "Nur geplante Projekte"),
            ),
        ),
    ),
    "dachreinigung": (
        ClarifyQuestion(
            id="property_type",
            prompt="Mostly private houses or larger buildings?",
            prompt_de="Hauptsächlich Einfamilienhäuser oder größere Objekte?",
            why="Maßstab ändert Equipment- und Hero-Szene.",
            unlocks=("projects", "equipment"),
            options=(
                ClarifyOption("houses", "Private houses", "Einfamilienhäuser"),
                ClarifyOption("multi", "Multi-family / commercial", "MFH / Gewerbe"),
                ClarifyOption("mixed", "Mixed", "Gemischt"),
            ),
        ),
        ClarifyQuestion(
            id="impregnation",
            prompt="Do you also impregnate / coat after cleaning?",
            prompt_de="Bieten Sie auch Imprägnierung nach der Reinigung?",
            why="Zusatzleistung → Angebot und Before/After.",
            unlocks=("services", "before_after"),
            options=(
                ClarifyOption("yes", "Yes", "Ja"),
                ClarifyOption("no", "Cleaning only", "Nur Reinigung"),
            ),
        ),
    ),
    "dental": (
        ClarifyQuestion(
            id="patient_focus",
            prompt="Private, insurance, or anxiety patients focus?",
            prompt_de="Schwerpunkt: Privat, Kasse oder Angstpatienten?",
            why="Angstpatienten brauchen andere Tone of Voice.",
            unlocks=("faq", "booking"),
            options=(
                ClarifyOption("mixed", "Mixed", "Gemischt"),
                ClarifyOption("private", "Mostly private", "Überwiegend privat"),
                ClarifyOption("anxiety", "Anxiety patients", "Angstpatienten"),
            ),
        ),
    ),
    "law": (
        ClarifyQuestion(
            id="practice_focus",
            prompt="Main practice area?",
            prompt_de="Hauptsächlicher Schwerpunkt?",
            why="Familienrecht ≠ Wirtschaftsrecht — andere Cases.",
            unlocks=("practice_areas",),
            options=(
                ClarifyOption("family", "Family / divorce", "Familie / Scheidung"),
                ClarifyOption("business", "Business / contracts", "Wirtschaft / Verträge"),
                ClarifyOption("criminal", "Criminal", "Strafrecht"),
                ClarifyOption("general", "General practice", "Allgemein"),
            ),
        ),
    ),
    "auto": (
        ClarifyQuestion(
            id="shop_type",
            prompt="Workshop, dealership, or towing?",
            prompt_de="Werkstatt, Autohaus oder Abschleppdienst?",
            why="Drei völlig unterschiedliche digitale Produkte.",
            unlocks=("booking", "listings", "emergency_call"),
            options=(
                ClarifyOption("workshop", "Workshop", "Werkstatt"),
                ClarifyOption("dealership", "Dealership", "Autohaus"),
                ClarifyOption("towing", "Towing", "Abschleppdienst"),
                ClarifyOption("detailing", "Detailing", "Detailing"),
            ),
        ),
    ),
    "beauty": (
        ClarifyQuestion(
            id="booking_need",
            prompt="Is online booking essential?",
            prompt_de="Ist Online-Terminbuchung zentral?",
            why="Salon ohne Buchung = veralteter Look.",
            unlocks=("booking",),
            options=(
                ClarifyOption("yes", "Yes — must have", "Ja — unbedingt"),
                ClarifyOption("phone", "Phone / WhatsApp only", "Nur Telefon / WhatsApp"),
            ),
        ),
    ),
    "fitness": (
        ClarifyQuestion(
            id="offer_type",
            prompt="Studio membership, personal training, or both?",
            prompt_de="Studio-Mitgliedschaft, Personal Training oder beides?",
            why="PT-Site ≠ Gym-Membership-Site.",
            unlocks=("membership", "booking"),
            options=(
                ClarifyOption("studio", "Studio / gym", "Studio"),
                ClarifyOption("pt", "Personal training", "Personal Training"),
                ClarifyOption("both", "Both", "Beides"),
            ),
        ),
    ),
    "realestate": (
        ClarifyQuestion(
            id="side",
            prompt="Sell, rent, or both?",
            prompt_de="Verkauf, Vermietung oder beides?",
            why="Listings + CTA ändern sich komplett.",
            unlocks=("listings", "inquiry"),
            options=(
                ClarifyOption("sell", "Sell", "Verkauf"),
                ClarifyOption("rent", "Rent", "Vermietung"),
                ClarifyOption("both", "Both", "Beides"),
            ),
        ),
    ),
}

_SCALE_QUESTION = ClarifyQuestion(
    id="business_scale",
    prompt="How large is the business today?",
    prompt_de="Wie groß ist das Unternehmen heute?",
    why="Solo-Meister ≠ 40-Personen-Firma ≠ Franchise — andere Site-Architektur.",
    unlocks=("crew", "multi_page", "locations"),
    options=(
        ClarifyOption("solo", "Solo / one person", "Allein / Einzelmeister"),
        ClarifyOption("small_team", "Small team (2–10)", "Kleines Team (2–10)"),
        ClarifyOption("company", "Company (10+)", "Unternehmen (10+)"),
        ClarifyOption("franchise", "Franchise / multi-location", "Franchise / mehrere Standorte"),
    ),
)

DREAM_PROMPT = (
    "If budget were not a limit — what do you dream your company looks like in five years?"
)
DREAM_PROMPT_DE = (
    "Wenn Budget egal wäre — wie soll Ihre Firma in fünf Jahren aussehen?"
)


def detect_business_scale(
    *,
    text: str = "",
    team: str = "",
    clarify_answers: dict[str, str] | None = None,
) -> BusinessScale:
    answers = clarify_answers if isinstance(clarify_answers, dict) else {}
    if answers.get("business_scale") in ("solo", "small_team", "company", "franchise"):
        return str(answers["business_scale"])

    blob = f"{text} {team}".lower()
    if any(w in blob for w in ("franchise", "filiale", "standorte", "kette")):
        return "franchise"
    if re.search(r"\b([2-9]|[1-9]\d)\s*(mitarbeiter|angestellt|leute|personen|employees)\b", blob):
        m = re.search(r"\b(\d+)\s*(mitarbeiter|angestellt|leute|personen|employees)\b", blob)
        if m and int(m.group(1)) >= 10:
            return "company"
        return "small_team"
    if any(w in blob for w in ("40 mitarbeiter", "team von", "firma mit")):
        return "company"
    if team in ("solo",) or any(
        w in blob for w in ("allein", "solo", "einzelmeister", "selbständig", "ich arbeite allein")
    ):
        return "solo"
    if team in ("family_or_small_team",) or any(
        w in blob for w in ("bruder", "familie", "zu zweit", "kleines team")
    ):
        return "small_team"
    return "small_team"


def next_clarifying_questions(
    *,
    niche_id: str,
    answered: dict[str, str] | None = None,
    free_text: str = "",
    max_questions: int = 3,
) -> list[ClarifyQuestion]:
    """Return the next unanswered clarifying questions for this business."""
    answered = dict(answered or {})
    niche = (niche_id or "").lower()
    bank = list(_CLARIFY_BANKS.get(niche, ()))

    # Generic fallbacks when niche bank empty
    if not bank:
        bank = [
            ClarifyQuestion(
                id="primary_goal",
                prompt="What should the site mainly do?",
                prompt_de="Was soll die Website vor allem tun?",
                why="Ziel bestimmt CTA und Komponenten.",
                unlocks=("leads", "booking", "portfolio"),
                options=(
                    ClarifyOption("leads", "Get inquiries", "Anfragen bekommen"),
                    ClarifyOption("booking", "Take bookings", "Termine annehmen"),
                    ClarifyOption("portfolio", "Show work", "Arbeit zeigen"),
                    ClarifyOption("sell", "Sell products", "Produkte verkaufen"),
                ),
            )
        ]

    # Skip questions already answered in free text
    out: list[ClarifyQuestion] = []
    blob = (free_text or "").lower()

    # Always consider scale early if unknown
    if "business_scale" not in answered and not any(
        w in blob for w in ("allein", "franchise", "mitarbeiter", "filiale")
    ):
        candidates = [_SCALE_QUESTION] + bank
    else:
        candidates = bank + ([_SCALE_QUESTION] if "business_scale" not in answered else [])

    for q in candidates:
        if q.id in answered:
            continue
        # Soft skip if dialogue already implies answer
        if q.id == "delivery" and any(w in blob for w in ("lieferung", "delivery", "liefer")):
            continue
        if q.id == "session_mode" and any(w in blob for w in ("online", "praxis", "video")):
            continue
        out.append(q)
        if len(out) >= max_questions:
            break
    return out


def apply_clarify_to_site_jobs(
    site_jobs: list[str] | tuple[str, ...],
    answers: dict[str, str] | None,
) -> tuple[str, ...]:
    jobs = list(site_jobs or ())
    a = answers if isinstance(answers, dict) else {}
    if a.get("delivery") in ("yes", "pickup"):
        jobs.extend(["sell", "delivery"])
    if a.get("reservations") == "yes" or a.get("session_mode") in ("online", "hybrid", "practice"):
        jobs.append("booking")
    if a.get("booking_need") == "yes":
        jobs.append("booking")
    if a.get("urgency") == "yes":
        jobs.append("leads")
    if a.get("primary_goal"):
        jobs.append(str(a["primary_goal"]))
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for j in jobs:
        jn = str(j).strip().lower()
        if jn and jn not in seen:
            seen.add(jn)
            out.append(jn)
    return tuple(out)


def apply_clarify_to_components(
    base_ids: list[str] | tuple[str, ...],
    *,
    niche_id: str,
    answers: dict[str, str] | None,
    scale: BusinessScale,
) -> list[str]:
    """Expand / prune component ids from clarifying answers + scale."""
    ids = list(base_ids)
    a = answers if isinstance(answers, dict) else {}
    niche = (niche_id or "").lower()

    def add(cid: str) -> None:
        if cid not in ids:
            ids.append(cid)

    def drop(cid: str) -> None:
        if cid in ids:
            ids.remove(cid)

    if a.get("delivery") == "yes":
        add("delivery")
        add("delivery_zones")
        add("order_cta")
    if a.get("delivery") == "pickup":
        add("order_cta")
    if a.get("reservations") == "yes":
        add("reservation")
    if a.get("session_mode") == "online":
        add("session_calendar")
        add("first_consultation")
        drop("map")
    if a.get("session_mode") in ("practice", "hybrid"):
        add("map")
        add("session_calendar")
    if a.get("urgency") == "yes":
        add("emergency_call")
        add("whatsapp")
    if a.get("booking_need") == "yes":
        add("booking")
    if a.get("impregnation") == "yes":
        add("before_after")
        add("services")

    # Scale shapes architecture signals (consumed by BI / renderers)
    if scale == "solo":
        drop("crew")  # single face, not team wall
        add("personal_story")
    elif scale == "company":
        add("crew")
        add("process")
        add("multi_page")
    elif scale == "franchise":
        add("locations")
        add("crew")
        add("multi_page")
        add("franchise_story")

    if niche == "restaurant" and a.get("cuisine_mood"):
        add("menu")
        add("gallery")

    return ids


def dream_influence(dream_text: str) -> dict[str, str]:
    """Turn Dream Mode answer into brand / Hero / ambition signals."""
    raw = (dream_text or "").strip()
    lower = raw.lower()
    out = {
        "dream": raw,
        "ambition": "local_leader",
        "hero_bias": "aspirational_trust",
        "tone": "confident_calm",
    }
    if not raw:
        return {"dream": "", "ambition": "", "hero_bias": "", "tone": ""}

    if any(w in lower for w in ("best", "beste", "führend", "nummer 1", "leading")):
        out["ambition"] = "category_leader"
        out["hero_bias"] = "authority"
        out["tone"] = "confident_premium"
    if any(w in lower for w in ("berlin", "stadt", "region", "lokal")):
        out["ambition"] = "city_reference"
        out["hero_bias"] = "local_pride"
    if any(w in lower for w in ("franchise", "deutschland", "expand", "wachs", "filiale")):
        out["ambition"] = "scale_up"
        out["hero_bias"] = "growth"
        out["tone"] = "modern_bold"
    if any(w in lower for w in ("vertrauen", "trust", "ruhe", "calm")):
        out["tone"] = "trust_first"
        out["hero_bias"] = "human_proof"
    if any(w in lower for w in ("luxus", "premium", "exklusiv")):
        out["tone"] = "luxury"
        out["hero_bias"] = "refined"
    return out


def technical_decisions_from_business(
    *,
    niche_id: str,
    scale: BusinessScale,
    site_jobs: tuple[str, ...] | list[str],
    clarify_answers: dict[str, str] | None = None,
    multi_service: bool = False,
) -> dict[str, Any]:
    """Factory owns UX architecture — owner never chooses these."""
    jobs = {str(j).lower() for j in site_jobs}
    a = clarify_answers if isinstance(clarify_answers, dict) else {}
    page_count = "landing"
    if scale in ("company", "franchise") or multi_service or len(jobs) >= 4:
        page_count = "multi_page"
    if a.get("delivery") == "yes" or "sell" in jobs:
        page_count = "multi_page" if scale != "solo" else "landing_plus"

    nav = "topbar"
    if page_count == "multi_page" and scale in ("company", "franchise"):
        nav = "topbar_with_section_panel"

    return {
        "law": "Factory owns technical decisions from business understanding",
        "page_architecture": page_count,
        "navigation": nav,
        "sticky_header": scale != "solo",
        "show_crew_section": scale in ("small_team", "company", "franchise"),
        "show_locations": scale == "franchise" or a.get("session_mode") != "online",
        "primary_cta": (
            "reservation"
            if a.get("reservations") == "yes"
            else "booking"
            if "booking" in jobs or a.get("booking_need") == "yes"
            else "order"
            if a.get("delivery") in ("yes", "pickup")
            else "whatsapp"
            if a.get("urgency") == "yes"
            else "contact"
        ),
        "renderer_hint": "auto",  # never user-selected
        "components_source": "business_intelligence",
    }


@dataclass
class ClarifySession:
    niche_id: str
    questions: list[ClarifyQuestion] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    scale: BusinessScale = "small_team"
    dream: str = ""
    dream_signals: dict[str, str] = field(default_factory=dict)
    technical: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "niche_id": self.niche_id,
            "questions": [q.as_dict() for q in self.questions],
            "answers": dict(self.answers),
            "scale": self.scale,
            "dream": self.dream,
            "dream_prompt": DREAM_PROMPT,
            "dream_prompt_de": DREAM_PROMPT_DE,
            "dream_signals": dict(self.dream_signals),
            "technical_decisions": dict(self.technical),
            "law": (
                "Factory does not ask technical questions. "
                "It asks about the business — then designs the digital solution."
            ),
        }


def build_clarify_session(
    *,
    niche_id: str,
    answered: dict[str, str] | None = None,
    free_text: str = "",
    team: str = "",
    dream: str = "",
    site_jobs: list[str] | tuple[str, ...] = (),
    max_questions: int = 3,
) -> ClarifySession:
    answers = dict(answered or {})
    scale = detect_business_scale(text=free_text, team=team, clarify_answers=answers)
    questions = next_clarifying_questions(
        niche_id=niche_id,
        answered=answers,
        free_text=free_text,
        max_questions=max_questions,
    )
    dream_sig = dream_influence(dream)
    jobs = apply_clarify_to_site_jobs(site_jobs, answers)
    tech = technical_decisions_from_business(
        niche_id=niche_id,
        scale=scale,
        site_jobs=jobs,
        clarify_answers=answers,
    )
    return ClarifySession(
        niche_id=(niche_id or "").lower(),
        questions=questions,
        answers=answers,
        scale=scale,
        dream=dream,
        dream_signals=dream_sig,
        technical=tech,
    )


__all__ = [
    "BusinessScale",
    "ClarifyOption",
    "ClarifyQuestion",
    "ClarifySession",
    "DREAM_PROMPT",
    "DREAM_PROMPT_DE",
    "apply_clarify_to_components",
    "apply_clarify_to_site_jobs",
    "build_clarify_session",
    "detect_business_scale",
    "dream_influence",
    "next_clarifying_questions",
    "technical_decisions_from_business",
]
