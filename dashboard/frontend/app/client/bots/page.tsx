"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { BRAND_NAME } from "../../lib/publicBrand";
import { publicApiBase } from "../../lib/publicApiBase";

type BotPackage = {
  package_id: string;
  name: string;
  setup_amount: number;
  monthly_amount: number;
  setup_label: string;
  monthly_label: string;
  price_label: string;
  currency: string;
  symbol: string;
  market_code: string;
};

type BotCatalog = {
  product_id: string;
  packages: BotPackage[];
  market_code: string;
  currency: string;
  symbol: string;
  channels: string[];
  note?: string;
};

const MARKETS = [
  "DE",
  "AT",
  "CH",
  "US",
  "CA",
  "GB",
  "AU",
  "NZ",
  "JP",
  "KR",
  "SG",
  "NL",
  "BE",
  "FR",
  "IE",
  "ES",
  "IT",
  "PL",
  "CZ",
  "SE",
  "NO",
  "DK",
  "FI",
  "UA",
  "RU",
  "KZ",
] as const;

export default function ClientBotsPage() {
  const api = publicApiBase();
  const [market, setMarket] = useState("DE");
  const [catalog, setCatalog] = useState<BotCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    async (code: string) => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `${api}/api/public/bots/pricing?market=${encodeURIComponent(code)}`,
          { cache: "no-store" },
        );
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        setCatalog((await res.json()) as BotCatalog);
      } catch (err) {
        setError(err instanceof Error ? err.message : "load_failed");
        setCatalog(null);
      } finally {
        setLoading(false);
      }
    },
    [api],
  );

  useEffect(() => {
    void load(market);
  }, [load, market]);

  const subtitle = useMemo(
    () =>
      `Отдельный продукт ${BRAND_NAME}: AI-боты для бизнеса. Цены по рынку и валюте — не входят в Landing Website.`,
    [],
  );

  return (
    <ClientWorkspaceShell title="Боты" subtitle={subtitle}>
      <div className="mb-6 flex flex-wrap items-end gap-3">
        <label className="text-sm text-zinc-400">
          Рынок
          <select
            className="mt-1 block rounded-xl border border-white/15 bg-black/40 px-3 py-2 text-sm text-white"
            value={market}
            onChange={(e) => setMarket(e.target.value)}
          >
            {MARKETS.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </label>
        {catalog ? (
          <p className="pb-2 text-sm text-zinc-500">
            Валюта: {catalog.currency} ({catalog.symbol})
          </p>
        ) : null}
      </div>

      {error ? (
        <p className="mb-4 text-sm text-rose-200">
          Не удалось загрузить цены: {error}
        </p>
      ) : null}
      {loading ? <p className="text-sm text-zinc-500">Загрузка цен…</p> : null}

      {!loading && catalog ? (
        <ul className="grid gap-4 sm:grid-cols-3">
          {catalog.packages.map((pkg) => (
            <li
              key={pkg.package_id}
              className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <p className="text-lg font-semibold text-white">{pkg.name}</p>
              <p className="mt-3 text-2xl font-semibold tracking-tight text-emerald-300">
                {pkg.setup_label}
              </p>
              <p className="mt-1 text-sm text-zinc-400">
                настройка · затем {pkg.monthly_label}/мес
              </p>
              <p className="mt-4 flex-1 text-xs leading-relaxed text-zinc-500">
                Website chat + Telegram. WhatsApp / Instagram — в rollout.
              </p>
              <div className="mt-5">
                <Link
                  href="/projects/chatbot/setup"
                  className="inline-block rounded-lg bg-emerald-500 px-3 py-1.5 text-sm font-semibold text-black hover:brightness-110"
                >
                  Заказать и настроить
                </Link>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      {catalog?.channels?.length ? (
        <p className="mt-6 text-sm text-zinc-500">
          Каналы: {catalog.channels.join(" · ")}
        </p>
      ) : null}
      {catalog?.note ? (
        <p className="mt-2 text-xs text-zinc-600">{catalog.note}</p>
      ) : null}
    </ClientWorkspaceShell>
  );
}
