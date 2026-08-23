"use client";

import Link from "next/link";
import { ClientWorkspaceShell } from "./ClientWorkspaceShell";
import { ASSISTANT_NAME } from "../lib/publicBrand";

type Props = {
  title: string;
  subtitle?: string;
  why?: string;
  virtusHint?: string;
  primaryHref?: string;
  primaryLabel?: string;
  comingSoon?: boolean;
};

/** Honest stub section — no fake CMS. Edit path = Virtus AI. */
export function WorkspaceSectionStub({
  title,
  subtitle,
  why,
  virtusHint,
  primaryHref = "/client",
  primaryLabel = "К Dashboard",
  comingSoon = true,
}: Props) {
  return (
    <ClientWorkspaceShell title={title} subtitle={subtitle}>
      <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 sm:p-8">
        {comingSoon ? (
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-300/80">
            Coming Soon · Bearbeitung über {ASSISTANT_NAME} / Admin
          </p>
        ) : null}
        <h2 className="mt-3 text-xl font-semibold text-white">{title}</h2>
        {why ? <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">{why}</p> : null}
        {virtusHint ? (
          <p className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3 text-sm text-emerald-100/90">
            {virtusHint}
          </p>
        ) : (
          <p className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3 text-sm text-emerald-100/90">
            Скажите {ASSISTANT_NAME}: что изменить в проекте — получите план и
            предпросмотр. Полный визуальный редактор страниц подключается поэтапно;
            сейчас центр управления — чат и чек-лист запуска.
          </p>
        )}
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href={primaryHref}
            className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
          >
            {primaryLabel}
          </Link>
          <Link
            href="/client/shop"
            className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          >
            Marketplace
          </Link>
        </div>
      </div>
    </ClientWorkspaceShell>
  );
}
