"""Catalog of Farm connectors by readiness tier (no premature automation)."""

from __future__ import annotations

from typing import Any

from .base import ConnectorStatus, Tier

# Static catalog for CEO panel — implementation status, not marketing.
CONNECTOR_CATALOG: list[dict[str, Any]] = [
    # --- Tier A ---
    {
        "id": "opire",
        "display_name": "Opire",
        "tier": Tier.A.value,
        "status": ConnectorStatus.LIVE.value,
        "official_docs_url": "https://docs.opire.dev",
        "notes_ru": "Живой коннектор. Официальный flow: /try → PR /claim → payout.",
    },
    {
        "id": "polar",
        "display_name": "Polar.sh",
        "tier": Tier.A.value,
        "status": ConnectorStatus.PLANNED.value,
        "official_docs_url": "https://polar.sh/docs",
        "notes_ru": "Tier A — следующий. Только официальный API / процесс Polar.",
    },
    {
        "id": "algora",
        "display_name": "Algora",
        "tier": Tier.A.value,
        "status": ConnectorStatus.PLANNED.value,
        "official_docs_url": "https://algora.io",
        "notes_ru": "Tier A — GitHub Issues с bounty. Коннектор после изучения API.",
    },
    {
        "id": "github_bounties",
        "display_name": "GitHub Bounties",
        "tier": Tier.A.value,
        "status": ConnectorStatus.PLANNED.value,
        "official_docs_url": "https://docs.github.com/en/issues",
        "notes_ru": "Issues/Labels «Bounty: $N» + Sponsors. Scanner без обхода ToS.",
    },
    # --- Tier B (bug bounty — separate module later) ---
    {
        "id": "hackerone",
        "display_name": "HackerOne",
        "tier": Tier.B.value,
        "status": ConnectorStatus.DISABLED.value,
        "official_docs_url": "https://docs.hackerone.com",
        "notes_ru": "Bug bounty — не смешивать с Tier A Execution Engine.",
    },
    {
        "id": "bugcrowd",
        "display_name": "Bugcrowd",
        "tier": Tier.B.value,
        "status": ConnectorStatus.DISABLED.value,
        "official_docs_url": "https://docs.bugcrowd.com",
        "notes_ru": "Отдельный security-модуль, не Farm OSS pipeline.",
    },
    {
        "id": "intigriti",
        "display_name": "Intigriti",
        "tier": Tier.B.value,
        "status": ConnectorStatus.DISABLED.value,
        "official_docs_url": "https://www.intigriti.com",
        "notes_ru": "Tier B — disabled до security module.",
    },
    {
        "id": "yeswehack",
        "display_name": "YesWeHack",
        "tier": Tier.B.value,
        "status": ConnectorStatus.DISABLED.value,
        "official_docs_url": "https://www.yeswehack.com",
        "notes_ru": "Tier B — disabled.",
    },
    {
        "id": "immunefi",
        "display_name": "Immunefi",
        "tier": Tier.B.value,
        "status": ConnectorStatus.DISABLED.value,
        "official_docs_url": "https://immunefi.com",
        "notes_ru": "Web3 security bug bounty — не Tier A.",
    },
    # --- Tier C (research) ---
    {
        "id": "gitcoin",
        "display_name": "Gitcoin",
        "tier": Tier.C.value,
        "status": ConnectorStatus.RESEARCH.value,
        "official_docs_url": "https://gitcoin.co",
        "notes_ru": "Исследование официального процесса — не реализовывать сейчас.",
    },
    {
        "id": "questbook",
        "display_name": "Questbook",
        "tier": Tier.C.value,
        "status": ConnectorStatus.RESEARCH.value,
        "official_docs_url": "https://questbook.app",
        "notes_ru": "Tier C research.",
    },
    {
        "id": "dework",
        "display_name": "Dework",
        "tier": Tier.C.value,
        "status": ConnectorStatus.RESEARCH.value,
        "official_docs_url": "https://dework.xyz",
        "notes_ru": "Tier C research.",
    },
]
