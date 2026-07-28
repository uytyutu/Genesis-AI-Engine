"use client";

import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { CookiePreferencesPanel } from "../../components/CookiePreferencesPanel";

export default function ClientPrivacyPage() {
  return (
    <ClientWorkspaceShell
      title="Privacy & Cookies"
      subtitle="Управляйте согласием на cookies в личном кабинете — не только из футера."
    >
      <CookiePreferencesPanel />
    </ClientWorkspaceShell>
  );
}
