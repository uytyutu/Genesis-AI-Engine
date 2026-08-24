"""B4.0 — Vector Business Companion contracts (scope lock).

APPROVED order (do not reorder without CEO):
  B4.0 Contracts → B4.1 Auth+Context → B4.2 READ → B4.3 CLARIFY+i18n
  → B4.4 ACTION+Confirm → B4.5 Website/Shop analysis → B4.6 Web Research
  → B4.7 Capability honesty

Laws (binding for B4.1+):
  1. One Vector. Surface context changes; no Website-/Shop-Vector clones.
  2. Client facts ONLY from GET /api/client/context (b3_client_context_v1) —
     no Vector-private copy of products / analytics / orders.
  3. Never invent client metrics, ownership, or niche facts.
  4. READ may analyze/explain; RESEARCH must label external sources;
     ACTION never mutates until explicit Übernehmen confirmation.
  5. First ACTION set: navigate + existing live website/store capabilities only.
  6. Entry UI: VectorDialogDock (persistent BCC companion). Expanded workspace
     is optional later — same Context SSOT.
  7. Frozen under B4: Factory, Game, Video, Product-first, Analytics Foundation
     rewrites (Context may be *consumed*; not re-architected).

This module is contracts only — no turn pipeline, no LLM, no research fetch.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

# --- Slice lock -------------------------------------------------------------

B4_ENGINE = "b4_vector_companion_v1"
CONTEXT_ENGINE_REQUIRED = "b3_client_context_v1"
CONTEXT_PATH = "/api/client/context"

B4_SLICE_ORDER: tuple[str, ...] = (
    "B4.0",
    "B4.1",
    "B4.2",
    "B4.3",
    "B4.4",
    "B4.5",
    "B4.6",
    "B4.7",
)

# --- Intent / mode ----------------------------------------------------------

CompanionIntent = Literal["read", "clarify", "research", "action"]

# --- BCC route awareness (where the client stands) --------------------------

CompanionLocation = Literal[
    "dashboard",
    "products",
    "website",
    "shop",
    "analytics",
    "settings",
    "support",
    "billing",
    "other",
]

CompanionSurface = Literal[
    "customer",  # BCC — primary for Business Companion
    "website_admin",
    "store_admin",
    "platform",
]

ENTRY_SURFACE = "VectorDialogDock"
ASSISTANT_NAME = "Vector"
DEFAULT_GREETING_DE = (
    "Guten Tag! Ich bin Vector, dein Business Assistant."
)

# Companion voice: proactive Context-aware, not empty « Чем могу помочь? »
VOICE_PRINCIPLE = (
    "Speak as a Virtus Core employee who already sees the client's products "
    "and Context. Lead with what is true now and one concrete next step. "
    "Never invent missing facts — clarify instead."
)

# --- Permissions ------------------------------------------------------------

READ_SCOPES: tuple[str, ...] = (
    "business",
    "products",
    "website",
    "shop",
    "ai",
    "analytics",
    "orders",
)

# B4.4 first set only — expand later with CEO approval
FIRST_ACTION_KINDS: tuple[str, ...] = (
    "navigate",
    "live_website_capability",
    "live_store_capability",
)

CONFIRM_CTA_LABEL = "Übernehmen"
CONFIRM_CANCEL_LABEL = "Abbrechen"

# --- Research (B4.6) --------------------------------------------------------

RESEARCH_SOURCE_KIND = "external"
RESEARCH_DISCLAIMER_DE = (
    "Externe Information (Web Research) — nicht aus Ihren Virtus-Core-Daten."
)

# --- Forbidden worlds (access boundary) -------------------------------------

FORBIDDEN_WORLDS: tuple[str, ...] = (
    "factory",
    "game",
    "video",
    "farm",
    "alpha_hunter",
    "mission_control_owner",
    "other_tenant",
)


@dataclass(frozen=True)
class CompanionTurnRequest:
    """Inbound turn envelope (B4.1+). Contracts only — not wired yet."""

    customer_id: str
    message: str
    location: CompanionLocation = "dashboard"
    surface: CompanionSurface = "customer"
    locale_hint: str | None = None
    page_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContextRef:
    """Pointer to SSOT — Vector must load this, not duplicate payloads long-term."""

    path: str = CONTEXT_PATH
    engine: str = CONTEXT_ENGINE_REQUIRED
    period: str = "30d"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchSource:
    """B4.6 — every research claim must carry at least one external source."""

    title: str
    url: str
    retrieved_at: str  # ISO
    kind: str = RESEARCH_SOURCE_KIND

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["disclaimer"] = RESEARCH_DISCLAIMER_DE
        return d


@dataclass(frozen=True)
class ActionProposal:
    """B4.4 — proposed mutation or navigation; never applied until confirmed."""

    proposal_id: str
    kind: str  # must be in FIRST_ACTION_KINDS for v1
    capability_id: str | None
    label: str
    summary: str
    href: str | None = None
    section: str | None = None
    irreversible: bool = False
    confirm_label: str = CONFIRM_CTA_LABEL
    cancel_label: str = CONFIRM_CANCEL_LABEL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionConfirmation:
    """Client confirms Übernehmen for a prior proposal_id."""

    proposal_id: str
    confirmed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompanionTurnResponse:
    """Outbound turn shape (B4.1+)."""

    ok: bool = True
    engine: str = B4_ENGINE
    intent: CompanionIntent = "read"
    assistant: str = ASSISTANT_NAME
    greeting_used: bool = False
    message: str = ""
    clarify_question: str | None = None
    context_ref: dict[str, Any] = field(default_factory=lambda: ContextRef().to_dict())
    cited_read_scopes: list[str] = field(default_factory=list)
    research_sources: list[dict[str, Any]] = field(default_factory=list)
    research_disclaimer: str | None = None
    action_proposal: dict[str, Any] | None = None
    location: CompanionLocation = "dashboard"
    honesty: str = (
        "Facts from Client Context only; research labeled external; "
        "no ACTION without Übernehmen."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "engine": self.engine,
            "intent": self.intent,
            "assistant": self.assistant,
            "greeting_used": self.greeting_used,
            "message": self.message,
            "clarify_question": self.clarify_question,
            "context_ref": self.context_ref,
            "cited_read_scopes": list(self.cited_read_scopes),
            "research_sources": list(self.research_sources),
            "research_disclaimer": self.research_disclaimer,
            "action_proposal": self.action_proposal,
            "location": self.location,
            "honesty": self.honesty,
            "entry_surface": ENTRY_SURFACE,
            "voice_principle": VOICE_PRINCIPLE,
        }


def assert_research_labeled(sources: list[ResearchSource] | list[dict[str, Any]]) -> None:
    """Raise if RESEARCH response would ship without external sources."""
    if not sources:
        raise ValueError("B4.6 research requires ≥1 external source with URL")


def assert_action_kind_allowed(kind: str) -> None:
    if kind not in FIRST_ACTION_KINDS:
        raise ValueError(
            f"ACTION kind {kind!r} not in FIRST_ACTION_KINDS {FIRST_ACTION_KINDS}"
        )


def assert_context_engine(engine: str) -> None:
    if engine != CONTEXT_ENGINE_REQUIRED:
        raise ValueError(
            f"Vector must consume {CONTEXT_ENGINE_REQUIRED}, got {engine!r}"
        )


def location_from_path(path: str | None) -> CompanionLocation:
    """Map BCC pathname → companion location (pure; for B4.1+ wiring)."""
    p = (path or "").rstrip("/") or "/client"
    rules: tuple[tuple[str, CompanionLocation], ...] = (
        ("/client/analytics", "analytics"),
        ("/client/stats", "analytics"),
        ("/client/site", "website"),
        ("/client/website", "website"),
        ("/client/shop", "shop"),
        ("/client/products", "products"),
        ("/client/settings", "settings"),
        ("/client/support", "support"),
        ("/client/billing", "billing"),
        ("/client/bots", "other"),
        ("/store", "shop"),
        ("/website-admin", "website"),
    )
    for prefix, loc in rules:
        if p == prefix or p.startswith(prefix + "/"):
            return loc
    if p == "/client" or p.startswith("/client"):
        return "dashboard"
    return "other"
