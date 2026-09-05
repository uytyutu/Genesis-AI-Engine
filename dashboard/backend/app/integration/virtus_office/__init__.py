"""Virtus Office — micro-document job product (separate from B2B packages).

Public brand line: Virtus Office. Not AI Chat UX.
Pipeline LIVE only when OFFICE_PIPELINE_LIVE is True in office_job_ssot.
"""

from app.integration.virtus_office.job_engine import OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.language_catalog import catalog_public, list_office_languages
from app.integration.virtus_office.office_job_ssot import (
    OFFICE_JOB_STATUSES,
    OFFICE_PIPELINE_LIVE,
    OFFICE_PRICE_MATRIX_EUR,
    OFFICE_SELLABLE_NOW,
    OFFICE_SKU_ROADMAP,
    OFFICE_VITRINE_FORBIDDEN,
    STAGE1_SUCCESS_STATUS,
    STAGE2_SUCCESS_STATUS,
    empty_proposal_contract,
    empty_understanding_contract,
    office_pipeline_stages,
    office_reuse_map,
    office_stripe_live,
)

__all__ = [
    "OFFICE_JOB_STATUSES",
    "OFFICE_PIPELINE_LIVE",
    "OFFICE_PRICE_MATRIX_EUR",
    "OFFICE_SELLABLE_NOW",
    "OFFICE_SKU_ROADMAP",
    "OFFICE_VITRINE_FORBIDDEN",
    "STAGE1_SUCCESS_STATUS",
    "STAGE2_SUCCESS_STATUS",
    "OfficeJobEngine",
    "OfficeJobError",
    "catalog_public",
    "empty_proposal_contract",
    "empty_understanding_contract",
    "list_office_languages",
    "office_pipeline_stages",
    "office_reuse_map",
    "office_stripe_live",
]
