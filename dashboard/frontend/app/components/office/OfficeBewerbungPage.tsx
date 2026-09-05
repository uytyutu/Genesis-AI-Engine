"use client";

import { VirtusBewerbungStorefront } from "../storefront/VirtusBewerbungStorefront";
import { OfficeShell } from "./OfficeShell";

export function OfficeBewerbungPage() {
  return (
    <OfficeShell active="bewerbung">
      <VirtusBewerbungStorefront embedded />
    </OfficeShell>
  );
}
