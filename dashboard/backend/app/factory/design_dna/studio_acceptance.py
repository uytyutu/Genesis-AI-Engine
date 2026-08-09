"""Studio Acceptance — impression gate. Not HTML. Not CSS. Not DNA PASS.

Proof is only what a human opens. Agent may record FAIL / PARTIAL / PENDING_OWNER.
Never auto-write PASS. Owner phrase unlocks acceptance.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["PASS", "FAIL", "PARTIAL", "PENDING_OWNER"]

OWNER_PASS_PHRASE = "Да, я бы без стыда продал этот сайт клиенту"
# Alias accepted as owner sell-readiness (Virtus Core 2026+)
OWNER_PASS_PHRASES: tuple[str, ...] = (
    OWNER_PASS_PHRASE,
    "Да. Я готов продать этот сайт своему клиенту.",
    "Да, я готов продать этот сайт своему клиенту.",
)

CHECKS: tuple[tuple[str, str], ...] = (
    ("hero", "Hero creates the impression of an expensive product?"),
    ("composition", "Does it feel like a template / section stack?"),
    ("atmosphere", "Is there life (air, depth, motion) — not flat wallpaper?"),
    ("white_space", "No ladder of empty/white sections?"),
    ("store", "Does the store read as modern brand e-commerce?"),
    ("premium_studio_test", "Logo off — still a costly European digital studio?"),
    (
        "template_like",
        "Would a stranger say 'constructor template'? If yes → FAIL/REBUILD",
    ),
)

DEMO_KEYS: tuple[tuple[str, str], ...] = (
    ("starter_site", "sites/basic/psychology/index.html"),
    ("business_site", "sites/business/psychology/index.html"),
    ("premium_site", "sites/premium/psychology/index.html"),
    ("starter_store", "stores/basic/psychology/index.html"),
    ("business_store", "stores/business/psychology/index.html"),
    ("premium_store", "stores/premium/psychology/index.html"),
)


@dataclass
class StudioCheck:
    id: str
    question: str
    verdict: Verdict = "PENDING_OWNER"
    note: str = ""


@dataclass
class StudioAcceptanceReport:
    gate: str = "studio_acceptance"
    status: Verdict = "PENDING_OWNER"
    rule: str = "No internal PASS. Only owner sell-without-shame counts."
    optimize_for: str = "first visual effect — not internal metrics"
    quality_floors: dict[str, str] = field(
        default_factory=lambda: {
            "starter": "not below modern small business",
            "business": "not worse than Virtus Core /site",
            "premium": "ABOVE Virtus Core — expensive European digital studio",
        }
    )
    checks: list[StudioCheck] = field(default_factory=list)
    demos: dict[str, str] = field(default_factory=dict)
    base_url: str = "http://127.0.0.1:3001"
    owner_required: str = OWNER_PASS_PHRASE
    agent_may_not_pass: bool = True
    updated_at: str = ""
    freeze: str = "No new niches / Directors until Premium Psychology site+store sell without shame"

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def default_demo_urls(base_url: str = "http://127.0.0.1:3001") -> dict[str, str]:
    root = base_url.rstrip("/")
    return {
        key: f"{root}/package-previews/{rel}"
        for key, rel in DEMO_KEYS
    }


def build_pending_report(
    *,
    base_url: str = "http://127.0.0.1:3001",
    agent_notes: dict[str, tuple[Verdict, str]] | None = None,
) -> StudioAcceptanceReport:
    """Always PENDING_OWNER unless owner has spoken (never in this helper)."""
    notes = agent_notes or {}
    checks: list[StudioCheck] = []
    for cid, question in CHECKS:
        verdict, note = notes.get(cid, ("PENDING_OWNER", ""))
        # Agent must not mint PASS through this builder.
        if verdict == "PASS":
            verdict = "PENDING_OWNER"
            note = (note + " — agent cannot PASS; awaiting owner").strip(" —")
        checks.append(StudioCheck(id=cid, question=question, verdict=verdict, note=note))
    return StudioAcceptanceReport(
        status="PENDING_OWNER",
        checks=checks,
        demos=default_demo_urls(base_url),
        base_url=base_url.rstrip("/"),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


def write_studio_acceptance(
    dest: Path,
    *,
    base_url: str = "http://127.0.0.1:3001",
    agent_notes: dict[str, tuple[Verdict, str]] | None = None,
) -> Path:
    report = build_pending_report(base_url=base_url, agent_notes=agent_notes)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return dest


def print_demo_links(base_url: str = "http://127.0.0.1:3001") -> list[str]:
    urls = default_demo_urls(base_url)
    order = (
        "starter_site",
        "business_site",
        "premium_site",
        "starter_store",
        "business_store",
        "premium_store",
    )
    labels = {
        "starter_site": "Starter Psychology",
        "business_site": "Business Psychology",
        "premium_site": "Premium Psychology",
        "starter_store": "Starter Store",
        "business_store": "Business Store",
        "premium_store": "Premium Store",
    }
    lines: list[str] = []
    for key in order:
        line = f"{labels[key]}: {urls[key]}"
        lines.append(line)
        print(line)
    return lines
