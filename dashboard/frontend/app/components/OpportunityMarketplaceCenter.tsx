"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Farm = {
  id: string;
  label_ru: string;
  stars: number;
  status: string;
  status_ru: string;
  flow_ru?: string[];
  rule_ru?: string;
  href?: string;
  networks?: { id: string; connected: boolean; role: string }[];
  products?: { id: string; enabled?: boolean; path?: string; price_eur?: string }[];
};

type Opp = {
  id: string;
  title_ru: string;
  farm_id: string;
  roi: string;
  priority: number;
  action_ru: string;
  why_ru: string;
  live: boolean;
};

type Board = {
  headline_ru?: string;
  title_ru?: string;
  subtitle_ru?: string;
  principle_ru?: string;
  digital_farm_note_ru?: string;
  external_task_marketplace?: boolean;
  farms?: Farm[];
  opportunities?: Opp[];
  desk_pulse?: {
    ready_now?: number;
    waiting?: number;
    autosend?: boolean;
    runner?: boolean;
    sent_today?: number;
    stripe_key?: boolean;
    digistore_key?: boolean;
  };
};

type ResearchFinding = {
  id: string;
  platform_id: string;
  name?: string;
  stars?: number;
  verdict?: string;
  title_ru?: string;
  detail_ru?: string;
  needs_ceo_key?: boolean;
  can_get_task?: boolean;
  can_submit?: boolean;
  can_payout?: boolean;
  gate_ru?: string;
  next_ru?: string;
};

type ResearchPlatform = {
  id: string;
  name?: string;
  stars?: number;
  verdict?: string;
  api_get_task?: boolean;
  api_submit_result?: boolean;
  api_receive_payout?: boolean;
  automation_pct?: number;
  tos_automation?: string;
  reason_ru?: string;
  next_ru?: string;
  gate_ru?: string;
  ceo_approved?: boolean;
  real_payout_proven?: boolean;
};

type AdapterPlatform = {
  id: string;
  name?: string;
  maturity_level?: number;
  maturity_label_ru?: string;
  has_adapter?: boolean;
  sandbox_passed?: boolean;
  work_farm_eligible?: boolean;
  verdict?: string;
  real_payout_proven?: boolean;
  ceo_approved?: boolean;
};

type AdapterBoard = {
  title_ru?: string;
  rule_ru?: string;
  levels_ru?: string[];
  pipeline_ru?: string[];
  counts_by_level?: Record<string, number>;
  work_farm_allowlist?: string[];
  platforms?: AdapterPlatform[];
  forbidden_ru?: string[];
};

type ResearchBoard = {
  title_ru?: string;
  rule_ru?: string;
  last_scan_at?: string | null;
  next_scan_at?: string | null;
  scan_count?: number;
  counts?: { working?: number; candidates?: number; rejected?: number; findings?: number };
  findings?: ResearchFinding[];
  platforms?: ResearchPlatform[];
  pipeline_ru?: string[];
  forbidden_ru?: string[];
};

function roiTone(roi: string): string {
  if (roi === "high") return "border-emerald-500/40 bg-emerald-950/25 text-emerald-100";
  if (roi === "medium") return "border-amber-500/35 bg-amber-950/20 text-amber-50";
  return "border-white/10 bg-black/20 text-white/80";
}

function statusPill(status: string): string {
  if (status === "live") return "border-emerald-400/40 text-emerald-200";
  if (status === "partial" || status === "own_orders_only") return "border-sky-400/40 text-sky-200";
  return "border-white/20 text-white/50";
}

function verdictPill(v: string): string {
  if (v === "working") return "border-emerald-400/50 text-emerald-200";
  if (v === "candidate" || v === "partial") return "border-amber-400/45 text-amber-100";
  return "border-rose-400/35 text-rose-200/80";
}

export function OpportunityMarketplaceCenter() {
  const [board, setBoard] = useState<Board | null>(null);
  const [research, setResearch] = useState<ResearchBoard | null>(null);
  const [adapters, setAdapters] = useState<AdapterBoard | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [researchMsg, setResearchMsg] = useState("");

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const [mRes, rRes, aRes] = await Promise.all([
        fetch(`${API}/api/earn-marketplace/today`),
        fetch(`${API}/api/worker-research/board`),
        fetch(`${API}/api/worker-adapters/board`),
      ]);
      if (!mRes.ok) {
        setErr(`Marketplace ${mRes.status} — перезапустите Genesis`);
        return;
      }
      setBoard(await mRes.json());
      if (rRes.ok) setResearch(await rRes.json());
      if (aRes.ok) setAdapters(await aRes.json());
      setErr("");
    } catch {
      setErr("Backend недоступен");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function runScan() {
    setResearchMsg("");
    try {
      const res = await fetch(`${API}/api/worker-research/scan?force=true`, { method: "POST" });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setResearchMsg(String(body?.detail || "Scan failed"));
        return;
      }
      setResearchMsg(`Scan OK · findings ${body.findings_count ?? "—"}`);
      await load();
    } catch {
      setResearchMsg("Backend недоступен");
    }
  }

  async function approvePlatform(platformId: string) {
    setResearchMsg("");
    try {
      const res = await fetch(
        `${API}/api/worker-research/platforms/${encodeURIComponent(platformId)}/approve`,
        { method: "POST" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setResearchMsg(String(body?.detail || "Approve failed"));
        return;
      }
      setResearchMsg(body.message_ru || "Одобрено");
      await load();
    } catch {
      setResearchMsg("Backend недоступен");
    }
  }

  async function adapterAction(
    platformId: string,
    action: "create" | "sandbox" | "promote-working",
  ) {
    setResearchMsg("");
    try {
      const res = await fetch(
        `${API}/api/worker-adapters/${encodeURIComponent(platformId)}/${action}`,
        { method: "POST" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setResearchMsg(String(body?.detail || `${action} failed`));
        return;
      }
      setResearchMsg(body.message_ru || `${action} OK · L${body.maturity_level ?? "?"}`);
      await load();
    } catch {
      setResearchMsg("Backend недоступен");
    }
  }

  const pulse = board?.desk_pulse;
  const opps = board?.opportunities ?? [];
  const farms = board?.farms ?? [];
  const findings = research?.findings ?? [];
  const platforms = research?.platforms ?? [];
  const adapterRows = adapters?.platforms ?? [];
  const levelCounts = adapters?.counts_by_level ?? {};

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6">
        <header className="rounded-2xl border border-violet-500/30 bg-gradient-to-br from-violet-950/40 via-genesis-panel to-genesis-bg p-6 sm:p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-violet-300/80">{BRAND_NAME}</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">
            {board?.title_ru ?? "Marketplace возможностей"}
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
            {board?.subtitle_ru ??
              "Реальные способы создать ценность и получить оплату. Не цифровая ферма разметки."}
          </p>
          <p className="mt-3 text-sm font-medium text-violet-100">
            {board?.headline_ru ?? (busy ? "Загрузка…" : "—")}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/90 hover:bg-white/10"
            >
              Обновить сегодня
            </button>
            <Link
              href="/revenue"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm text-genesis-muted hover:text-white"
            >
              Доход / Work Farm →
            </Link>
            <Link
              href="/acquisition"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm text-genesis-muted hover:text-white"
            >
              Country Desk →
            </Link>
            <Link
              href="/"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm text-genesis-muted hover:text-white"
            >
              Ферма разметки (другое) →
            </Link>
          </div>
          {err ? <p className="mt-3 text-xs text-amber-200">{err}</p> : null}
          {board?.digital_farm_note_ru ? (
            <p className="mt-3 text-[11px] text-white/40">{board.digital_farm_note_ru}</p>
          ) : null}
        </header>

        {pulse ? (
          <section className="grid gap-2 sm:grid-cols-4">
            <Pulse label="Ready" value={String(pulse.ready_now ?? 0)} />
            <Pulse label="Waiting" value={String(pulse.waiting ?? 0)} />
            <Pulse label="Sent today" value={String(pulse.sent_today ?? 0)} />
            <Pulse
              label="Ключи"
              value={`Stripe ${pulse.stripe_key ? "✓" : "—"} · Digi ${pulse.digistore_key ? "✓" : "—"}`}
            />
          </section>
        ) : null}

        <section className="rounded-2xl border border-sky-500/30 bg-gradient-to-br from-sky-950/35 via-black/20 to-genesis-panel p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-sky-100">
                {research?.title_ru ?? "Worker Research Lab"}
              </h2>
              <p className="mt-1 max-w-2xl text-[11px] text-genesis-muted">
                {research?.rule_ru ??
                  "Ищем платформы с официальным циклом: взять задачу → сделать → получить оплату. Без авто-регистрации."}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void runScan()}
              className="rounded-lg border border-sky-400/40 bg-sky-950/40 px-3 py-1.5 text-xs text-sky-100 hover:bg-sky-900/50"
            >
              Scan сейчас
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2 text-[10px] text-white/55">
            <span>
              Working {research?.counts?.working ?? 0} · Candidates {research?.counts?.candidates ?? 0}{" "}
              · Rejected {research?.counts?.rejected ?? 0}
            </span>
            {research?.next_scan_at ? (
              <span>· next {String(research.next_scan_at).slice(0, 16)}</span>
            ) : null}
          </div>
          {research?.pipeline_ru?.length ? (
            <p className="mt-2 text-[11px] text-sky-100/70">{research.pipeline_ru.join(" → ")}</p>
          ) : null}
          {researchMsg ? <p className="mt-2 text-xs text-amber-100">{researchMsg}</p> : null}

          <h3 className="mt-5 text-xs font-semibold uppercase tracking-wide text-sky-200/80">
            Сегодня найдено (worker)
          </h3>
          <ul className="mt-2 space-y-2">
            {findings.length === 0 ? (
              <li className="text-xs text-genesis-muted">Нет findings — нажмите Scan.</li>
            ) : (
              findings.slice(0, 8).map((f) => (
                <li
                  key={f.id}
                  className="rounded-xl border border-white/10 bg-black/25 px-3 py-2.5 text-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-white">
                      {"★".repeat(Math.min(5, Number(f.stars) || 0))} {f.title_ru || f.name}
                    </p>
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[10px] uppercase ${verdictPill(
                        String(f.verdict || ""),
                      )}`}
                    >
                      {f.verdict}
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] text-white/60">{f.detail_ru}</p>
                  <p className="mt-1 text-[10px] text-white/40">
                    API: task {f.can_get_task ? "✓" : "✗"} · submit {f.can_submit ? "✓" : "✗"} · pay{" "}
                    {f.can_payout ? "✓" : "✗"}
                  </p>
                  {f.gate_ru ? <p className="mt-1 text-[10px] text-amber-200/80">{f.gate_ru}</p> : null}
                  {f.needs_ceo_key ? (
                    <button
                      type="button"
                      onClick={() => void approvePlatform(f.platform_id)}
                      className="mt-2 rounded-md border border-emerald-500/35 px-2.5 py-1 text-[11px] text-emerald-100 hover:bg-emerald-950/40"
                    >
                      CEO: в очередь Adapter (ключ вручную)
                    </button>
                  ) : null}
                </li>
              ))
            )}
          </ul>

          <h3 className="mt-5 text-xs font-semibold uppercase tracking-wide text-white/50">
            Каталог платформ
          </h3>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {platforms.map((p) => (
              <article
                key={p.id}
                className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-[11px]"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-white/90">{p.name}</span>
                  <span className={`rounded border px-1.5 py-0.5 text-[9px] uppercase ${verdictPill(String(p.verdict || ""))}`}>
                    {p.verdict}
                  </span>
                </div>
                <p className="mt-1 text-white/45">{p.reason_ru}</p>
                {p.ceo_approved ? (
                  <p className="mt-1 text-emerald-300/80">CEO approved · payout {p.real_payout_proven ? "proven" : "pending"}</p>
                ) : null}
              </article>
            ))}
          </div>
          {research?.forbidden_ru?.length ? (
            <p className="mt-3 text-[10px] text-rose-200/60">
              Запрещено: {research.forbidden_ru.join(" · ")}
            </p>
          ) : null}
        </section>

        <section className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-950/30 via-black/20 to-genesis-panel p-5 sm:p-6">
          <h2 className="text-sm font-semibold text-amber-100">
            {adapters?.title_ru ?? "Worker Adapter Builder"}
          </h2>
          <p className="mt-1 max-w-2xl text-[11px] text-genesis-muted">
            {adapters?.rule_ru ??
              "Research → Adapter → Sandbox → First payout → Working. Sandbox ≠ деньги."}
          </p>
          {adapters?.pipeline_ru?.length ? (
            <p className="mt-2 text-[11px] text-amber-100/75">{adapters.pipeline_ru.join(" → ")}</p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
            {[0, 1, 2, 3, 4, 5, 6].map((lv) => (
              <span
                key={lv}
                className="rounded border border-white/15 px-2 py-0.5 text-white/70"
              >
                L{lv} {levelCounts[String(lv)] ?? 0}
              </span>
            ))}
          </div>
          <p className="mt-2 text-[10px] text-emerald-200/80">
            Work Farm allowlist: {(adapters?.work_farm_allowlist || []).join(", ") || "—"}
          </p>
          <ul className="mt-4 space-y-2">
            {adapterRows
              .filter((p) => p.verdict !== "reject")
              .map((p) => (
                <li
                  key={p.id}
                  className="rounded-xl border border-white/10 bg-black/25 px-3 py-2.5 text-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-white">{p.name || p.id}</p>
                    <span className="rounded-full border border-amber-400/40 px-2 py-0.5 text-[10px] text-amber-100">
                      L{p.maturity_level ?? 0} {p.maturity_label_ru}
                    </span>
                  </div>
                  <p className="mt-1 text-[10px] text-white/45">
                    adapter {p.has_adapter ? "✓" : "—"} · sandbox {p.sandbox_passed ? "✓" : "—"} ·
                    payout {p.real_payout_proven ? "✓" : "—"} · farm{" "}
                    {p.work_farm_eligible ? "✓" : "—"}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void adapterAction(p.id, "create")}
                      className="rounded-md border border-white/20 px-2 py-1 text-[11px] text-white/80 hover:bg-white/5"
                    >
                      Create Adapter
                    </button>
                    <button
                      type="button"
                      onClick={() => void adapterAction(p.id, "sandbox")}
                      className="rounded-md border border-sky-400/35 px-2 py-1 text-[11px] text-sky-100 hover:bg-sky-950/40"
                    >
                      Sandbox
                    </button>
                    <button
                      type="button"
                      onClick={() => void adapterAction(p.id, "promote-working")}
                      className="rounded-md border border-emerald-500/40 px-2 py-1 text-[11px] text-emerald-100 hover:bg-emerald-950/40"
                    >
                      Promote Working
                    </button>
                  </div>
                </li>
              ))}
          </ul>
          {adapters?.forbidden_ru?.length ? (
            <p className="mt-3 text-[10px] text-rose-200/60">
              {adapters.forbidden_ru.join(" · ")}
            </p>
          ) : null}
        </section>

        <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/15 p-5">
          <h2 className="text-sm font-semibold text-emerald-100">Сегодня найдено</h2>
          <p className="mt-1 text-[11px] text-genesis-muted">
            Список возможностей с ROI — делать живые (live) в первую очередь.
          </p>
          <ol className="mt-4 space-y-3">
            {opps.map((o, idx) => (
              <li
                key={o.id}
                className={`rounded-xl border px-4 py-3 text-sm ${roiTone(o.roi)}`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-medium text-white">
                    <span className="mr-2 text-white/40">{idx + 1}.</span>
                    {o.title_ru}
                  </p>
                  <div className="flex gap-2 text-[10px] uppercase">
                    <span className="rounded-full border border-white/20 px-2 py-0.5">
                      ROI {o.roi}
                    </span>
                    <span
                      className={`rounded-full border px-2 py-0.5 ${
                        o.live
                          ? "border-emerald-400/40 text-emerald-200"
                          : "border-white/15 text-white/45"
                      }`}
                    >
                      {o.live ? "live" : "plan"}
                    </span>
                  </div>
                </div>
                <p className="mt-2 text-xs text-white/85">→ {o.action_ru}</p>
                <p className="mt-1 text-[11px] text-white/50">{o.why_ru}</p>
                <p className="mt-1 font-mono text-[10px] text-violet-200/70">{o.farm_id}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-white">Пять ферм ценности</h2>
          <div className="grid gap-3 lg:grid-cols-2">
            {farms.map((f) => (
              <article
                key={f.id}
                className="rounded-2xl border border-white/10 bg-black/25 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-white">
                    {"★".repeat(Math.min(5, f.stars))} {f.label_ru}
                  </h3>
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] uppercase ${statusPill(f.status)}`}
                  >
                    {f.status}
                  </span>
                </div>
                <p className="mt-2 text-xs text-genesis-muted">{f.status_ru}</p>
                {f.flow_ru?.length ? (
                  <p className="mt-2 text-[11px] text-violet-100/75">{f.flow_ru.join(" → ")}</p>
                ) : null}
                {f.networks?.length ? (
                  <ul className="mt-2 flex flex-wrap gap-1.5 text-[10px]">
                    {f.networks.map((n) => (
                      <li
                        key={n.id}
                        className={`rounded border px-2 py-0.5 ${
                          n.connected
                            ? "border-emerald-500/40 text-emerald-200"
                            : "border-white/10 text-white/40"
                        }`}
                      >
                        {n.id}
                      </li>
                    ))}
                  </ul>
                ) : null}
                {f.products?.length ? (
                  <ul className="mt-2 space-y-1 text-[11px] text-genesis-muted">
                    {f.products.map((p) => (
                      <li key={p.id}>
                        {p.enabled ? "✓" : "○"} {p.id}
                        {p.path ? ` · ${p.path}` : ""}
                        {p.price_eur ? ` · ${p.price_eur}` : ""}
                      </li>
                    ))}
                  </ul>
                ) : null}
                <p className="mt-2 text-[10px] text-white/40">{f.rule_ru}</p>
                {f.href ? (
                  <Link href={f.href} className="mt-3 inline-block text-xs text-violet-300 hover:underline">
                    Открыть →
                  </Link>
                ) : null}
              </article>
            ))}
          </div>
        </section>

        {board?.principle_ru ? (
          <p className="text-center text-xs text-genesis-muted">{board.principle_ru}</p>
        ) : null}
        <p className="text-center text-[10px] text-white/30">
          external_task_marketplace = {String(board?.external_task_marketplace ?? false)}
        </p>
      </div>
    </main>
  );
}

function Pulse({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2">
      <p className="text-[10px] uppercase text-white/45">{label}</p>
      <p className="mt-1 text-sm font-semibold tabular-nums text-white">{value}</p>
    </div>
  );
}
