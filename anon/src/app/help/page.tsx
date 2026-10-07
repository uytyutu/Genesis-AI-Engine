"use client";

import { useI18n } from "@/components/I18nProvider";

export default function HelpPage() {
  const { t } = useI18n();
  return (
    <main className="anon-card anim-in space-y-4 p-6">
      <h1 className="text-2xl font-semibold">{t("help.title")}</h1>
      <p className="anon-muted">{t("help.body")}</p>
      <ul className="list-disc space-y-2 pl-5 text-sm">
        <li>{t("help.li1")}</li>
        <li>{t("help.li2")}</li>
        <li>{t("help.li3")}</li>
        <li>{t("help.li4")}</li>
        <li>{t("help.li5")}</li>
      </ul>
    </main>
  );
}
