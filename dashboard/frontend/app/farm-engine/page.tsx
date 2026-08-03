"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Candidate = {
  id: string;
  title?: string;
  url?: string;
  repository?: string;
  issue_id?: string;
  languages?: string[];
  reward_usd?: number;
  confidence_pct?: number;
  acceptance_pct?: number;
  overall_confidence_pct?: number;
  estimated_hours?: number;
  recommendation?: string;
  risk?: string;
  competitors?: number;
  bot_installed?: boolean;
  blockers?: string[];
  required_capabilities?: string[];
};

type Task = Candidate & {
  status?: string;
  pr_url?: string;
  real_income?: boolean;
  estimated_reward_usd?: number;
  payout_confirmed_usd?: number;
  opire_commands?: { try?: string; claim?: string };
  execution_checklist?: { id: string; title: string; done?: boolean }[];
};

type Panel = {
  ok?: boolean;
  workflow_ru?: string[];
  funnel?: {
    found?: number;
    analyzed?: number;
    high_confidence?: number;
    ceo_approved?: number;
    executed?: number;
    pr_submitted?: number;
    pr_merged?: number;
    paid?: number;
    total_confirmed_usd?: number;
    bottleneck_hint_ru?: string;
  };
  scan?: {
    ok?: boolean;
    error?: string | null;
    scanned?: number;
    filtered_out?: number;
    threshold?: number;
    candidates?: Candidate[];
    finance_law_ru?: string;
    official_flow?: string;
  };
  active_tasks?: Task[];
  history?: Task[];
  ledger?: {
    estimated_usd?: number;
    real_confirmed_usd?: number;
    note_ru?: string;
  };
};

export default function FarmEnginePage() {
  const [data, setData] = useState<Panel | null>(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/farm/opire`);
      if (!res.ok) throw new Error("opire_farm");
      setData(await res.json());
      setError("");
    } catch {
      setError("Backend недоступен — запустите Genesis.exe");
      setData(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 45_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  async function decide(id: string, decision: "approve" | "skip") {
    setBusy(`${id}:${decision}`);
    try {
      const q = new URLSearchParams({ reward_id: id, decision });
      const res = await fetch(`${API}/api/farm/opire/decide?${q}`, { method: "POST" });
      const body = await res.json();
      if (!res.ok || body.ok === false) {
        setError(String(body.message_ru || body.error || "decide failed"));
        setInfo("");
      } else {
        setError("");
        setInfo(String(body.message_ru || "OK"));
        await refresh();
      }
    } catch {
      setError("decide failed");
    } finally {
      setBusy("");
    }
  }

  async function advance(id: string, status: string) {
    setBusy(`${id}:${status}`);
    try {
      const q = new URLSearchParams({ reward_id: id, status });
      if (status === "payout_confirmed") {
        const conf = window.prompt(
          "Payment Confirmation ID от Opire (обязательно для REAL):",
        );
        if (!conf?.trim()) {
          setError("Без Confirmation ID нельзя отметить REAL");
          setBusy("");
          return;
        }
        q.set("payment_confirmation_id", conf.trim());
      }
      const res = await fetch(`${API}/api/farm/opire/advance?${q}`, { method: "POST" });
      const body = await res.json();
      if (!res.ok || body.ok === false) {
        setError(String(body.message_ru || body.error || "advance failed"));
      } else {
        setInfo(`Статус → ${status}`);
        await refresh();
      }
    } catch {
      setError("advance failed");
    } finally {
      setBusy("");
    }
  }

  const candidates = data?.scan?.candidates || [];
  const active = data?.active_tasks || [];

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <header className="text-center">
        <p className="text-xs uppercase tracking-widest text-sky-300/80">
          Farm Engine · Opire Semi-Auto
        </p>
        <h1 className="mt-2 text-2xl font-bold text-white">Bounty Scanner</h1>
        <p className="mt-2 text-sm text-genesis-muted">
          Внутренний доход владельца — отдельно от Commercial Engine / клиентов Virtus Core.
          Официальный процесс Opire: /try → PR /claim → merge → payout. REAL только после
          подтверждения выплаты.
        </p>
        <div className="mt-3 flex flex-wrap justify-center gap-2 text-xs">
          <Link href="/" className="rounded-lg border border-white/15 px-3 py-1.5 hover:bg-white/5">
            Mission Control
          </Link>
          <Link
            href="/payout"
            className="rounded-lg border border-white/15 px-3 py-1.5 hover:bg-white/5"
          >
            Вывод
          </Link>
          <a
            href="https://app.opire.dev"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-sky-400/30 px-3 py-1.5 text-sky-100 hover:bg-sky-500/10"
          >
            Opire Dashboard ↗
          </a>
        </div>
      </header>

      {error ? (
        <p className="rounded-lg border border-amber-500/40 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          {error}
        </p>
      ) : null}
      {info ? (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-100">
          {info}
        </p>
      ) : null}

      <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
        <p className="text-xs text-genesis-muted">
          {(data?.workflow_ru || []).join(" → ")}
        </p>
        {data?.funnel ? (
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {(
              [
                ["Найдено", data.funnel.found],
                ["Проанализировано", data.funnel.analyzed],
                ["Высокая вероятность", data.funnel.high_confidence],
                ["Одобрено CEO", data.funnel.ceo_approved],
                ["В работе / выполнено", data.funnel.executed],
                ["PR отправлено", data.funnel.pr_submitted],
                ["PR принято", data.funnel.pr_merged],
                ["Выплачено", data.funnel.paid],
              ] as const
            ).map(([label, val]) => (
              <div
                key={label}
                className="rounded-lg border border-white/10 bg-black/25 px-2.5 py-2"
              >
                <p className="text-[10px] text-genesis-muted">{label}</p>
                <p className="text-base font-semibold text-white">{val ?? 0}</p>
              </div>
            ))}
          </div>
        ) : null}
        {data?.funnel?.bottleneck_hint_ru ? (
          <p className="mt-2 text-[11px] text-amber-100/85">{data.funnel.bottleneck_hint_ru}</p>
        ) : null}
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <div className="rounded-lg border border-amber-500/20 bg-amber-950/20 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-amber-200/70">
              Estimated (не доход)
            </p>
            <p className="text-lg font-semibold text-amber-50">
              ${data?.ledger?.estimated_usd?.toFixed(2) ?? "0.00"}
            </p>
          </div>
          <div className="rounded-lg border border-emerald-500/25 bg-emerald-950/20 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-emerald-200/70">
              Total Confirmed (REAL)
            </p>
            <p className="text-lg font-semibold text-emerald-50">
              $
              {(
                data?.funnel?.total_confirmed_usd ??
                data?.ledger?.real_confirmed_usd ??
                0
              ).toFixed(2)}
            </p>
          </div>
        </div>
        <p className="mt-2 text-[11px] text-genesis-muted">{data?.ledger?.note_ru}</p>
        <p className="mt-1 text-[11px] text-sky-100/70">
          Scan: {data?.scan?.scanned ?? 0} · filtered {data?.scan?.filtered_out ?? 0} ·
          threshold {data?.scan?.threshold ?? "—"}% · {data?.scan?.official_flow}
        </p>
        {data?.scan?.error ? (
          <p className="mt-2 text-xs text-rose-200">Scan error: {data.scan.error}</p>
        ) : null}
        <button
          type="button"
          onClick={() => void refresh()}
          className="mt-3 rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5"
        >
          Обновить Scanner
        </button>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-white">
          High-confidence · Approve / Skip
        </h2>
        {candidates.length === 0 ? (
          <p className="rounded-lg border border-white/10 bg-black/20 px-3 py-4 text-sm text-genesis-muted">
            Нет кандидатов выше порога. Scanner отфильтровал низкий confidence / неподдерживаемые
            языки / высокую конкуренцию.
          </p>
        ) : (
          <ul className="space-y-3">
            {candidates.map((c) => (
              <li
                key={c.id}
                className="rounded-xl border border-sky-500/20 bg-sky-950/15 px-4 py-3 text-sm"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-white hover:underline"
                    >
                      {c.title}
                    </a>
                    <p className="mt-0.5 text-[11px] text-genesis-muted">
                      {c.repository} · #{c.issue_id} · {(c.languages || []).join(", ") || "lang?"}
                      {c.bot_installed ? " · Opire bot" : ""}
                    </p>
                  </div>
                  <p className="text-lg font-semibold text-emerald-200">
                    ${c.reward_usd?.toFixed(0)}
                  </p>
                </div>
                <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-sky-100/80">
                  <span>Confidence {c.overall_confidence_pct}%</span>
                  <span>Success {c.confidence_pct}%</span>
                  <span>Acceptance {c.acceptance_pct}%</span>
                  <span>~{c.estimated_hours}h</span>
                  <span>Risk {c.risk}</span>
                  <span>Competitors {c.competitors}</span>
                  <span className="font-semibold text-emerald-200">{c.recommendation}</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={Boolean(busy)}
                    onClick={() => void decide(c.id, "approve")}
                    className="rounded-lg bg-emerald-500/90 px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-40"
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={Boolean(busy)}
                    onClick={() => void decide(c.id, "skip")}
                    className="rounded-lg border border-white/20 px-3 py-1.5 text-xs text-zinc-200 disabled:opacity-40"
                  >
                    Skip
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-white">Активные bounty (после Approve)</h2>
        {active.length === 0 ? (
          <p className="text-sm text-genesis-muted">Пока нет одобренных задач.</p>
        ) : (
          <ul className="space-y-3">
            {active.map((t) => (
              <li
                key={t.id}
                className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm"
              >
                <div className="flex flex-wrap justify-between gap-2">
                  <div>
                    <p className="font-medium text-white">{t.title}</p>
                    <p className="text-[11px] text-genesis-muted">
                      {t.repository} · status <span className="text-sky-200">{t.status}</span> ·
                      est ${t.estimated_reward_usd ?? t.reward_usd} · REAL{" "}
                      {t.real_income ? "yes" : "no"}
                    </p>
                    {t.opire_commands ? (
                      <p className="mt-1 font-mono text-[11px] text-amber-100/80">
                        {t.opire_commands.try} → PR body: {t.opire_commands.claim}
                      </p>
                    ) : null}
                  </div>
                  <a
                    href={t.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-sky-300 hover:underline"
                  >
                    Issue ↗
                  </a>
                </div>
                <ul className="mt-2 space-y-0.5 text-[11px] text-genesis-muted">
                  {(t.execution_checklist || []).map((s) => (
                    <li key={s.id}>
                      {s.done ? "✓" : "○"} {s.title}
                    </li>
                  ))}
                </ul>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(
                    [
                      ["executing", "Executing"],
                      ["draft_pr", "Draft PR ready"],
                      ["pr_submitted", "CEO Submit PR"],
                      ["maintainer_review", "Under review"],
                      ["changes_requested", "Changes requested"],
                      ["merged", "Merged"],
                      ["payment_available", "Payment available"],
                      ["payout_confirmed", "Payout confirmed → REAL"],
                    ] as const
                  ).map(([st, label]) => (
                    <button
                      key={st}
                      type="button"
                      disabled={Boolean(busy)}
                      onClick={() => void advance(t.id, st)}
                      className="rounded-lg border border-white/15 px-2.5 py-1 text-[10px] text-zinc-200 hover:bg-white/5 disabled:opacity-40"
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
