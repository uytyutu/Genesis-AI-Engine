"use client";

import Link from "next/link";
import { AnonSpeak } from "@/components/AnonSpeak";
import { useI18n } from "@/components/I18nProvider";
import { THEME_TOKENS, type ThemeId } from "@/lib/themes";

const CATEGORIES: {
  href: string;
  titleKey: string;
  descKey: string;
  emoji: string;
  theme: ThemeId;
  live: boolean;
}[] = [
  {
    href: "/drop",
    titleKey: "moments.cat.drop",
    descKey: "moments.cat.drop.desc",
    emoji: "🔥",
    theme: "fire",
    live: true,
  },
  {
    href: "/create",
    titleKey: "moments.cat.create",
    descKey: "moments.cat.create.desc",
    emoji: "💌",
    theme: "dream",
    live: true,
  },
  {
    href: "/anonymous",
    titleKey: "moments.cat.anon",
    descKey: "moments.cat.anon.desc",
    emoji: "🕵️",
    theme: "secret",
    live: true,
  },
  {
    href: "/open-when",
    titleKey: "moments.cat.later",
    descKey: "moments.cat.later.desc",
    emoji: "🔒",
    theme: "night",
    live: true,
  },
  {
    href: "/create?pillar=send&sku=SEND_SURPRISE",
    titleKey: "moments.cat.surprise",
    descKey: "moments.cat.surprise.desc",
    emoji: "🎁",
    theme: "party",
    live: true,
  },
  {
    href: "/create?pillar=open_when&sku=SEND_TIME_CAPSULE",
    titleKey: "moments.cat.capsule",
    descKey: "moments.cat.capsule.desc",
    emoji: "🧊",
    theme: "ocean",
    live: true,
  },
];

export default function MomentsPage() {
  const { t } = useI18n();

  return (
    <main className="anim-in space-y-6">
      <section className="text-center">
        <p className="text-xs tracking-[0.35em] text-violet-300">ANON</p>
        <h1 className="mt-3 text-3xl font-semibold sm:text-4xl">💜 {t("moments.hubTitle")}</h1>
        <p className="mx-auto mt-3 max-w-md text-sm anon-muted">{t("moments.hubSub")}</p>
      </section>
      <section className="anon-card p-4">
        <AnonSpeak lineKey="veil.moment" mood="happy" accent="moment" size={68} />
      </section>

      <Link
        href="/drop"
        className="block overflow-hidden rounded-3xl border border-fuchsia-300/25 bg-gradient-to-br from-[#4a2860] via-[#3a1848] to-[#1a1230] p-6 transition hover:-translate-y-0.5"
      >
        <p className="text-xs tracking-[0.3em] text-rose-200">TRENDING</p>
        <h2 className="mt-2 text-2xl font-semibold">🔥 {t("drop.createTitle")}</h2>
        <p className="mt-2 max-w-md text-sm text-white/70">{t("drop.createSub")}</p>
        <span className="anon-btn anon-btn-primary mt-4 inline-flex">{t("drop.createCta")}</span>
      </Link>

      <div className="grid gap-3 sm:grid-cols-2">
        {CATEGORIES.map((c) => {
          const th = THEME_TOKENS[c.theme];
          return (
            <Link
              key={c.href + c.titleKey}
              href={c.href}
              className={`rounded-3xl border border-white/10 bg-gradient-to-br p-5 transition hover:-translate-y-0.5 hover:border-white/25 ${th.gradient}`}
            >
              <div className="text-3xl">{c.emoji}</div>
              <h3 className="mt-3 text-lg font-bold">{t(c.titleKey)}</h3>
              <p className="mt-1 text-sm text-white/70">{t(c.descKey)}</p>
            </Link>
          );
        })}
      </div>

      <section className="anon-card p-5 text-center">
        <p className="text-sm anon-muted">{t("moments.afterGame")}</p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:justify-center">
          <Link href="/games" className="anon-btn anon-btn-ghost">
            🎮 {t("nav.games")}
          </Link>
          <Link href="/inbox" className="anon-btn anon-btn-ghost">
            💬 {t("nav.messages")}
          </Link>
        </div>
      </section>
    </main>
  );
}
