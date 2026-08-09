"use client";

import { useTranslation } from "react-i18next";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { CookiePreferencesPanel } from "../../components/CookiePreferencesPanel";

export default function ClientPrivacyPage() {
  const { t } = useTranslation("site");
  return (
    <ClientWorkspaceShell
      title={t("cookies.cabinetTitle", {
        defaultValue: "Privacy & Cookies",
      })}
      subtitle={t("cookies.cabinetSubtitle", {
        defaultValue:
          "Manage cookie consent in your cabinet — not only from the footer.",
      })}
    >
      <CookiePreferencesPanel />
    </ClientWorkspaceShell>
  );
}
