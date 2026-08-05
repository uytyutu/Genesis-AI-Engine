"use client";

import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import {
  HUB_AGENCY_SERVICE_IDS,
  SERVICE_SPECS,
  getServiceSpec,
} from "../../lib/serviceOrderSpecs";

export default function ClientShopPage() {
  const agency = HUB_AGENCY_SERVICE_IDS.map((id) => getServiceSpec(id)!).filter(
    Boolean,
  );
  const core = SERVICE_SPECS.filter((s) =>
    ["landing_website", "ai_business_bot"].includes(s.id),
  );

  return (
    <ClientWorkspaceShell
      title="Магазин услуг"
      subtitle="Website Services и сайты — заказ через форму, результат в кабинете."
    >
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-200/80">
        Core
      </p>
      <ul className="mb-8 grid gap-3 sm:grid-cols-2">
        {core.map((c) => (
          <li
            key={c.id}
            className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-lg font-semibold text-white">{c.name}</p>
              <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-emerald-200">
                Live
              </span>
            </div>
            <p className="mt-1 text-sm font-medium text-emerald-200/90">
              {c.price_label}
            </p>
            <p className="mt-2 flex-1 text-sm text-zinc-400">{c.blurb}</p>
            <Link
              href={c.href}
              className="mt-4 inline-flex rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-black"
            >
              Заказать
            </Link>
          </li>
        ))}
      </ul>
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-200/80">
        Website Services
      </p>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {agency.map((c) => (
          <li
            key={c.id}
            className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
          >
            <p className="text-base font-semibold text-white">{c.name}</p>
            <p className="mt-1 text-sm font-medium text-emerald-200/90">
              {c.price_label}
            </p>
            <p className="mt-2 text-xs text-zinc-500">{c.timeline}</p>
            <ul className="mt-2 space-y-1 text-xs text-zinc-400">
              {c.includes.slice(0, 4).map((line) => (
                <li key={line}>✓ {line}</li>
              ))}
            </ul>
            <Link
              href={`${c.href}${c.href.includes("?") ? "&" : "?"}form=1`}
              className="mt-4 inline-flex rounded-xl border border-emerald-400/40 px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-950/40"
            >
              Заказать →
            </Link>
          </li>
        ))}
      </ul>
    </ClientWorkspaceShell>
  );
}
