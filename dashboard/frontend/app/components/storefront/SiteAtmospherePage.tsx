"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { BRAND_NAME } from "../../lib/publicBrand";
import { PublicPageShell } from "../PublicPageShell";
import {
  BotChatMock,
  OfficeDocsMock,
} from "../storefront/VitrineProductMocks";
import { PUBLIC_VITRINE_THUMB_VERSION } from "../../lib/publicVitrineCatalog";

const THUMB_V = PUBLIC_VITRINE_THUMB_VERSION;

export type AtmosphereExample = {
  title: string;
  blurb: string;
  thumb?: string;
  href?: string;
  /** Prefer chat/doc mockups over recycled website heroes */
  visual?: "chat-receptionist" | "chat-support" | "chat-sales" | "chat-booking" | "office" | "photo";
};

type Props = {
  kind: "websites" | "shops" | "bots";
  title: string;
  subtitle: string;
  ctaLabel: string;
  ctaHref: string;
  secondaryLabel?: string;
  secondaryHref?: string;
  examples: AtmosphereExample[];
};

export function SiteAtmospherePage({
  kind,
  title,
  subtitle,
  ctaLabel,
  ctaHref,
  secondaryLabel,
  secondaryHref,
  examples,
}: Props) {
  const { t } = useTranslation("site");
  const tone =
    kind === "websites"
      ? "from-sky-950 via-zinc-950 to-zinc-950"
      : kind === "shops"
        ? "from-violet-950 via-zinc-950 to-zinc-950"
        : "from-emerald-950 via-zinc-950 to-zinc-950";

  return (
    <PublicPageShell>
      <div className={`min-h-[70vh] bg-gradient-to-b ${tone} px-4 py-10 text-white sm:px-6 sm:py-14`}>
        <div className="mx-auto max-w-6xl space-y-10">
          <Link
            href="/site"
            className="inline-flex text-sm text-zinc-400 underline-offset-2 hover:text-white hover:underline"
          >
            {t("agencyHub.directions.backCore", {
              defaultValue: "← Back to Virtus Core",
            })}
          </Link>

          <header className="max-w-2xl space-y-4">
            <p className="text-xs font-semibold tracking-[0.24em] text-white/60">
              {BRAND_NAME.toUpperCase()}
            </p>
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{title}</h1>
            <p className="text-lg text-zinc-300">{subtitle}</p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                href={ctaHref}
                className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-violet-600 px-6 text-sm font-semibold text-white hover:bg-violet-500"
              >
                {ctaLabel}
              </Link>
              {secondaryLabel && secondaryHref ? (
                <Link
                  href={secondaryHref}
                  className="inline-flex min-h-[48px] items-center justify-center rounded-xl border border-white/20 px-6 text-sm font-semibold text-white hover:bg-white/[0.04]"
                >
                  {secondaryLabel}
                </Link>
              ) : null}
            </div>
          </header>

          {kind === "bots" ? (
            <div className="max-w-xl">
              <BotChatMock variant="receptionist" />
            </div>
          ) : null}

          <section className="space-y-4">
            <h2 className="text-xl font-semibold">
              {t("agencyHub.directions.examplesTitle", {
                defaultValue: "Selected examples",
              })}
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {examples.map((ex) => {
                const visual = ex.visual || (ex.thumb ? "photo" : "chat-receptionist");
                const body = (
                  <>
                    <div className="aspect-[16/10] overflow-hidden bg-zinc-900">
                      {visual === "office" ? (
                        <div className="h-full p-2">
                          <OfficeDocsMock compact />
                        </div>
                      ) : visual.startsWith("chat") ? (
                        <div className="h-full p-2">
                          <BotChatMock
                            compact
                            variant={
                              visual === "chat-support"
                                ? "support"
                                : visual === "chat-sales"
                                  ? "sales"
                                  : visual === "chat-booking"
                                    ? "booking"
                                    : "receptionist"
                            }
                          />
                        </div>
                      ) : (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img
                          src={
                            ex.thumb!.includes("?")
                              ? ex.thumb!
                              : `${ex.thumb}?v=${THUMB_V}`
                          }
                          alt=""
                          className="h-full w-full object-cover"
                          loading="lazy"
                        />
                      )}
                    </div>
                    <div className="space-y-1 p-4">
                      <h3 className="font-semibold text-white">{ex.title}</h3>
                      <p className="text-sm text-zinc-400">{ex.blurb}</p>
                    </div>
                  </>
                );
                return ex.href ? (
                  <a
                    key={ex.title}
                    href={ex.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] transition hover:border-violet-400/40"
                  >
                    {body}
                  </a>
                ) : (
                  <div
                    key={ex.title}
                    className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03]"
                  >
                    {body}
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </PublicPageShell>
  );
}
