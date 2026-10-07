"use client";

import Link from "next/link";
import { useI18n } from "@/components/I18nProvider";

export default function AnonymousPage() {
  const { t } = useI18n();
  return (
    <main className="anim-in">
      <section className="anon-card overflow-hidden p-6 sm:p-10">
        <p className="text-xs tracking-[0.35em] text-fuchsia-300">🕵️ ANON</p>
        <h1 className="mt-4 text-3xl font-semibold leading-tight sm:text-4xl">
          {t("anon.hero")}
        </h1>
        <p className="mt-4 max-w-lg anon-muted">{t("anon.privacy")}</p>
        <div className="mt-8 rounded-2xl border border-white/10 bg-black/30 p-5">
          <p className="text-sm anon-muted">{t("anon.demoLeft")}</p>
          <p className="mt-2 text-sm">
            {t("anon.demoFrom")} <strong>ANON #81724</strong>
          </p>
          <p className="mt-4 italic">«…»</p>
          <div className="mt-5">
            <span className="anon-btn anon-btn-primary pointer-events-none">
              {t("cta.open").toUpperCase()}
            </span>
          </div>
        </div>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link href="/create?pillar=anon" className="anon-btn anon-btn-primary">
            {t("anon.send")}
          </Link>
          <Link href="/play?lane=anon" className="anon-btn anon-btn-ghost">
            🎮 {t("cta.playStrangers")}
          </Link>
        </div>
      </section>
    </main>
  );
}
