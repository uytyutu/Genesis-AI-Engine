"""Bootstrap Hero Pack 2.0 directories from niche preview.jpg, then report gaps."""

from __future__ import annotations

from app.factory.hero_pack import (
    BASIC_SLOTS,
    BUSINESS_SLOTS,
    PREMIUM_SLOTS,
    seed_pack_from_preview,
    slot_path,
)
from app.factory.niche_profiles import known_niche_ids


def main() -> None:
    for niche in known_niche_ids():
        n = seed_pack_from_preview(niche)
        print(f"seeded {niche}: {n} new files")
    print("--- missing unique check (all exist after seed) ---")
    for niche in known_niche_ids():
        for tier, slots in (
            ("basic", BASIC_SLOTS),
            ("business", BUSINESS_SLOTS),
            ("premium", PREMIUM_SLOTS),
        ):
            for slot in slots:
                p = slot_path(niche, tier, slot)
                assert p.is_file(), p
    print("OK all niches have full pack slots (may still share preview bytes until gen)")


if __name__ == "__main__":
    main()
