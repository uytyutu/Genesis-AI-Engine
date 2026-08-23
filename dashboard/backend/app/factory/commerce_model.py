"""Virtus Core commerce model — Standalone vs Connected.

Client-facing: two purchase modes (not Basic / Business / Premium).
Legacy package_id values remain accepted and normalize here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

CommerceMode = Literal["standalone", "connected"]

# Public catalog prices (EUR)
STANDALONE_PRICE_EUR = 499
CONNECTED_SETUP_EUR = 499
CONNECTED_MONTHLY_EUR = 99

# Legacy ladder kept for API / unpaid orders / demos
LEGACY_ALIAS: dict[str, CommerceMode] = {
    "basic": "standalone",
    "business": "standalone",
    "standalone": "standalone",
    "premium": "connected",
    "connected": "connected",
}

# Factory feature tier: both modes get full digital-company quality.
# Connected adds ecosystem flags only.
FACTORY_PACKAGE_FOR_MODE: dict[CommerceMode, str] = {
    "standalone": "standalone",
    "connected": "connected",
}


@dataclass(frozen=True)
class CommerceResolution:
    commerce_mode: CommerceMode
    package_id: str  # canonical: standalone | connected
    factory_package_id: str  # passed into PackageFeatures
    legacy_alias: str  # original input if legacy
    price_eur: int
    monthly_eur: int
    label: str
    promise: str
    ecosystem: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_commerce_mode(
    package_id: str | None = None,
    *,
    commerce_mode: str | None = None,
) -> CommerceResolution:
    """Resolve Standalone / Connected from package_id and/or explicit mode."""
    raw_mode = (commerce_mode or "").strip().lower()
    raw_pkg = (package_id or "").strip().lower()

    if raw_mode in ("standalone", "connected"):
        mode: CommerceMode = raw_mode  # type: ignore[assignment]
        legacy = raw_pkg or raw_mode
    elif raw_pkg in LEGACY_ALIAS:
        mode = LEGACY_ALIAS[raw_pkg]
        legacy = raw_pkg
    else:
        mode = "standalone"
        legacy = raw_pkg or "standalone"

    if mode == "connected":
        return CommerceResolution(
            commerce_mode="connected",
            package_id="connected",
            factory_package_id="connected",
            legacy_alias=legacy,
            price_eur=CONNECTED_SETUP_EUR,
            monthly_eur=CONNECTED_MONTHLY_EUR,
            label="Virtus Core Connected",
            promise=(
                "Ready digital product connected to the Virtus Core ecosystem — "
                "CRM, AI, automation, analytics, Workspace."
            ),
            ecosystem=True,
        )
    return CommerceResolution(
        commerce_mode="standalone",
        package_id="standalone",
        factory_package_id="standalone",
        legacy_alias=legacy,
        price_eur=STANDALONE_PRICE_EUR,
        monthly_eur=0,
        label="Standalone",
        promise=(
            "Ready digital product you fully own — site or store, panel, "
            "source, instructions. No subscription required."
        ),
        ecosystem=False,
    )


def is_connected(package_id: str | None = None, *, commerce_mode: str | None = None) -> bool:
    return normalize_commerce_mode(package_id, commerce_mode=commerce_mode).ecosystem


def public_commerce_packages() -> list[dict[str, Any]]:
    """Catalog rows for API / storefront (two modes only)."""
    out: list[dict[str, Any]] = []
    for mode in ("standalone", "connected"):
        r = normalize_commerce_mode(mode)
        out.append(
            {
                "id": r.package_id,
                "commerce_mode": r.commerce_mode,
                "name": r.label,
                "price_eur": r.price_eur,
                "monthly_eur": r.monthly_eur,
                "tagline": r.promise,
                "ecosystem": r.ecosystem,
                "billing": "monthly" if r.monthly_eur else "one_time",
                # Back-compat keys used by older UI
                "legacy_maps_from": [
                    k for k, v in LEGACY_ALIAS.items() if v == mode and k not in ("standalone", "connected")
                ],
            }
        )
    return out


__all__ = [
    "CONNECTED_MONTHLY_EUR",
    "CONNECTED_SETUP_EUR",
    "CommerceMode",
    "CommerceResolution",
    "FACTORY_PACKAGE_FOR_MODE",
    "LEGACY_ALIAS",
    "STANDALONE_PRICE_EUR",
    "is_connected",
    "normalize_commerce_mode",
    "public_commerce_packages",
]
