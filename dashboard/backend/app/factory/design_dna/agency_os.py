"""Virtus Core Agency OS — ideology as a question chain.

Not every role must be a separate module.
Every Digital Experience generation must pass these questions.

Also defines Digital Signature (recognizable craft, not sameness)
and Digital Business framing (ecosystem > page).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


MANIFEST_ID = "virtus_core_studio_era_manifest_2026_2030"
MANIFEST_PATH = "docs/VIRTUS_CORE_STUDIO_ERA_MANIFEST.md"

OWNER_BUY_PHRASE = "Да. Я бы купил такой сайт."


@dataclass(frozen=True)
class AgencyRole:
    id: str
    title: str
    question: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# Operating system of a digital agency — question chain per generation
AGENCY_ROLES: tuple[AgencyRole, ...] = (
    AgencyRole(
        "ceo",
        "CEO",
        "Does this strengthen the client's business presence — not just fill a page?",
    ),
    AgencyRole(
        "creative_director",
        "Creative Director",
        "Is the creative direction clear, ownable, and non-template?",
    ),
    AgencyRole(
        "brand_strategist",
        "Brand Strategist",
        "What is this brand's personality — and why does it exist?",
    ),
    AgencyRole(
        "marketing_strategist",
        "Marketing Strategist",
        "What should the stranger feel in 3 seconds — and what should they do?",
    ),
    AgencyRole(
        "ux_researcher",
        "UX Researcher",
        "Is the path human, calm, credible — free of constructor anxiety?",
    ),
    AgencyRole(
        "art_director",
        "Art Director",
        "Does every scene have its own composition, rhythm, mood, and visual center?",
    ),
    AgencyRole(
        "typography_director",
        "Typography Director",
        "Does type carry character and brand voice — not a default stack?",
    ),
    AgencyRole(
        "color_director",
        "Color Director",
        "Does color create the intended emotion — not decoration?",
    ),
    AgencyRole(
        "motion_director",
        "Motion Director",
        "Does every animation have meaning — or is it noise?",
    ),
    AgencyRole(
        "frontend_architect",
        "Frontend Architect",
        "Is the craft export clean, resilient, and worthy of a studio?",
    ),
    AgencyRole(
        "accessibility_specialist",
        "Accessibility Specialist",
        "Can everyone use this with dignity?",
    ),
    AgencyRole(
        "performance_engineer",
        "Performance Engineer",
        "Does beauty stay fast on real devices?",
    ),
    AgencyRole(
        "qa_designer",
        "QA Designer",
        "Would a European digital studio ship this without shame?",
    ),
    AgencyRole(
        "owner_review",
        "Owner Review",
        f'Has the owner said: "{OWNER_BUY_PHRASE}"?',
    ),
)


@dataclass(frozen=True)
class DigitalSignature:
    """Recognizable craft level — handwriting of quality, not a template."""

    name: str = "Virtus Core Digital Signature"
    aim: str = (
        "Stranger thinks: I don't know who made this — but the work is clearly strong."
    )
    craft_marks: tuple[str, ...] = (
        "attention to detail",
        "meaningful motion",
        "strong typography",
        "harmonious spacing",
        "considered interactive states",
        "coherent interaction sequences",
    )
    never: tuple[str, ...] = (
        "same colors across every niche",
        "identical compositions",
        "constructor ladders",
        "empty decorative zones",
        "motion without meaning",
    )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


DIGITAL_SIGNATURE = DigitalSignature()


@dataclass(frozen=True)
class EcosystemSurface:
    id: str
    label: str
    role: str  # how it serves the digital business

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# Digital business ecosystem — site is one surface, not the end product
ECOSYSTEM_SURFACES: tuple[EcosystemSurface, ...] = (
    EcosystemSurface("experience", "Digital Experience (site/store)", "first impression & brand face"),
    EcosystemSurface("booking", "Booking / scheduling", "convert intent to appointments"),
    EcosystemSurface("crm", "CRM", "remember and serve the client"),
    EcosystemSurface("reminders", "Automated reminders", "reduce no-shows"),
    EcosystemSurface("chat", "Chat / assistant", "answer when humans sleep"),
    EcosystemSurface("reviews", "Reviews", "trust at scale"),
    EcosystemSurface("seo", "SEO", "be found"),
    EcosystemSurface("ads", "Advertising", "reach with brand integrity"),
    EcosystemSurface("analytics", "Analytics", "learn what works"),
    EcosystemSurface("video", "Video", "emotion and proof"),
    EcosystemSurface("social", "Social", "presence beyond the site"),
    EcosystemSurface("cabinet", "Client cabinet", "ongoing relationship"),
)


WRONG_FRAME = 'Create a dentist website.'
RIGHT_FRAME = 'Create the digital business of a dental clinic.'


@dataclass
class AgencyReview:
    """Ideology checklist for one generation — questions, not auto PASS."""

    manifest_id: str = MANIFEST_ID
    roles: list[dict[str, Any]] = field(default_factory=list)
    digital_signature: dict[str, Any] = field(default_factory=dict)
    ecosystem_frame: dict[str, Any] = field(default_factory=dict)
    owner_buy_phrase: str = OWNER_BUY_PHRASE
    owner_review: str = "PENDING_OWNER"
    note: str = (
        "Roles are questions every generation must face. "
        "PASS only after human approval."
    )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_agency_review(
    *,
    niche_id: str = "generic",
    package_id: str = "business",
    business_name: str = "",
) -> AgencyReview:
    """Build the Agency OS question pack for this Digital Experience."""
    niche = (niche_id or "generic").strip().lower()
    name = (business_name or "Business").strip() or "Business"
    return AgencyReview(
        roles=[r.as_dict() for r in AGENCY_ROLES],
        digital_signature=DIGITAL_SIGNATURE.as_dict(),
        ecosystem_frame={
            "wrong": WRONG_FRAME,
            "right": RIGHT_FRAME,
            "for_this_project": (
                f"Create the digital business of {name} ({niche}) — "
                "experience is one surface of the ecosystem, not the end product."
            ),
            "surfaces": [s.as_dict() for s in ECOSYSTEM_SURFACES],
            "package_id": package_id,
        },
        owner_review="PENDING_OWNER",
    )


def agency_questions() -> list[str]:
    return [f"{r.title}: {r.question}" for r in AGENCY_ROLES]
