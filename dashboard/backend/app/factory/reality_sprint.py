"""Reality Sprint — eye-test scorecards (no auto PASS).

Law: quality = would a German business owner want this site?
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REALITY_NICHES_10: tuple[str, ...] = (
    "handwerk",
    "dachreinigung",
    "restaurant",
    "psychology",
    "dental",
    "law",
    "beauty",
    "auto",
    "fitness",
    "realestate",
)

TEST_IDS: tuple[str, ...] = (
    "t1_five_second_niche",
    "t2_price_perception",
    "t3_german_company",
    "t4_portfolio",
    "t5_business_identity",
)


@dataclass
class RealityScorecard:
    """Filled by human eyes — Factory may prefill structure only."""

    niche_id: str
    product_id: str = ""
    company_name: str = ""
    preview_url: str = ""
    # TEST 1
    five_second_what: str = ""  # free: what does the company do?
    t1_pass: bool | None = None
    # TEST 2
    price_guess_eur: str = ""  # e.g. "300-700" | "1000-2000" | "studio"
    t2_pass: bool | None = None
    # TEST 3
    feels_real_german: bool | None = None
    t3_pass: bool | None = None
    # TEST 4
    portfolio_yes: bool | None = None
    t4_pass: bool | None = None
    # TEST 5
    character: str = ""
    price_position: str = ""  # cheap | mid | premium
    family_or_corporate: str = ""
    local_or_national: str = ""
    modern_or_dated: str = ""
    t5_pass: bool | None = None
    notes: str = ""
    overall: str = "PENDING_OWNER"  # PENDING_OWNER | PASS | FAIL | REBUILD

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def compute_overall(self) -> str:
        flags = [self.t1_pass, self.t2_pass, self.t3_pass, self.t4_pass, self.t5_pass]
        if any(f is None for f in flags):
            return "PENDING_OWNER"
        if all(flags):
            return "PASS"
        if self.t4_pass is False:
            return "REBUILD"
        return "FAIL"


def empty_scorecard(
    *,
    niche_id: str,
    product_id: str = "",
    company_name: str = "",
    preview_url: str = "",
) -> RealityScorecard:
    return RealityScorecard(
        niche_id=niche_id,
        product_id=product_id,
        company_name=company_name,
        preview_url=preview_url,
    )


def write_product_scorecard(product_dir: Path, card: RealityScorecard) -> Path:
    product_dir.mkdir(parents=True, exist_ok=True)
    path = product_dir / "REALITY_SCORECARD.md"
    path.write_text(
        f"""# Reality Scorecard — {card.company_name or card.niche_id}

**Status:** {card.overall}  
**Niche:** `{card.niche_id}` · product `{card.product_id}`  
**Preview:** {card.preview_url or "(open index.html — cover the logo)"}

Canon: `docs/canon/VIRTUS_CORE_REALITY_SPRINT.md`

---

## TEST 1 — 5-Second Niche
Cover the logo. Within 5 seconds: **What does this company do?**

- Observed: _{card.five_second_what or "…fill after looking"}_
- Pass: `{card.t1_pass}`

## TEST 2 — Price Perception
Show a stranger: **What would a studio charge?**

- Guess: `{card.price_guess_eur or "…"}`  
  - 300–700 € → FAIL · 1000–2000 € → good · «studio site» → PASS
- Pass: `{card.t2_pass}`

## TEST 3 — German Company Test
Does it feel like a real German firm (not a demo)?

- Feels real: `{card.feels_real_german}` · Pass: `{card.t3_pass}`

## TEST 4 — Portfolio Test
Would this go in the Virtus Core portfolio?

- Yes: `{card.portfolio_yes}` · Pass: `{card.t4_pass}`

## TEST 5 — Business Identity (no reading copy)
| Axis | Answer |
| --- | --- |
| Character | {card.character or "…"} |
| Cheap / mid / premium | {card.price_position or "…"} |
| Family / corporate | {card.family_or_corporate or "…"} |
| Local / national | {card.local_or_national or "…"} |
| Modern / dated | {card.modern_or_dated or "…"} |
| Pass | `{card.t5_pass}` |

## Notes
{card.notes or "—"}

---
*No internal JSON PASS overrides this card. Eyes only.*
""",
        encoding="utf-8",
    )
    (product_dir / "reality_scorecard.json").write_text(
        json.dumps(card.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def sprint_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pending = sum(1 for r in rows if r.get("overall") == "PENDING_OWNER")
    passed = sum(1 for r in rows if r.get("overall") == "PASS")
    failed = sum(1 for r in rows if r.get("overall") in ("FAIL", "REBUILD"))
    return {
        "sprint": "Reality Sprint — 10 Real Companies Test",
        "law": "Eyes over engines · Law №4 No Repeated Companies",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "pending_owner": pending,
        "pass": passed,
        "fail_or_rebuild": failed,
        "gate": (
            "≥8/10 PASS by owner eye to continue features; "
            "else stop and fix generation only"
        ),
        "one_question": (
            "Would a real German business owner say: "
            "Ja — genau so einen Auftritt will ich?"
        ),
        "rows": rows,
    }


__all__ = [
    "REALITY_NICHES_10",
    "TEST_IDS",
    "RealityScorecard",
    "empty_scorecard",
    "sprint_manifest",
    "write_product_scorecard",
]
