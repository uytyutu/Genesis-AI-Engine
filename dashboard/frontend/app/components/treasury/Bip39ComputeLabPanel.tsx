"use client";

import { useCallback, useState } from "react";

type DualReport = {
  ok?: boolean;
  insight?: string;
  telegram_required?: boolean;
  bip39_compute_lab?: {
    workers?: number;
    vectors_per_sec?: number;
    total_vectors?: number;
    income_claimed?: boolean;
    security?: { status?: string };
  };
  opportunity_ai?: {
    epoch_status?: string;
    outcome?: string;
    message?: string;
    hypotheses?: number;
    counts?: { working_brick_candidates?: number };
    honest_negative?: string;
  };
  screen_number_is_not_found?: { found?: boolean; status?: string };
  public_chain_analyzer?: { status?: string; events?: { balance_ton?: number; address?: string }[] };
  error?: string;
};

export function Bip39ComputeLabPanel() {
  const [data, setData] = useState<DualReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/compute/bip39-lab", { cache: "no-store" });
      const json = (await res.json()) as DualReport;
      if (!res.ok || json.ok === false) setErr(json.error || `HTTP ${res.status}`);
      else setData(json);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }, []);

  const b = data?.bip39_compute_lab;

  return (
    <section className="rounded-2xl border-2 border-violet-800/40 bg-gradient-to-b from-violet-950/25 to-zinc-950 p-5 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-violet-400">
            BIP39 Compute Lab · без Telegram · без чужих seed
          </p>
          <h2 className="mt-1 text-lg font-bold text-violet-50">ВЫЧИСЛИТЕЛЬНАЯ АРХИТЕКТУРА (гипотеза видео)</h2>
          <p className="mt-2 max-w-3xl text-xs text-zinc-400 leading-relaxed">
            Видео показывает интересный compute — но <strong className="text-zinc-200">не доказывает заработок</strong>.
            Lab меряет vectors/s (own/synthetic). Opportunity AI параллельно ищет permissionless rewards. FOUND = адрес +
            tx + баланс + законный источник + перевод — не цифра на экране.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void run()}
          className="rounded-lg bg-violet-500 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
        >
          {busy ? "Bench…" : "ЗАПУСТИТЬ DUAL"}
        </button>
      </div>

      <div className="grid gap-2 sm:grid-cols-4 text-[11px]">
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">vectors/s</p>
          <p className="text-xl font-bold text-violet-100">{b?.vectors_per_sec ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">workers</p>
          <p className="text-xl font-bold text-violet-100">{b?.workers ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">income_claimed</p>
          <p className="text-xl font-bold text-rose-200">{String(b?.income_claimed ?? false)}</p>
        </div>
        <div className="rounded-lg border border-zinc-700 p-3">
          <p className="font-mono text-zinc-500">FOUND trap</p>
          <p className="text-xl font-bold text-amber-100">
            {data ? String(data.screen_number_is_not_found?.found) : "—"}
          </p>
        </div>
      </div>

      {data?.insight && <p className="text-xs text-zinc-400">{data.insight}</p>}
      {data?.opportunity_ai && (
        <p className="text-xs text-cyan-200/90">
          Opportunity AI: {data.opportunity_ai.epoch_status || data.opportunity_ai.outcome}
          {data.opportunity_ai.counts?.working_brick_candidates != null
            ? ` · bricks=${data.opportunity_ai.counts.working_brick_candidates}`
            : ""}{" "}
          · {data.opportunity_ai.message}
        </p>
      )}
      {err && <div className="rounded border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">{err}</div>}
      <p className="text-[10px] text-zinc-600">
        CLI: <code className="text-zinc-400">npm run compute:bip39</code> · foreign seed path = SECURITY_REJECTED
      </p>
    </section>
  );
}
