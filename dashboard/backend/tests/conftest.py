"""Backend pytest defaults for Virtus Office unit tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _office_unit_translate_offline_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Allow offline_glossary only for ordinary unit tests (not live E2E).

    Commercial / OWNER E2E must set OFFICE_E2E_LIVE=1 and load_local_env so
    Groq/Resend run for real — offline_glossary is forbidden there.
    """
    if os.getenv("OFFICE_E2E_LIVE", "").strip().lower() in {"1", "true", "yes"}:
        monkeypatch.delenv("OFFICE_ALLOW_OFFLINE_TRANSLATE", raising=False)
        return
    monkeypatch.setenv("OFFICE_ALLOW_OFFLINE_TRANSLATE", "1")
