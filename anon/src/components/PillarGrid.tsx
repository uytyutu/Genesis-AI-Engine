"use client";

import Link from "next/link";
import { useI18n } from "./I18nProvider";

const ITEMS = [
  {
    href: "/create",
    emoji: "💌",
    titleKey: "product.moment",
    descKey: "product.moment.desc",
    accent: "from-violet-500/30 to-sky-500/10",
  },
  {
    href: "/anonymous",
    emoji: "🕵️",
    titleKey: "product.anon",
    descKey: "product.anon.desc",
    accent: "from-fuchsia-500/30 to-violet-500/10",
  },
  {
    href: "/open-when",
    emoji: "🔒",
    titleKey: "product.openLater",
    descKey: "product.openLater.desc",
    accent: "from-sky-500/30 to-pink-500/10",
  },
] as const;

export function PillarGrid() {
  const { t } = useI18n();
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {ITEMS.map((p, i) => (
        <Link
          key={p.href}
          href={p.href}
          className={`anon-card anim-in bg-gradient-to-br ${p.accent} p-5 transition hover:-translate-y-0.5 hover:border-white/20`}
          style={{ animationDelay: `${i * 80}ms` }}
        >
          <div className="mb-3 text-3xl" aria-hidden>
            {p.emoji}
          </div>
          <h2 className="text-lg font-bold tracking-wide">{t(p.titleKey)}</h2>
          <p className="mt-1 text-sm anon-muted">{t(p.descKey)}</p>
        </Link>
      ))}
    </div>
  );
}
