"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

type ComputeReport = {
  ok?: boolean;
  conclusion?: string;
  auto_mode?: boolean;
  electricity_status?: string;
  electricity_eur_per_kwh?: number | null;
  hardware?: {
    cpu_name?: string;
    cpu_cores?: number;
    cpu_threads?: number;
    ram_gb?: number;
    os?: string;
    gpu?: {
      name?: string;
      vram_mib?: number;
      power_watts?: number;
      temperature_c?: number;
      cuda_available?: boolean;
    };
    notes?: string[];
  };
  benchmarks?: Array<{
    algorithm: string;
    device: string;
    ops_per_sec: number;
    unit: string;
    duration_sec: number;
    notes: string;
  }>;
  opportunities?: Array<{
    rank: number;
    source_id: string;
    algorithm: string;
    measured_ops_per_sec: number | null;
    expected_gross_eur_day: number | null;
    expected_cost_eur_day: number | null;
    expected_net_eur_day: number | null;
    confidence: number;
    status: string;
    can_run: boolean;
    detail: string;
  }>;
  current_worker?: {
    state?: string;
    measured_ops_per_sec?: number;
    real_reward?: number;
    message?: string;
  } | null;
  treasury?: {
    expected: number;
    pending: number;
    confirmed: number;
    withdrawable: number;
    currency: string;
    rule: string;
  };
  blockers?: string[];
  laws?: string[];
};

function Badge({ children, tone }: { children: React.ReactNode; tone: "ok" | "warn" | "bad" | "info" }) {
  const cls =
    tone === "ok"
      ? "border-emerald-600 bg-emerald-950/40 text-emerald-300"
      : tone === "warn"
        ? "border-amber-500 bg-amber-950/40 text-amber-200"
        : tone === "bad"
          ? "border-rose-600 bg-rose-950/40 text-rose-300"
          : "border-cyan-700 bg-cyan-950/40 text-cyan-300";
  return <span className={`rounded border px-2 py-0.5 text-[10px] font-bold ${cls}`}>{children}</span>;
}

export default function ComputePage() {
  const [data, setData] = useState<ComputeReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (measure: boolean) => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(`/api/compute/status${measure ? "?measure=1" : ""}`, { cache: "no-store" });
      const json = (await res.json()) as ComputeReport & { error?: string };
      if (!res.ok || json.ok === false) {
        setErr(json.error || `HTTP ${res.status}`);
        setData(null);
      } else {
        setData(json);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка запроса");
    } finally {
      setBusy(false);
    }
  }, []);

  const hw = data?.hardware;
  const gpu = hw?.gpu;

  return (
    <main className="min-h-screen bg-zinc-950 px-4 py-8 text-zinc-100 md:px-8">
      <div className="mx-auto max-w-6xl space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-zinc-800 pb-4">
          <div>
            <p className="text-xs font-mono uppercase tracking-wide text-cyan-600">Virtus Core · Research</p>
            <h1 className="text-2xl font-semibold text-cyan-300">REAL COMPUTE ENGINE</h1>
            <p className="mt-1 max-w-2xl text-sm text-zinc-400">
              Не майнер «из коробки». Железо → бенчмарк → экономика → только VERIFIED worker. REAL € только после
              CONFIRMED payout. По умолчанию AUTO_MODE=false.
            </p>
          </div>
          <div className="flex gap-3 text-sm">
            <Link href="/treasury" className="text-zinc-400 hover:underline">
              ← Treasury / Agent
            </Link>
            <Link href="/executive" className="text-zinc-400 hover:underline">
              CEO
            </Link>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => void load(false)}
            className="rounded-lg bg-cyan-700 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
          >
            {busy ? "Скан…" : "Аудит железа + экономика"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void load(true)}
            className="rounded-lg bg-amber-600 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
          >
            Измерить SHA-256 (reward=0)
          </button>
        </div>

        {err && (
          <div className="rounded-lg border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">{err}</div>
        )}

        {data && (
          <>
            <div className="rounded-xl border border-zinc-700 bg-zinc-900/60 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={data.conclusion?.includes("NO PROFITABLE") ? "warn" : "info"}>
                  {data.conclusion || "—"}
                </Badge>
                <Badge tone="info">AUTO_MODE={String(data.auto_mode)}</Badge>
                <Badge tone={data.electricity_status === "KNOWN" ? "ok" : "warn"}>
                  electricity={data.electricity_status}
                  {data.electricity_eur_per_kwh != null ? ` €${data.electricity_eur_per_kwh}/kWh` : ""}
                </Badge>
              </div>
            </div>

            <section className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4 text-xs space-y-1">
                <h2 className="text-sm font-semibold text-cyan-400">Hardware</h2>
                <p>CPU: {hw?.cpu_name || "—"}</p>
                <p>
                  Cores/Threads: {hw?.cpu_cores}/{hw?.cpu_threads} · RAM {hw?.ram_gb} GB
                </p>
                <p>OS: {hw?.os}</p>
                <p className="pt-2 font-semibold text-amber-200">GPU: {gpu?.name || "не обнаружен"}</p>
                <p>
                  VRAM {gpu?.vram_mib} MiB · {gpu?.power_watts} W · {gpu?.temperature_c} °C · CUDA=
                  {String(gpu?.cuda_available)}
                </p>
                {(hw?.notes || []).map((n) => (
                  <p key={n} className="text-zinc-500">
                    · {n}
                  </p>
                ))}
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4 text-xs space-y-2">
                <h2 className="text-sm font-semibold text-cyan-400">Treasury (REAL = CONFIRMED)</h2>
                <div className="grid grid-cols-2 gap-2 font-mono">
                  <div className="rounded border border-zinc-800 p-2">
                    EXPECTED
                    <div className="text-zinc-400">{data.treasury?.expected ?? 0}</div>
                  </div>
                  <div className="rounded border border-zinc-800 p-2">
                    PENDING
                    <div className="text-amber-300">{data.treasury?.pending ?? 0}</div>
                  </div>
                  <div className="rounded border border-emerald-900 p-2">
                    CONFIRMED
                    <div className="text-emerald-400">{data.treasury?.confirmed ?? 0}</div>
                  </div>
                  <div className="rounded border border-zinc-800 p-2">
                    WITHDRAWABLE
                    <div>{data.treasury?.withdrawable ?? 0}</div>
                  </div>
                </div>
                <p className="text-[10px] text-zinc-500">{data.treasury?.rule}</p>
              </div>
            </section>

            <section className="rounded-xl border border-zinc-800 p-4">
              <h2 className="text-sm font-semibold text-cyan-400">Benchmarks (measured)</h2>
              <ul className="mt-2 space-y-2 text-xs font-mono">
                {(data.benchmarks || []).map((b) => (
                  <li key={b.algorithm} className="rounded border border-zinc-800 p-2">
                    <span className="text-emerald-400">
                      {b.algorithm}: {b.ops_per_sec} {b.unit}
                    </span>
                    <span className="text-zinc-500"> · {b.duration_sec}s · {b.device}</span>
                    <div className="text-[10px] text-zinc-500">{b.notes}</div>
                  </li>
                ))}
              </ul>
            </section>

            <section className="rounded-xl border border-zinc-800 p-4 overflow-x-auto">
              <h2 className="text-sm font-semibold text-cyan-400">Opportunity ranking</h2>
              <table className="mt-2 w-full text-left text-[11px]">
                <thead className="text-zinc-500">
                  <tr>
                    <th className="p-1">#</th>
                    <th className="p-1">Source</th>
                    <th className="p-1">Status</th>
                    <th className="p-1">Measured</th>
                    <th className="p-1">Gross/d</th>
                    <th className="p-1">Cost/d</th>
                    <th className="p-1">Net/d</th>
                    <th className="p-1">Run?</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.opportunities || []).map((o) => (
                    <tr key={o.source_id} className="border-t border-zinc-900 align-top">
                      <td className="p-1">{o.rank}</td>
                      <td className="p-1">
                        <div className="text-zinc-200">{o.algorithm}</div>
                        <div className="text-[10px] text-zinc-500 max-w-xs">{o.detail}</div>
                      </td>
                      <td className="p-1">{o.status}</td>
                      <td className="p-1 font-mono">
                        {o.measured_ops_per_sec != null ? o.measured_ops_per_sec : "—"}
                      </td>
                      <td className="p-1">{o.expected_gross_eur_day ?? "—"}</td>
                      <td className="p-1">{o.expected_cost_eur_day ?? "—"}</td>
                      <td className="p-1">{o.expected_net_eur_day ?? "—"}</td>
                      <td className="p-1">{o.can_run ? "yes*" : "no"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 text-[10px] text-zinc-500">* research measure only — reward always 0 until external CONFIRMED payout.</p>
            </section>

            {data.current_worker && (
              <section className="rounded-xl border border-amber-800/50 bg-amber-950/20 p-4 text-xs">
                <h2 className="text-sm font-semibold text-amber-200">Current worker</h2>
                <p>State: {data.current_worker.state}</p>
                <p>Measured: {data.current_worker.measured_ops_per_sec ?? "—"} H/s</p>
                <p>REAL reward: {data.current_worker.real_reward ?? 0}</p>
                <p className="text-zinc-400">{data.current_worker.message}</p>
              </section>
            )}

            <section className="rounded-xl border border-zinc-800 p-4 text-xs text-zinc-400">
              <h2 className="text-sm font-semibold text-zinc-300">Blockers</h2>
              <ul className="mt-2 list-disc pl-5 space-y-1">
                {(data.blockers || []).map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            </section>
          </>
        )}

        {!data && !err && (
          <p className="text-sm text-zinc-500">
            Нажмите «Аудит» — система сама определит CPU/GPU (nvidia-smi), прогонит локальный бенчмарк и покажет, есть
            ли экономически положительный compute. Терминал:{" "}
            <code className="text-amber-200">npm run compute:audit</code>
          </p>
        )}
      </div>
    </main>
  );
}
