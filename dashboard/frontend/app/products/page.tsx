"use client";

import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { Badge, ButtonLink, Card } from "../components/ui";
import {
  COMMERCIAL_CATALOG,
  type CommercialCategory,
  type CommercialRow,
} from "../lib/commercialCatalog";
import { BRAND_NAME } from "../lib/publicBrand";

/**
 * G2.3 — Commercial Readiness catalog.
 * Rule: Coming Soon must never look like Buy now.
 */

const SECTIONS: { id: CommercialCategory; title: string; blurb: string }[] = [
  {
    id: "product",
    title: "Products",
    blurb: "What you can start today — order a landing or activate Vector.",
  },
  {
    id: "one_time",
    title: "One-time Services",
    blurb: "Priced for the German SMB market. Online checkout opens when delivery is ready.",
  },
  {
    id: "monthly",
    title: "Monthly Services",
    blurb: "Subscriptions with clear tariffs. Buy buttons stay Coming Soon until billing works.",
  },
];

function SectionBlock({
  title,
  blurb,
  rows,
}: {
  title: string;
  blurb: string;
  rows: CommercialRow[];
}) {
  if (rows.length === 0) return null;
  return (
    <section className="mt-10">
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      <p className="mt-1 text-sm text-genesis-muted">{blurb}</p>
      <ul className="mt-4 space-y-3">
        {rows.map((row) => {
          const live = row.cta !== "coming_soon";
          return (
            <li key={row.id}>
              <Card
                padding="lg"
                className={`text-left ${live ? "border-emerald-500/25" : ""}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold text-white">{row.name}</p>
                    <p className="mt-1 text-sm font-medium text-emerald-200/90">
                      {row.price_label}
                    </p>
                    <p className="mt-1 text-sm text-genesis-muted">{row.includes}</p>
                  </div>
                  <Badge variant={live ? "success" : "outline"}>
                    {row.cta_label}
                  </Badge>
                </div>
                {live && row.cta_href ? (
                  <ButtonLink
                    href={row.cta_href}
                    variant={row.cta === "order_now" ? "success" : "primary"}
                    size="md"
                    className="mt-4"
                  >
                    {row.cta_label} →
                  </ButtonLink>
                ) : (
                  <p className="mt-4 text-xs text-zinc-500">
                    Not for sale online yet — price is published, checkout opens
                    when the delivery path is ready.
                  </p>
                )}
              </Card>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default function ProductsPage() {
  return (
    <PublicPageShell>
      <div className="mx-auto max-w-3xl py-4">
        <div className="text-center">
          <Badge variant="outline">{BRAND_NAME}</Badge>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-white">
            Commercial catalog
          </h1>
          <p className="mt-3 text-genesis-muted">
            Honest offers for Germany: Products · One-time · Monthly. We never
            sell what is not ready.
          </p>
        </div>

        {SECTIONS.map((section) => (
          <SectionBlock
            key={section.id}
            title={section.title}
            blurb={section.blurb}
            rows={COMMERCIAL_CATALOG.filter((r) => r.category === section.id)}
          />
        ))}

        <p className="mt-8 text-center text-sm text-genesis-muted">
          <Link href="/site" className="text-emerald-300 hover:underline">
            ← Back to {BRAND_NAME}
          </Link>
        </p>
      </div>
    </PublicPageShell>
  );
}
