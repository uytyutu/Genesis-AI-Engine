"""Overlay Gewerbe / legal operator fields from environment when JSON is incomplete."""

from __future__ import annotations

import os

from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.legal.entity_schema import LegalEntityConfig

_PUBLIC_CONTACT_EMAIL = "hello@genesis-ai-engine.com"

# First env key wins per attribute; only fills empty JSON fields.
_OPERATOR_ENV_KEYS: tuple[tuple[str, ...], str] = (
    (("GENESIS_LEGAL_OPERATOR_NAME", "NEXT_PUBLIC_LEGAL_NAME"), "full_name"),
    (("GENESIS_LEGAL_LEGAL_FORM",), "legal_form"),
    (("GENESIS_LEGAL_TRADE_NAME",), "trade_name"),
    (("GENESIS_LEGAL_ADDRESS_STREET",), "address_street"),
    (("GENESIS_LEGAL_ADDRESS_ZIP",), "address_zip"),
    (("GENESIS_LEGAL_ADDRESS_CITY",), "address_city"),
    (("GENESIS_LEGAL_EMAIL",), "email"),
    (("GENESIS_LEGAL_PHONE", "NEXT_PUBLIC_LEGAL_PHONE"), "phone"),
    (("GENESIS_PUBLIC_URL", "NEXT_PUBLIC_SITE_URL"), "website"),
    (("GENESIS_LEGAL_VAT_ID", "NEXT_PUBLIC_LEGAL_VAT_ID"), "vat_id"),
    (("GENESIS_LEGAL_MANAGING_DIRECTOR",), "managing_director"),
    (("GENESIS_LEGAL_HANDELSREGISTER",), "handelsregister"),
    (("GENESIS_LEGAL_REGISTER_COURT",), "register_court"),
)


def apply_env_overlay(cfg: LegalEntityConfig) -> LegalEntityConfig:
    op = cfg.operator

    for env_keys, attr in _OPERATOR_ENV_KEYS:
        if str(getattr(op, attr)).strip():
            continue
        for key in env_keys:
            val = os.getenv(key, "").strip()
            if val:
                setattr(op, attr, val)
                break

    if not op.address_street.strip():
        combined = os.getenv("NEXT_PUBLIC_LEGAL_ADDRESS", "").strip()
        if combined:
            op.address_street = combined

    if not op.trade_name.strip():
        op.trade_name = BRAND_NAME

    if not op.email.strip():
        op.email = _PUBLIC_CONTACT_EMAIL

    if cfg.is_impressum_publishable():
        cfg.interview_completed = True

    return cfg
