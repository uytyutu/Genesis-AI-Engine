"use client";

import Link from "next/link";
import {
  HUB_MORE_SERVICE_IDS,
  HUB_PRIMARY_SERVICE_IDS,
  SERVICE_SPECS,
  type ServiceSpec,
} from "../lib/serviceOrderSpecs";
import { BotChannelIconRow } from "./ChannelBrandIcons";

function ServiceCard({
  spec,
  featured,
}: {
  spec: ServiceSpec;
  featured?: boolean;
}) {
  const live = spec.availability === "available";
  const inner = (
    <>
      <div className="flex items-start justify-between gap-3">
        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border text-sm font-bold text-white ${spec.accent}`}
          aria-hidden
        >
          {spec.mark}
        </span>
        <span
          className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
            live
              ? "bg-emerald-500/15 text-emerald-200"
              : "bg-white/5 text-zinc-400"
          }`}
        >
          {live ? "Order" : "Soon"}
        </span>
      </div>
      <h3 className="mt-4 text-lg font-semibold text-white">{spec.name}</h3>
      <p className="mt-1 text-sm font-medium text-emerald-200/90">{spec.price_label}</p>
      <p className="mt-2 text-sm text-zinc-400">{spec.blurb}</p>
      {spec.id === "ai_business_bot" ? (
        <div className="mt-3">
          <BotChannelIconRow />
        </div>
      ) : null}
      <ul className="mt-3 space-y-1 text-xs text-zinc-400">
        {spec.includes.slice(0, 3).map((line) => (
          <li key={line} className="flex gap-2">
            <span className="text-emerald-400/80" aria-hidden>
              ✓
            </span>
            <span>{line}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[11px] text-zinc-500">
        {spec.stages.length} stages · {spec.timeline}
      </p>
      <p className="mt-1 text-[11px] text-zinc-500">Support: {spec.support}</p>
      <span
        className={`mt-4 inline-flex text-sm font-semibold ${
          live ? "text-emerald-300" : "text-zinc-500"
        }`}
      >
        {live ? "Open order form →" : "Interest form →"}
      </span>
    </>
  );

  const className = `block h-full rounded-2xl border p-5 text-left transition ${
    featured
      ? "border-emerald-400/30 bg-emerald-500/[0.06] hover:border-emerald-300/45"
      : live
        ? "border-white/12 bg-white/[0.03] hover:border-white/25 hover:bg-white/[0.05]"
        : "border-white/8 bg-white/[0.02] opacity-90"
  }`;

  return (
    <Link href={spec.href} className={className}>
      {inner}
      {!live ? (
        <p className="mt-2 text-xs text-zinc-500">{spec.deliveryNote}</p>
      ) : null}
    </Link>
  );
}

export function ServiceCatalogGrid({
  mode = "hub",
}: {
  mode?: "hub" | "all";
}) {
  const primary = HUB_PRIMARY_SERVICE_IDS.map(
    (id) => SERVICE_SPECS.find((s) => s.id === id)!,
  ).filter(Boolean);
  const more = HUB_MORE_SERVICE_IDS.map(
    (id) => SERVICE_SPECS.find((s) => s.id === id)!,
  ).filter(Boolean);

  if (mode === "all") {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {SERVICE_SPECS.map((spec) => (
          <ServiceCard
            key={spec.id}
            spec={spec}
            featured={
              spec.id === "landing_website" || spec.id === "ai_business_bot"
            }
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {primary.map((spec) => (
          <ServiceCard
            key={spec.id}
            spec={spec}
            featured={spec.id === "landing_website"}
          />
        ))}
      </div>
      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
          More website services
        </p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {more.map((spec) => (
            <ServiceCard key={spec.id} spec={spec} />
          ))}
        </div>
      </div>
    </div>
  );
}
