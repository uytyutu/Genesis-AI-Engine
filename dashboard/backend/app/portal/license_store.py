"""Commercial Platform 6.5 — LicenseStore."""

from __future__ import annotations

from typing import Protocol

from app.portal.license import License

ENGINE_ID = "license_store_v1"


class LicenseStore(Protocol):
    def save(self, license: License) -> None: ...

    def get(self, license_id: str) -> License | None: ...

    def list_for_account(self, account_id: str) -> tuple[License, ...]: ...


class InMemoryLicenseStore:
    def __init__(self) -> None:
        self._rows: dict[str, License] = {}

    def save(self, license: License) -> None:
        self._rows[license.license_id] = license

    def get(self, license_id: str) -> License | None:
        return self._rows.get(license_id)

    def list_for_account(self, account_id: str) -> tuple[License, ...]:
        return tuple(
            row for row in self._rows.values() if row.account_id == account_id
        )
