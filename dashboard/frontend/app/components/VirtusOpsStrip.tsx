"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchApi } from "../lib/fetchApi";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Props = {
  clientsCount?: number;
  revenueEur?: number;
  websitesSold?: number;
  systemMark?: string;
};

/** MC 2.0 morning strip — Virtus commercial pulse (not Farm). */
export function VirtusOpsStrip({
  clientsCount,
  revenueEur,
  websitesSold,
  systemMark,
}: Props) {
  const [ordersNew, setOrdersNew] = useState<number | null>(null);
  const [inProduction, setInProduction] = useState<number | null>(null);
  const [supportOpen, setSupportOpen] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [ordersRes, supportRes] = await Promise.all([
          fetchApi(`${API}/api/sales/orders`, { timeoutMs: 8_000 }),
          fetchApi(`${API}/api/support/threads?limit=50`, { timeoutMs: 8_000 }),
        ]);
        if (cancelled) return;
        if (ordersRes.ok) {
          const body = await ordersRes.json();
          const list = (body.orders || []) as {
            status?: string;
            paid?: boolean;
          }[];
          setOrdersNew(
            list.filter((o) =>
              ["pending_confirmation", "confirmed", "awaiting_payment"].includes(
                String(o.status || ""),
              ),
            ).length,
          );
          setInProduction(
            list.filter((o) =>
              ["paid", "in_production", "ready"].includes(String(o.status || "")),
            ).length,
          );
        }
        if (supportRes.ok) {
          const body = await supportRes.json();
          const threads = body.items || body.threads || [];
          setSupportOpen(Array.isArray(threads) ? threads.length : 0);
        }
      } catch {
        /* Overview still works from ceo-dashboard alone */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const cards: {
    label: string;
    value: string;
    href: string;
    hint: string;
  }[] = [
    {
      label: "Customers",
      value: clientsCount != null ? String(clientsCount) : "—",
      href: "/clients",
      hint: "зарегистрировано",
    },
    {
      label: "New orders",
      value: ordersNew != null ? String(ordersNew) : "—",
      href: "/orders",
      hint: "ждут действия",
    },
    {
      label: "Revenue",
      value:
        revenueEur != null ? formatEur(revenueEur) : "—",
      href: "/finance",
      hint: "Virtus commercial",
    },
    {
      label: "In production",
      value: inProduction != null ? String(inProduction) : String(websitesSold ?? "—"),
      href: "/factory",
      hint: "Website · Shop · AI",
    },
    {
      label: "Support",
      value: supportOpen != null ? String(supportOpen) : "—",
      href: "/support",
      hint: "inbox threads",
    },
    {
      label: "System",
      value: systemMark ? "●" : "●",
      href: "/check",
      hint: systemMark || "Health check",
    },
  ];

  return (
    <section className="rounded-xl border border-emerald-500/25 bg-emerald-950/20 p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold text-emerald-100">
          Virtus Ops · сегодня
        </h2>
        <p className="text-[11px] text-zinc-500">
          Farm / Earn Labs — в Studios, не здесь
        </p>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <Link
            key={c.label}
            href={c.href}
            className="rounded-lg border border-white/10 bg-black/30 px-3 py-2.5 hover:border-emerald-400/40 hover:bg-black/40"
          >
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">
              {c.label}
            </p>
            <p className="mt-1 text-xl font-semibold text-white">{c.value}</p>
            <p className="mt-0.5 text-[11px] text-zinc-400">{c.hint}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
