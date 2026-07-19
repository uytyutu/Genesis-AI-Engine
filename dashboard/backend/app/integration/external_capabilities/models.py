"""External free-tier API capabilities — catalog + runtime adapters.

Rules (Mission 1 Freeze):
- Disabled by default (env gate required).
- Always return a fallback Result — product never hard-depends on these APIs.
- Do not alter Groq → Gemini → OpenRouter → Ollama LLM chain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

MissionRequired = Literal["Mission1", "Mission2", "Optional", "Internal"]


@dataclass(frozen=True)
class ExternalCapabilityDef:
    id: str
    label: str
    provider: str
    purpose: str
    commercial_value: str
    mission_required: MissionRequired
    env_enable: str
    env_key: str | None = None
    requires_key: bool = False
    license_note: str = ""
    quota_hint: str = ""
    fallback_mode: str = "skip"
    product_surfaces: tuple[str, ...] = ()
    adapter: str = ""  # module hint


@dataclass(frozen=True)
class AdapterResult:
    ok: bool
    capability_id: str
    data: dict[str, Any] = field(default_factory=dict)
    used_fallback: bool = False
    source: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Canonical catalog — register potential APIs; only Mission1 adapters ship runtime.
EXTERNAL_CATALOG: tuple[ExternalCapabilityDef, ...] = (
    ExternalCapabilityDef(
        id="nominatim",
        label="OpenStreetMap Nominatim",
        provider="openstreetmap",
        purpose="Geocode address → OSM embed for Business landings",
        commercial_value="Maps on paid landings without Google API cost",
        mission_required="Mission1",
        env_enable="GENESIS_CAP_NOMINATIM",
        requires_key=False,
        license_note="ODbL — attribution required (© OpenStreetMap contributors)",
        quota_hint="~1 req/s; User-Agent mandatory",
        fallback_mode="google_maps_embed",
        product_surfaces=("factory_landing", "package_business"),
        adapter="nominatim",
    ),
    ExternalCapabilityDef(
        id="wikipedia",
        label="Wikipedia REST API",
        provider="wikipedia",
        purpose="Internal brief enrichment from public encyclopedia",
        commercial_value="Richer Path A analysis without inventing niche facts",
        mission_required="Mission1",
        env_enable="GENESIS_CAP_WIKIPEDIA",
        requires_key=False,
        license_note="CC BY-SA — always show source URL; not final truth",
        quota_hint="Fair use; cache results",
        fallback_mode="skip_enrichment",
        product_surfaces=("order_insights", "analysis_brief"),
        adapter="wikipedia",
    ),
    ExternalCapabilityDef(
        id="wikidata",
        label="Wikidata",
        provider="wikidata",
        purpose="Structured entity hints for niche/city enrichment",
        commercial_value="Structured context for analysis briefs",
        mission_required="Mission1",
        env_enable="GENESIS_CAP_WIKIDATA",
        requires_key=False,
        license_note="CC0 data — cite Wikidata; not final truth",
        quota_hint="Fair use; cache results",
        fallback_mode="skip_enrichment",
        product_surfaces=("order_insights", "analysis_brief"),
        adapter="wikidata",
    ),
    ExternalCapabilityDef(
        id="telegram_bot",
        label="Telegram Bot API",
        provider="telegram",
        purpose="CEO / order notifications via bot",
        commercial_value="Faster owner response after paid events",
        mission_required="Optional",
        env_enable="GENESIS_CAP_TELEGRAM",
        env_key="GENESIS_TELEGRAM_BOT_TOKEN",
        requires_key=True,
        license_note="Telegram Bot API ToS",
        quota_hint="Bot API limits",
        fallback_mode="local_notifications",
        product_surfaces=("owner_notify",),
        adapter="",
    ),
    ExternalCapabilityDef(
        id="qrserver",
        label="QRServer",
        provider="qrserver",
        purpose="QR code image for order status / visiting card",
        commercial_value="Low-friction share of order status URL",
        mission_required="Optional",
        env_enable="GENESIS_CAP_QRSERVER",
        requires_key=False,
        license_note="goqr.me public API — check ToS for production volume",
        quota_hint="Public free endpoint",
        fallback_mode="plain_url",
        product_surfaces=("order_status",),
        adapter="",
    ),
    ExternalCapabilityDef(
        id="hibp",
        label="Have I Been Pwned",
        provider="haveibeenpwned",
        purpose="Email breach trust signal at checkout",
        commercial_value="Trust / security signal for real buyers",
        mission_required="Optional",
        env_enable="GENESIS_CAP_HIBP",
        env_key="GENESIS_HIBP_API_KEY",
        requires_key=True,
        license_note="HIBP API license — key required for production",
        quota_hint="Paid tiers for volume; free limited",
        fallback_mode="skip",
        product_surfaces=("checkout",),
        adapter="",
    ),
    ExternalCapabilityDef(
        id="virustotal",
        label="VirusTotal Public API",
        provider="virustotal",
        purpose="Optional URL reputation in site analysis",
        commercial_value="Safer analysis of client websites",
        mission_required="Optional",
        env_enable="GENESIS_CAP_VIRUSTOTAL",
        env_key="GENESIS_VIRUSTOTAL_API_KEY",
        requires_key=True,
        license_note="VT public API ToS — not for mandatory UX path",
        quota_hint="Strict public rate limits",
        fallback_mode="skip",
        product_surfaces=("site_analysis",),
        adapter="",
    ),
    ExternalCapabilityDef(
        id="huggingface",
        label="Hugging Face Inference",
        provider="huggingface",
        purpose="Optional embeddings / niche helpers",
        commercial_value="Unproven vs existing Groq/Gemini/OR chain — not Mission1",
        mission_required="Optional",
        env_enable="GENESIS_CAP_HUGGINGFACE",
        env_key="GENESIS_HF_TOKEN",
        requires_key=True,
        license_note="Model-specific licenses",
        quota_hint="Free tier rate limits",
        fallback_mode="llm_chain",
        product_surfaces=(),
        adapter="",
    ),
    ExternalCapabilityDef(
        id="open_meteo",
        label="Open-Meteo",
        provider="open-meteo",
        purpose="Weather widget for local-service landings",
        commercial_value="Nice-to-have; does not move first payment",
        mission_required="Optional",
        env_enable="GENESIS_CAP_OPEN_METEO",
        requires_key=False,
        license_note="Open-Meteo free non-commercial / attribution",
        quota_hint="Generous free tier",
        fallback_mode="omit_widget",
        product_surfaces=("factory_landing",),
        adapter="",
    ),
)
