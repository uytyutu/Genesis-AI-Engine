"use client";

import { useTranslation } from "react-i18next";
import {
  HUB_MORE_SERVICE_IDS,
  HUB_PRIMARY_SERVICE_IDS,
  SERVICE_SPECS,
  type ServiceSpec,
} from "../lib/serviceOrderSpecs";
import { BotChannelIconRow } from "./ChannelBrandIcons";

function useLocalizedSpec(spec: ServiceSpec) {
  const { t } = useTranslation("site");
  const k = `catalog.${spec.id}`;
  const includes = t(`${k}.includes`, {
    returnObjects: true,
    defaultValue: spec.includes,
  });
  const highlightsRaw = t(`${k}.highlights`, {
    returnObjects: true,
    defaultValue: spec.highlights || [],
  });
  return {
    name: t(`${k}.name`, { defaultValue: spec.name }),
    price_label: t(`${k}.price`, { defaultValue: spec.price_label }),
    blurb: t(`${k}.blurb`, { defaultValue: spec.blurb }),
    includes: Array.isArray(includes) ? (includes as string[]) : spec.includes,
    highlights: Array.isArray(highlightsRaw)
      ? (highlightsRaw as string[])
      : spec.highlights || [],
    timeline: t(`${k}.timeline`, { defaultValue: spec.timeline }),
    support: t(`${k}.support`, { defaultValue: spec.support }),
    deliveryNote: t(`${k}.deliveryNote`, {
      defaultValue: spec.deliveryNote,
    }),
    stagesCount: spec.stages.length,
  };
}

function ServiceCard({
  spec,
  featured,
  onOpenLocal,
}: {
  spec: ServiceSpec;
  featured?: boolean;
  onOpenLocal?: (id: string) => void;
}) {
  const { t } = useTranslation("site");
  const copy = useLocalizedSpec(spec);
  const live = spec.availability === "available";
  const localOnly = spec.id === "website_check" && typeof onOpenLocal === "function";

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
          {live
            ? t("catalog.badgeOrder", { defaultValue: "Order" })
            : t("catalog.badgeSoon", { defaultValue: "Soon" })}
        </span>
      </div>
      <h3 className="mt-4 text-lg font-semibold leading-snug text-white">
        {copy.name}
      </h3>
      <p className="mt-1 text-sm font-medium text-emerald-200/90">{copy.price_label}</p>
      <p className="mt-2 text-sm text-zinc-400">{copy.blurb}</p>
      {copy.highlights.length ? (
        <ul className="mt-3 space-y-1.5 text-sm text-zinc-200">
          {copy.highlights.slice(0, 3).map((line) => (
            <li key={line} className="flex gap-2">
              <span className="text-emerald-400" aria-hidden>
                ✓
              </span>
              <span>{line}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {spec.id === "ai_business_bot" ? (
        <div className="mt-3">
          <BotChannelIconRow />
        </div>
      ) : null}
      <ul className="mt-3 space-y-1 text-xs text-zinc-400">
        {copy.includes.slice(0, 3).map((line) => (
          <li key={line} className="flex gap-2">
            <span className="text-emerald-400/80" aria-hidden>
              ✓
            </span>
            <span>{line}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[11px] text-zinc-500">
        {t("catalog.stagesLine", {
          count: copy.stagesCount,
          timeline: copy.timeline,
          defaultValue: "{{count}} stages · {{timeline}}",
        })}
      </p>
      <p className="mt-1 text-[11px] text-zinc-500">
        {t("catalog.supportLine", {
          support: copy.support,
          defaultValue: "Support: {{support}}",
        })}
      </p>
      <span
        className={`mt-4 inline-flex text-sm font-semibold ${
          live ? "text-emerald-300" : "text-zinc-500"
        }`}
      >
        {live
          ? spec.id === "website_check"
            ? t("s0.startAnalysis", { defaultValue: "Start free check →" })
            : t("catalog.openForm", { defaultValue: "Open order form →" })
          : t("catalog.interestForm", { defaultValue: "Interest form →" })}
      </span>
    </>
  );

  const className = `block h-full w-full rounded-2xl border p-5 text-left transition ${
    featured
      ? "border-emerald-400/30 bg-emerald-500/[0.06] hover:border-emerald-300/45"
      : live
        ? "border-white/12 bg-white/[0.03] hover:border-white/25 hover:bg-white/[0.05]"
        : "border-white/8 bg-white/[0.02] opacity-90"
  }`;

  if (localOnly) {
    return (
      <button
        type="button"
        className={className}
        onClick={() => onOpenLocal!(spec.id)}
      >
        {inner}
      </button>
    );
  }

  return (
    <Link href={spec.href} prefetch className={className}>
      {inner}
      {!live ? (
        <p className="mt-2 text-xs text-zinc-500">{copy.deliveryNote}</p>
      ) : null}
    </Link>
  );
}

export function ServiceCatalogGrid({
  mode = "hub",
  onOpenLocal,
}: {
  mode?: "hub" | "all";
  /** Hub: free website check stays on /site without full navigation. */
  onOpenLocal?: (serviceId: string) => void;
}) {
  const { t } = useTranslation("site");
  const primary = HUB_PRIMARY_SERVICE_IDS.map(
    (id) => SERVICE_SPECS.find((s) => s.id === id)!,
  ).filter(Boolean);
  const more = HUB_MORE_SERVICE_IDS.map(
    (id) => SERVICE_SPECS.find((s) => s.id === id)!,
  ).filter(Boolean);

  if (mode === "all") {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {SERVICE_SPECS.filter((s) => s.id !== "website_check").map((spec) => (
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
            onOpenLocal={onOpenLocal}
          />
        ))}
      </div>
      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
          {t("catalog.moreTitle", { defaultValue: "More website services" })}
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
