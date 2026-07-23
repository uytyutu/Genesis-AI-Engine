"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { publicApiBase } from "../../lib/publicApiBase";

type CaseRow = {
  case_id: string;
  created_at?: string;
  url?: string;
  health_score?: number;
  recommended_id?: string | null;
  vector_plain?: string;
  repair_quote?: { label?: string | null; package_id?: string | null };
};

export default function ClientAnalysesPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [cases, setCases] = useState<CaseRow[]>([]);

  async function onLoad(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await fetch(
        `${publicApiBase()}/api/client/analysis-cases?email=${encodeURIComponent(email.trim())}`
      );
      const body = await res.json();
      if (!res.ok) {
        setError(String(body.detail || "load_failed"));
        setCases([]);
        return;
      }
      setCases(body.cases || []);
    } catch {
      setError("Не удалось загрузить отчёты. Запустите Virtus Core.");
      setCases([]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <ClientWorkspaceShell
      title="Website Analysis"
      subtitle="Сохранённые отчёты по вашему email — вход воронки Repair / New Website."
    >
      <form onSubmit={onLoad} className="flex flex-col gap-3 sm:flex-row">
        <input
          type="email"
          required
          value={email}
          onChange={(ev) => setEmail(ev.target.value)}
          placeholder="email@firma.de"
          className="min-w-0 flex-1 rounded-xl border border-white/15 bg-black/40 px-3 py-2.5 text-sm text-white"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black disabled:opacity-50"
        >
          {busy ? "…" : "Показать отчёты"}
        </button>
      </form>
      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      <ul className="mt-6 space-y-3">
        {cases.map((c) => (
          <li
            key={c.case_id}
            className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm"
          >
            <p className="font-medium text-white">{c.url || c.case_id}</p>
            <p className="mt-1 text-xs text-zinc-500">
              {c.created_at} · score {c.health_score ?? "—"} ·{" "}
              {c.recommended_id || "—"}
              {c.repair_quote?.label ? ` · repair ${c.repair_quote.label}` : ""}
            </p>
            {c.vector_plain ? (
              <p className="mt-2 text-zinc-300">{c.vector_plain}</p>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-2">
              {c.repair_quote?.package_id ? (
                <Link
                  href={`/order?package=${c.repair_quote.package_id}&analysis_case=${c.case_id}`}
                  className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-black"
                >
                  Order Repair
                </Link>
              ) : null}
              <Link
                href={`/order?package=business&analysis_case=${c.case_id}`}
                className="rounded-lg border border-white/20 px-3 py-1.5 text-xs text-white"
              >
                Order New Website
              </Link>
              <Link
                href="/site#analysis"
                className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-zinc-400"
              >
                Новый анализ
              </Link>
            </div>
          </li>
        ))}
      </ul>
      {!busy && cases.length === 0 ? (
        <p className="mt-6 text-sm text-zinc-500">
          Пока пусто. Сделайте бесплатный анализ на{" "}
          <Link href="/site#analysis" className="text-emerald-300 hover:underline">
            /site
          </Link>{" "}
          с тем же email.
        </p>
      ) : null}
    </ClientWorkspaceShell>
  );
}
