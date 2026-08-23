"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getBackendApiBase } from "../../lib/backendApiBase";

const API = getBackendApiBase();

type Coverage = {
  countries_total?: number;
  live?: number;
  ready?: number;
  planned?: number;
  blocked?: number;
  data_available?: number;
  research?: number;
  honesty_rule?: string;
};

type MatrixRow = {
  country?: string;
  name?: string;
  postal?: boolean;
  city?: boolean;
  address?: boolean;
  phone?: boolean;
  vat?: boolean;
  status?: string;
};

type QualityRow = {
  country?: string;
  status?: string;
  market_score?: number;
};

type Product = {
  id?: string;
  name?: string;
  status?: string;
  live_countries?: number;
};

export default function ApiMarketsPage() {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [matrix, setMatrix] = useState<MatrixRow[]>([]);
  const [quality, setQuality] = useState<QualityRow[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [err, setErr] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/farm/rapidapi/markets?wave_only=true`);
      const data = await res.json();
      if (!data?.ok) {
        setErr(String(data?.error || "load failed"));
        return;
      }
      setCoverage(data.coverage || null);
      setMatrix(Array.isArray(data.matrix) ? data.matrix : []);
      setQuality(Array.isArray(data.quality) ? data.quality : []);
      setProducts(Array.isArray(data.products) ? data.products : []);
      setErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "load failed");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const yesNo = (v?: boolean) => (v ? "YES" : "NO");

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-violet-300/80">API Farm</p>
          <h1 className="mt-1 text-2xl font-semibold text-white">Global Market Coverage</h1>
          <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
            One architecture · many markets · activate only with verified commercial datasets.
            REAL revenue ≠ coverage map.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 text-sm">
          <Link href="/farm/rapidapi" className="text-emerald-300 hover:underline">
            ← API Farm
          </Link>
          <Link href="/business" className="text-genesis-muted hover:underline">
            Business Health
          </Link>
        </div>
      </div>

      {err ? (
        <p className="rounded-lg border border-rose-500/40 bg-rose-950/30 px-3 py-2 text-sm text-rose-100">
          {err}
        </p>
      ) : null}

      <section className="grid gap-2 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
        {(
          [
            ["Countries", coverage?.countries_total],
            ["LIVE", coverage?.live],
            ["READY", coverage?.ready],
            ["DATA AVAILABLE", coverage?.data_available],
            ["PLANNED", coverage?.planned],
            ["BLOCKED", coverage?.blocked],
          ] as const
        ).map(([label, val]) => (
          <div
            key={label}
            className="rounded-xl border border-violet-500/25 bg-violet-950/20 px-3 py-3"
          >
            <p className="text-[10px] uppercase tracking-wide text-violet-300/80">{label}</p>
            <p className="mt-1 text-xl font-semibold text-white">{val ?? "—"}</p>
          </div>
        ))}
      </section>

      <p className="text-xs text-genesis-muted">
        {coverage?.honesty_rule ||
          "LIVE only with verified dataset + commercial_use_allowed. No invented postal/city data."}
      </p>

      <section className="overflow-x-auto rounded-2xl border border-white/10">
        <table className="min-w-full text-left text-sm text-violet-50/90">
          <thead className="bg-black/30 text-xs uppercase tracking-wide text-violet-300/80">
            <tr>
              <th className="px-3 py-2">Country</th>
              <th className="px-3 py-2">Postal</th>
              <th className="px-3 py-2">City</th>
              <th className="px-3 py-2">Address</th>
              <th className="px-3 py-2">Phone</th>
              <th className="px-3 py-2">VAT</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Score</th>
            </tr>
          </thead>
          <tbody>
            {matrix.map((row) => {
              const q = quality.find((x) => x.country === row.country);
              return (
                <tr key={row.country} className="border-t border-white/5">
                  <td className="px-3 py-2">
                    {row.country} {row.name}
                  </td>
                  <td className="px-3 py-2">{yesNo(row.postal)}</td>
                  <td className="px-3 py-2">{yesNo(row.city)}</td>
                  <td className="px-3 py-2">{yesNo(row.address)}</td>
                  <td className="px-3 py-2">{yesNo(row.phone)}</td>
                  <td className="px-3 py-2">{yesNo(row.vat)}</td>
                  <td className="px-3 py-2">{row.status}</td>
                  <td className="px-3 py-2">{q?.market_score ?? 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
        <h2 className="text-sm font-semibold text-white">RapidAPI product shells</h2>
        <ul className="mt-2 space-y-1 text-xs text-genesis-muted">
          {products.map((p) => (
            <li key={p.id}>
              {p.name} · {p.status}
              {typeof p.live_countries === "number" ? ` · live markets ${p.live_countries}` : ""}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
