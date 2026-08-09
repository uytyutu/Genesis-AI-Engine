"""Virtus Core Website Auditor — shared report schema (public + in-platform).

Brand: Virtus Core Website Auditor (never generic "Website Auditor" alone).
"""

from __future__ import annotations

PRODUCT_NAME = "Virtus Core Website Auditor"
PRODUCT_ID = "vc_website_auditor"
PRODUCT_VERSION = "1.0.0-mvp"
ENGINE_ID = "vc_auditor_v1"

# Category ids for website technical scores (0–100 each)
WEBSITE_SCORE_KEYS = (
    "seo",
    "performance",
    "accessibility",
    "mobile",
    "security",
)

LEGAL_DE_KEYS = (
    "impressum",
    "datenschutz",
    "cookie",
    "kontakt",
)

BUSINESS_KEYS = (
    "cta",
    "forms",
    "maps",
    "social",
    "trust",
    "reviews",
)

EXPORT_FORMATS = ("json", "csv", "markdown", "pdf", "md")
