"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { FarmExecutionTimeline } from "../components/FarmExecutionTimeline";
import {
  isGithubAuthPath,
  isGithubHost,
  isGithubOpenArmed,
  disarmGithubOpen,
  onGithubLinkClick,
} from "../lib/farmGithubGate";
import { loadFarmAccounts, type FarmAccountState } from "../lib/farmAccountPermissions";
import { FarmAccountPermissions } from "../components/FarmAccountPermissions";
import {
  getBackendApiBase,
  probeBackendReachability,
} from "../lib/backendApiBase";

const API = getBackendApiBase();

function ExternalOpenButton({
  href,
  children,
  className,
  title,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
  title?: string;
}) {
  if (!href) return null;
  if (!isGithubHost(href)) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={className} title={title}>
        {children}
      </a>
    );
  }
  return (
    <button
      type="button"
      title={title || "Открыть только после вашего клика (не OAuth Farm)"}
      className={className}
      onClick={() =>
        onGithubLinkClick(href, (reason) => {
          console.warn("[farm-engine] github open blocked", reason, href);
        })
      }
    >
      {children}
    </button>
  );
}

type Candidate = {
  id: string;
  platform?: string;
  also_on?: string[];
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
  estimated_minutes?: number;
  roi_stars?: number;
  roi_label?: string;
  roi_usd_per_hour?: number;
  roi_rank_score?: number;
  recommendation?: string;
  risk?: string;
  difficulty?: string;
  competitors?: number;
  success_probability_pct?: number;
  bot_installed?: boolean;
  blockers?: string[];
  reject_reasons?: string[];
  band?: string;
  required_capabilities?: string[];
  issue_body_preview?: string;
  issue_analysis?: { summary_ru?: string; signals?: string[] };
  repo_status?: "ok" | "unreachable" | "auth_required" | "unknown" | string;
  sniper_detail_ru?: string;
  money_mode_eligible?: boolean;
  overall_success_probability_pct?: number;
  task_type?: string;
  capability_auto?: string;
  preflight?: {
    verdict?: string;
    go?: boolean;
    approve_allowed?: boolean;
    action?: string;
    checks?: { id: string; label: string; ok?: boolean; critical?: boolean; mark?: string; detail?: string }[];
    note_ru?: string;
  };
  success_checklist?: { id: string; label: string; ok?: boolean }[];
  ceo_action_links?: {
    issue?: string;
    repository?: string;
    opire_dashboard?: string;
    try_comment_text?: string;
    claim_pr_text?: string;
    new_pr_hint?: string;
  };
};

type ConnectorInfo = {
  id: string;
  display_name?: string;
  tier?: string;
  status?: string;
  runtime_status?: string;
  notes_ru?: string;
  official_docs_url?: string;
};

type Task = Candidate & {
  status?: string;
  pipeline_state?: string;
  pipeline_label?: string;
  pr_url?: string;
  real_income?: boolean;
  estimated_reward_usd?: number;
  payout_confirmed_usd?: number;
  execution_error?: string;
  execution_heal?: string;
  auto_retry_execution?: boolean;
  execution_estimate?: {
    success_probability_pct?: number;
    estimated_hours?: number;
    reward_usd?: number;
  };
  opire_commands?: { try?: string; claim?: string };
  execution_checklist?: { id: string; title: string; done?: boolean }[];
  execution?: {
    stage?: string;
    ok?: boolean;
    branch?: string;
    workspace?: string;
    error?: string;
    error_detail?: string;
    patch_ready?: boolean;
    ready_for_ceo?: { message_ru?: string; route?: string; patch_ready?: boolean };
    stages?: Record<
      string,
      {
        ok?: boolean;
        note_ru?: string;
        error_detail?: string;
        mode?: string;
        files_touched?: string[];
        brief_path?: string;
        skipped?: boolean;
        executor?: string;
        message_ru?: string;
      }
    >;
  };
};

type Panel = {
  ok?: boolean;
  north_star_ru?: string;
  market_note_ru?: string;
  workflow_ru?: string[];
  readiness?: {
    summary_ru?: string;
    next_proof_ru?: string;
    github_token_ready?: boolean;
    rows?: { component: string; status: string; mark: string; detail_ru?: string }[];
  };
  proof?: {
    tasks_analysed?: number;
    approved?: number;
    executed?: number;
    draft_pr?: number;
    submitted?: number;
    merged?: number;
    reward_confirmed?: number;
    payout_confirmed?: number;
    real_confirmed_usd?: number;
    proof_status?: string;
    proof_mark?: string;
    criterion_ru?: string;
    message_ru?: string;
  };
  connectors?: ConnectorInfo[];
  folders?: {
    new?: { label_ru?: string; count?: number; hint_ru?: string };
    active?: { label_ru?: string; count?: number; hint_ru?: string };
    archive?: { label_ru?: string; count?: number; hint_ru?: string };
  };
  seen_ledger_count?: number;
  skipped_forever_count?: number;
  archive_tasks?: Task[];
  funnel?: {
    found?: number;
    analyzed?: number;
    high_confidence?: number;
    review_all_count?: number;
    confidence_bands?: Record<string, number>;
    ceo_approved?: number;
    executed?: number;
    execution_ready_for_submit?: number;
    execution_failed?: number;
    pr_submitted?: number;
    pr_merged?: number;
    pr_merged_first_pass?: number;
    pr_changes_requested?: number;
    paid?: number;
    total_confirmed_usd?: number;
    bottleneck_hint_ru?: string;
  };
  execution_success?: {
    approved?: number;
    started?: number;
    execution?: number;
    completed?: number;
    failed?: number;
    skipped?: number;
    draft_pr?: number;
    merged?: number;
    paid?: number;
    start_rate?: number | null;
    complete_rate?: number | null;
    avg_execution_s?: number | null;
    avg_execution_samples?: number;
    note_ru?: string;
  };
  pipeline?: {
    found?: number;
    approved?: number;
    started?: number;
    draft_pr?: number;
    merged?: number;
    paid?: number;
    impossible?: number;
    blocker_ru?: string | null;
    note_ru?: string;
  };
  scan?: {
    ok?: boolean;
    error?: string | null;
    scanned?: number;
    filtered_out?: number;
    threshold?: number;
    from_cache?: boolean;
    candidates?: Candidate[];
    candidates_take_all?: Candidate[];
    review_all?: Candidate[];
    market_live?: Candidate[];
    market_live_count?: number;
    market_live_note_ru?: string;
    confidence_bands?: Record<string, number>;
    analytics?: {
      languages?: { name: string; count: number }[];
      reject_reasons?: { reason: string; count: number }[];
      potential_reward?: {
        high?: { label?: string; usd?: number; count?: number };
        medium?: { label?: string; usd?: number; count?: number };
        low?: { label?: string; usd?: number; count?: number };
        total_usd?: number;
        note_ru?: string;
      };
      capability_coverage?: {
        rows?: {
          capability: string;
          demand: number;
          covered: boolean;
          coverage_pct: number;
          lost_bounties: number;
        }[];
        coverage_pct?: number;
        note_ru?: string;
      };
      north_star_ru?: string;
      top_roi?: {
        title?: string;
        reward_usd?: number;
        estimated_minutes?: number;
        roi_stars?: number;
        roi_label?: string;
        roi_usd_per_hour?: number;
      }[];
    };
    money_mode?: {
      enabled_default?: boolean;
      threshold?: number;
      count?: number;
      hidden_count?: number;
      go_count?: number;
      mode?: string;
      note_ru?: string;
    };
    sniper_skipped?: number;
    sniper_probed?: number;
    excluded_already_active?: number;
    pool_before_sniper?: number;
    finance_law_ru?: string;
    official_flow?: string;
    architecture_ru?: string;
    law_ru?: string;
  };
  active_tasks?: Task[];
  history?: Task[];
  ledger?: {
    estimated_usd?: number;
    real_confirmed_usd?: number;
    note_ru?: string;
  };
  learning_ledger?: {
    closed?: number;
    wins?: number;
    losses?: number;
    earned_usd?: number;
    avg_actual_hours_win?: number | null;
    avg_reviews_win?: number | null;
    why_won?: { reason: string; count: number }[];
    why_lost?: { reason: string; count: number }[];
    top_win_languages?: { name: string; wins: number }[];
    recent?: {
      outcome?: string;
      title?: string;
      earned_usd?: number;
      reward_usd?: number;
      actual_hours?: number | null;
      reviews?: number;
      why_won?: string[];
      why_lost?: string[];
      roi_label?: string;
    }[];
    min_closed_for_stats?: number;
    stats_ready?: boolean;
    note_ru?: string;
    north_star_ru?: string;
  };
  payout_success?: {
    found?: number;
    approved?: number;
    executed?: number;
    draft_pr?: number;
    merged?: number;
    paid?: number;
    note_ru?: string;
  };
  income_contours?: {
    title_ru?: string;
    note_ru?: string;
    farms?: {
      id: string;
      label: string;
      role_ru?: string;
      href?: string;
      primary_kpi?: string;
      mode?: string;
      honesty_ru?: string;
    }[];
  };
  capability_matrix?: {
    matrix?: { id: string; label: string; auto?: string; note_ru?: string }[];
    note_ru?: string;
  };
};

/** Old draft_pr + needs_external without files — Research Agent never ran. */
function taskNeedsResearchRetry(t: Task): boolean {
  const impl = t.execution?.stages?.implementation;
  const files = impl?.files_touched?.length || 0;
  const mode = String(impl?.mode || "");
  const route = String(
    t.execution?.ready_for_ceo?.route ||
      (t.execution?.stages?.routing as { route?: string } | undefined)?.route ||
      mode ||
      "",
  );
  const noPatch = !t.execution?.patch_ready && files === 0;
  return (
    t.status === "needs_external" ||
    (noPatch && (route === "needs_external" || mode === "needs_external"))
  );
}

export default function FarmEnginePage() {
  const [data, setData] = useState<Panel | null>(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState("");
  const [opireLink, setOpireLink] = useState("");
  const [reviewBand, setReviewBand] = useState<"all" | "80+" | "60+" | "40+" | "20+">("all");
  const [moneyMode, setMoneyMode] = useState(true);
  const [hiddenIds, setHiddenIds] = useState<Set<string>>(() => new Set());
  const [accounts, setAccounts] = useState<FarmAccountState[]>([]);
  const autoLiveScanDone = useRef(false);

  useEffect(() => {
    setAccounts(loadFarmAccounts());
  }, []);

  const refresh = useCallback(async (opts?: { enrich?: boolean; forceScan?: boolean }) => {
    const enrich = opts?.enrich === true;
    // Default: cached panel (fast). Sniper/git only when user clicks «Обновить Scanner».
    const forceScan = opts?.forceScan === true;
    if (forceScan) setBusy("Scanner…");
    try {
      const q = new URLSearchParams({
        force_scan: forceScan ? "true" : "false",
        enrich_top: enrich ? "5" : "0",
      });
      const ctrl = new AbortController();
      const kill = window.setTimeout(() => ctrl.abort(), forceScan ? 120_000 : 20_000);
      const res = await fetch(`${API}/api/farm/opire?${q}`, { signal: ctrl.signal });
      window.clearTimeout(kill);
      if (!res.ok) throw new Error("opire_farm");
      const body = (await res.json()) as Panel;
      setData(body);
      setHiddenIds(new Set());
      setError("");
      const mm = body.scan?.money_mode;
      const n = body.scan?.scanned ?? 0;
      const hi = body.scan?.candidates?.length ?? 0;
      const sniped = body.scan?.sniper_skipped ?? 0;
      const probed = body.scan?.sniper_probed ?? 0;
      const excl = body.scan?.excluded_already_active ?? 0;
      setOpireLink(
        `Opire API: подключен · scanned ${n} · Money Mode ${hi}` +
          (mm?.hidden_count ? ` · скрыто ${mm.hidden_count}` : "") +
          (excl ? ` · уже взятых ${excl}` : "") +
          (probed
            ? ` · Sniper probed ${probed}` + (sniped ? `, dead ${sniped}` : "")
            : "") +
          ` (порог ${body.scan?.threshold ?? mm?.threshold ?? 80}%+)`,
      );
    } catch (e) {
      const aborted = e instanceof DOMException && e.name === "AbortError";
      if (aborted) {
        setError(
          "Scanner слишком долго отвечает — нажмите «Обновить Scanner» ещё раз.",
        );
        setOpireLink("Opire: timeout");
      } else {
        const probe = await probeBackendReachability(API);
        setError(
          probe.ok
            ? `Farm API ошибка при живом Backend (${API}/api/farm/opire). Обновите панель.`
            : probe.detail,
        );
        setOpireLink(
          probe.ok
            ? "Opire: backend жив, farm endpoint failed"
            : `Opire: ${probe.reason} · ${API}`,
        );
        if (!probe.ok) setData(null);
      }
    } finally {
      if (forceScan) setBusy("");
    }
  }, []);

  useEffect(() => {
    // Fast cache first; if empty — one live scan so Opire $ work appears.
    (async () => {
      await refresh({ enrich: false, forceScan: false });
    })();
    const t = window.setInterval(() => void refresh({ enrich: false, forceScan: false }), 90_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  // If cache was empty after first paint, show cached empty state.
  // Never auto force_scan — Sniper/git ls-remote freezes the пульт (user clicks Scanner).
  useEffect(() => {
    if (!data || autoLiveScanDone.current) return;
    autoLiveScanDone.current = true;
  }, [data]);

  // Block accidental github.com opens from Farm JS. Do NOT patch Location.assign/
  // replace/href — Chrome marks them read-only and throws (crashes the page).
  useEffect(() => {
    const report = (source: string, url: string, block: boolean) => {
      console.warn("[farm-engine][github-nav]", { source, url, block });
      if (block) {
        setInfo(
          `Заблокирован авто-переход на GitHub (${source}). ` +
            "Открывайте Issue/Repo только кнопкой «Открыть».",
        );
      }
    };

    const onClickCapture = (ev: MouseEvent) => {
      const t = ev.target;
      if (!(t instanceof Element)) return;
      const a = t.closest("a");
      if (!a) return;
      const href = a.getAttribute("href") || "";
      if (!href || !isGithubHost(href)) return;
      ev.preventDefault();
      ev.stopPropagation();
      report(`blocked bare <a href>`, href, true);
    };

    const origOpen = window.open.bind(window);
    try {
      window.open = ((url?: string | URL, ...rest: unknown[]) => {
        const s = String(url ?? "");
        if (s && isGithubHost(s)) {
          const armed = isGithubOpenArmed();
          if (!armed || isGithubAuthPath(s)) {
            report("window.open", s, true);
            return null;
          }
          disarmGithubOpen();
          report("window.open (armed user click)", s, false);
        }
        return origOpen(url as string | URL | undefined, ...(rest as [string?, string?]));
      }) as typeof window.open;
    } catch (e) {
      console.warn("[farm-engine] window.open patch skipped", e);
    }

    document.addEventListener("click", onClickCapture, true);
    return () => {
      document.removeEventListener("click", onClickCapture, true);
      try {
        window.open = origOpen;
      } catch {
        /* ignore */
      }
    };
  }, []);

  async function decide(id: string, decision: "approve" | "skip") {
    setBusy(decision === "approve" ? "Approve…" : "Skip…");
    setError("");
    setInfo(decision === "approve" ? "Approve → сохраняем и запускаем Execution…" : "Skip…");
    // Optimistic: remove card immediately so UI never looks frozen
    setHiddenIds((prev) => new Set(prev).add(id));
    setData((prev) => {
      if (!prev?.scan) return prev;
      const drop = (list?: Candidate[]) => (list || []).filter((c) => c.id !== id);
      return {
        ...prev,
        scan: {
          ...prev.scan,
          candidates: drop(prev.scan.candidates),
          candidates_take_all: drop(prev.scan.candidates_take_all),
          review_all: drop(prev.scan.review_all),
        },
      };
    });
    try {
      const q = new URLSearchParams({ reward_id: id, decision });
      const res = await fetch(`${API}/api/farm/opire/decide?${q}`, { method: "POST" });
      const body = await res.json().catch(() => ({}));
      if (body.auto_skipped) {
        setError("");
        setInfo(
          String(
            body.message_ru ||
              "Approve → Impossible (repo). Задача снята — берите следующую карточку.",
          ),
        );
        await refresh({ enrich: false, forceScan: false });
      } else if (!res.ok || body.ok === false) {
        setError(String(body.message_ru || body.error || `decide HTTP ${res.status}`));
        setInfo("");
        setHiddenIds((prev) => {
          const n = new Set(prev);
          n.delete(id);
          return n;
        });
        await refresh({ enrich: false, forceScan: false });
      } else {
        const auto = body.auto_started_execution === true;
        const queued = body.execution_queued === true;
        setInfo(
          String(
            body.message_ru ||
              (decision === "skip"
                ? "Skip — снято навсегда"
                : queued
                  ? "Approve → Execution в фоне. Смотрите «Активные bounty» ниже."
                    : auto
                    ? "Approve → 💻 Coding… Execution уже идёт. Смотрите Активные."
                    : "Approve → 🧠 Thinking… агент ставит Execution в очередь."),
          ),
        );
        await refresh({ enrich: false, forceScan: false });
        // If queued in background, poll once so timeline moves past QUEUED
        if (queued || auto) {
          window.setTimeout(() => void refresh({ enrich: false, forceScan: false }), 4000);
          window.setTimeout(() => void refresh({ enrich: false, forceScan: false }), 12000);
        }
      }
    } catch (e) {
      setError(`decide failed: ${e instanceof Error ? e.message : "network"}`);
      setInfo("");
      setHiddenIds((prev) => {
        const n = new Set(prev);
        n.delete(id);
        return n;
      });
      await refresh({ enrich: false, forceScan: false });
    } finally {
      setBusy("");
    }
  }

  async function advance(id: string, status: string) {
    setBusy(`Статус: ${status}…`);
    setError("");
    try {
      if (status === "payout_confirmed" || status === "withdraw") {
        const q = new URLSearchParams({
          reward_id: id,
          confirm_real: status === "payout_confirmed" ? "true" : "false",
        });
        const res = await fetch(`${API}/api/farm/opire/sync?${q}`, { method: "POST" });
        const body = await res.json().catch(() => ({}));
        if (!res.ok || body.ok === false) {
          setError(String(body.message_ru || body.error || "sync failed"));
        } else {
          setInfo(String(body.message_ru || "Синхронизировано"));
          await refresh({ enrich: false, forceScan: false });
        }
        return;
      }
      const q = new URLSearchParams({ reward_id: id, status });
      const res = await fetch(`${API}/api/farm/opire/advance?${q}`, { method: "POST" });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || body.ok === false) {
        setError(String(body.message_ru || body.error || "advance failed"));
      } else {
        setInfo(`Статус → ${status}`);
        await refresh({ enrich: false, forceScan: false });
      }
    } catch (e) {
      setError(`advance failed: ${e instanceof Error ? e.message : "network"}`);
    } finally {
      setBusy("");
    }
  }

  async function startExecution(id: string) {
    setBusy("Конвейер… (может занять минуты; при Impossible — Skip + следующая)");
    setError("");
    setInfo("Execution запущен…");
    try {
      const q = new URLSearchParams({ reward_id: id });
      const res = await fetch(`${API}/api/farm/opire/execute?${q}`, { method: "POST" });
      const body = await res.json().catch(() => ({}));
      const msg = String(body.message_ru || body.error || "");
      if (body.auto_skipped) {
        setInfo(msg || "Impossible → Skip → следующая");
        setError("");
        await refresh({ enrich: false, forceScan: false });
      } else if (!res.ok || body.ok === false) {
        setError(msg || "execution failed");
        setInfo("");
        await refresh({ enrich: false, forceScan: false });
      } else {
        setInfo(msg || "Draft PR Ready — нажмите Отправить");
        await refresh({ enrich: false, forceScan: false });
      }
    } catch (e) {
      setError(`execution failed: ${e instanceof Error ? e.message : "network"}`);
      setInfo("");
    } finally {
      setBusy("");
    }
  }

  async function ceoSubmit(id: string) {
    setBusy("Создание Draft PR через GitHub API…");
    setError("");
    setInfo("Отправка PR…");
    try {
      const q = new URLSearchParams({ reward_id: id });
      const res = await fetch(`${API}/api/farm/opire/submit?${q}`, { method: "POST" });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || body.ok === false) {
        setError(String(body.message_ru || body.error || "submit failed"));
        setInfo("");
      } else {
        const url = body.task?.pr_url || body.pr_url;
        setInfo(
          url
            ? `Draft PR создан: ${url}`
            : String(body.message_ru || "PR отправлен"),
        );
        await refresh({ enrich: false, forceScan: false });
      }
    } catch (e) {
      setError(`submit failed: ${e instanceof Error ? e.message : "network"}`);
      setInfo("");
    } finally {
      setBusy("");
    }
  }

  async function syncTask(id: string, confirmReal = false) {
    setBusy(confirmReal ? "REAL sync…" : "Синхронизация…");
    setError("");
    setInfo("Запрос sync к GitHub/Opire…");
    try {
      const q = new URLSearchParams({
        reward_id: id,
        confirm_real: confirmReal ? "true" : "false",
      });
      const res = await fetch(`${API}/api/farm/opire/sync?${q}`, { method: "POST" });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || body.ok === false) {
        setError(String(body.message_ru || body.error || "sync failed"));
        setInfo("");
      } else {
        setInfo(String(body.message_ru || "OK"));
        await refresh({ enrich: false, forceScan: false });
      }
    } catch (e) {
      setError(`sync failed: ${e instanceof Error ? e.message : "network"}`);
      setInfo("");
    } finally {
      setBusy("");
    }
  }

  const moneyPool = data?.scan?.candidates || [];
  const takeAll = data?.scan?.candidates_take_all || moneyPool;
  const candidates = (moneyMode ? moneyPool : takeAll).filter((c) => !hiddenIds.has(c.id));
  const reviewAll = data?.scan?.review_all || [];
  const bands = data?.scan?.confidence_bands || data?.funnel?.confidence_bands || {};
  const active = data?.active_tasks || [];
  const mmMeta = data?.scan?.money_mode;
  const marketNote =
    data?.scan?.market_live_note_ru ||
    (data?.scan?.market_live_count
      ? `Живой рынок Opire: ${data.scan.market_live_count} bounty с $`
      : "");

  const reviewFiltered = reviewAll.filter((c) => {
    const pct = Number(c.overall_confidence_pct || c.confidence_pct || 0);
    if (reviewBand === "80+") return pct >= 80;
    if (reviewBand === "60+") return pct >= 60;
    if (reviewBand === "40+") return pct >= 40;
    if (reviewBand === "20+") return pct >= 20;
    return true;
  });

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <header className="text-center">
        <p className="text-xs uppercase tracking-widest text-sky-300/80">
          Farm Engine · Opire Primary
        </p>
        <h1 className="mt-2 text-2xl font-bold text-white">Opire Control Center</h1>
        <p className="mt-2 text-sm text-genesis-muted">
          {data?.north_star_ru ||
            "Mission Control управляет Opire. Поиск и Approve — здесь. Сайт Opire не нужен для ежедневной работы."}
        </p>
        {data?.market_note_ru ? (
          <p className="mx-auto mt-2 max-w-2xl text-[11px] leading-relaxed text-amber-100/80">
            {data.market_note_ru}
          </p>
        ) : null}
        {opireLink ? (
          <p className="mt-2 text-[11px] text-sky-200/80">{opireLink}</p>
        ) : null}
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
            href="https://docs.opire.dev/overview/commands"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-sky-400/30 px-3 py-1.5 text-sky-100 hover:bg-sky-500/10"
          >
            Opire Commands ↗
          </a>
        </div>
        <div
          className={`mx-auto mt-4 max-w-2xl rounded-xl border px-3 py-2 text-left text-[11px] leading-relaxed ${
            data?.readiness?.github_token_ready
              ? "border-emerald-500/30 bg-emerald-950/30 text-emerald-100"
              : "border-amber-500/35 bg-amber-950/30 text-amber-100"
          }`}
          data-farm-auth-mode="pat"
        >
          <p className="font-semibold tracking-wide">
            GitHub auth · PAT mode (не OAuth) · без окон GCM
          </p>
          <p className="mt-1 opacity-90">
            Farm Engine <strong>не</strong> вызывает GitHub OAuth в браузере. API — через{" "}
            <code className="rounded bg-black/30 px-1">GITHUB_TOKEN</code> в{" "}
            <code className="rounded bg-black/30 px-1">.env.local</code>.
            {data?.readiness?.github_token_ready
              ? " Токен на месте — Approve → Execute → Draft PR без окна GitHub."
              : " Токен не найден — добавьте GITHUB_TOKEN и перезапустите Genesis.exe."}
          </p>
          <p className="mt-1 opacity-80">
            Окно <strong>Select an account</strong> / аккаунт <code className="rounded bg-black/30 px-1">x-access-token</code>{" "}
            открывал Windows <strong>Git Credential Manager</strong> при скане Farm (
            <code className="rounded bg-black/30 px-1">git ls-remote</code>
            ). Это исправлено: Farm git больше не вызывает интерактивный GCM. Перезапустите
            backend/Genesis.exe, закройте старые окна GitHub, снова откройте Farm.
          </p>
        </div>
      </header>

      <FarmAccountPermissions accounts={accounts} onChange={setAccounts} />

      {opireLink ? (
        <p className="rounded-lg border border-sky-500/25 bg-sky-950/20 px-3 py-2 text-xs text-sky-100">
          {opireLink}
        </p>
      ) : null}
      {busy ? (
        <p className="rounded-lg border border-violet-500/40 bg-violet-950/30 px-3 py-2 text-sm font-medium text-violet-100">
          ▶ {busy}
        </p>
      ) : null}
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

      {data?.folders ? (
        <section className="grid grid-cols-3 gap-2">
          {(
            [
              ["new", data.folders.new],
              ["active", data.folders.active],
              ["archive", data.folders.archive],
            ] as const
          ).map(([key, folder]) => (
            <div
              key={key}
              className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3 text-center"
            >
              <p className="text-[10px] uppercase tracking-wider text-zinc-500">
                {folder?.label_ru || key}
              </p>
              <p className="mt-1 text-2xl font-semibold text-white">{folder?.count ?? 0}</p>
              <p className="mt-1 text-[10px] text-zinc-500">{folder?.hint_ru}</p>
            </div>
          ))}
          {(data.skipped_forever_count ?? 0) > 0 ? (
            <p className="col-span-3 text-[11px] text-zinc-500">
              Seen Ledger: {data.seen_ledger_count ?? 0} · Skip навсегда:{" "}
              {data.skipped_forever_count} (не вернутся в Scanner / Review All)
            </p>
          ) : (
            <p className="col-span-3 text-[11px] text-zinc-500">
              Skip = SKIPPED_PERMANENT. Scanner показывает только новые / нерешённые bounty.
            </p>
          )}
        </section>
      ) : null}

      {data?.income_contours ? (
        <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <h2 className="text-sm font-semibold text-white">
            {data.income_contours.title_ru || "Три контура дохода"}
          </h2>
          <p className="mt-1 text-[11px] text-genesis-muted">
            {data.income_contours.note_ru}
          </p>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {(data.income_contours.farms || []).map((f) => (
              <Link
                key={f.id}
                href={f.href || "/farm-engine"}
                className={`rounded-lg border px-3 py-2 text-left text-xs hover:bg-white/5 ${
                  f.id === "opire_farm"
                    ? "border-sky-400/40 bg-sky-950/30"
                    : f.mode === "paper"
                      ? "border-amber-400/35 bg-amber-950/20"
                      : "border-white/10"
                }`}
              >
                <p className="font-semibold text-white">
                  {f.label}
                  {f.mode === "paper" ? (
                    <span className="ml-1 text-[10px] font-normal text-amber-200">· PAPER</span>
                  ) : null}
                </p>
                <p className="mt-1 text-[10px] text-zinc-400">{f.role_ru}</p>
                {f.primary_kpi ? (
                  <p className="mt-1 text-[10px] text-amber-100/80">KPI: {f.primary_kpi}</p>
                ) : null}
                {f.honesty_ru ? (
                  <p className="mt-1 text-[10px] leading-snug text-amber-100/70">{f.honesty_ru}</p>
                ) : null}
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {data?.pipeline || data?.payout_success ? (
        <section className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4">
          <h2 className="text-sm font-semibold text-emerald-100">Pipeline · единственный KPI</h2>
          <p className="mt-1 text-[11px] text-emerald-100/70">
            {data.pipeline?.note_ru ||
              "Found → Approved → Started → Draft PR → Merged → Paid. Пока Started=0 — Execution не запущен."}
          </p>
          {Number(data.pipeline?.started ?? data.payout_success?.executed ?? 0) === 0 ? (
            <p className="mt-2 rounded border border-amber-400/40 bg-amber-950/30 px-2 py-1.5 text-[11px] text-amber-100">
              {data.pipeline?.blocker_ru ||
                "Started = 0 — нажмите Approve (не Skip). Skip не запускает Execution."}
            </p>
          ) : null}
          <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-6">
            {(
              [
                ["Found", data.pipeline?.found ?? data.payout_success?.found],
                ["Approved", data.pipeline?.approved ?? data.payout_success?.approved],
                ["Started", data.pipeline?.started ?? data.payout_success?.executed],
                ["Draft PR", data.pipeline?.draft_pr ?? data.payout_success?.draft_pr],
                ["Merged", data.pipeline?.merged ?? data.payout_success?.merged],
                ["Paid", data.pipeline?.paid ?? data.payout_success?.paid],
              ] as const
            ).map(([label, val]) => (
              <div
                key={label}
                className={`rounded-lg border px-2 py-1.5 ${
                  label === "Started" && Number(val ?? 0) === 0
                    ? "border-amber-400/40 bg-amber-950/20"
                    : "border-white/10 bg-black/20"
                }`}
              >
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</p>
                <p
                  className={`text-sm font-semibold tabular-nums ${
                    label === "Paid" || label === "Merged"
                      ? "text-emerald-200"
                      : label === "Started"
                        ? "text-sky-200"
                        : "text-white"
                  }`}
                >
                  {val ?? 0}
                </p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {data?.capability_matrix?.matrix?.length ? (
        <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <h2 className="text-sm font-semibold text-white">Capability Matrix · Opire</h2>
          <p className="mt-1 text-[11px] text-genesis-muted">
            {data.capability_matrix.note_ru ||
              "Что Virtus может брать автоматически (не путать с Alpha Hunter)."}
          </p>
          <ul className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
            {data.capability_matrix.matrix.map((row) => (
              <li
                key={row.id}
                className="rounded-full border border-white/10 px-2.5 py-1 text-zinc-300"
                title={row.note_ru || row.label}
              >
                {row.auto || "✅"} {row.label}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {data?.readiness ? (
        <section className="rounded-xl border border-amber-500/25 bg-amber-950/15 p-4 text-sm">
          <h2 className="text-sm font-semibold text-white">Статус (зафиксировано)</h2>
          <p className="mt-2 text-[12px] leading-relaxed text-amber-50/90">
            {data.readiness.summary_ru}
          </p>
          <ul className="mt-3 space-y-1.5">
            {(data.readiness.rows || []).map((row) => (
              <li
                key={row.component}
                className="flex flex-wrap items-baseline justify-between gap-2 border-b border-white/5 py-1 text-[11px]"
              >
                <span className="text-zinc-200">
                  {row.mark} {row.component}
                </span>
                <span className="text-genesis-muted">
                  {row.detail_ru || row.status}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[11px] text-sky-100/80">{data.readiness.next_proof_ru}</p>
        </section>
      ) : null}

      {data?.proof ? (
        <section
          className={`rounded-xl border p-4 text-sm ${
            data.proof.proof_status === "VERIFIED"
              ? "border-emerald-500/35 bg-emerald-950/20"
              : "border-white/10 bg-white/[0.03]"
          }`}
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold text-white">Farm Engine Proof</h2>
            <p
              className={`text-xs font-semibold ${
                data.proof.proof_status === "VERIFIED"
                  ? "text-emerald-200"
                  : "text-amber-100"
              }`}
            >
              {data.proof.proof_mark}
            </p>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {(
              [
                ["Tasks Analysed", data.proof.tasks_analysed],
                ["Approved", data.proof.approved],
                ["Executed", data.proof.executed],
                ["Draft PR", data.proof.draft_pr],
                ["Submitted", data.proof.submitted],
                ["Merged", data.proof.merged],
                ["Reward Confirmed", data.proof.reward_confirmed],
                ["Payout Confirmed", data.proof.payout_confirmed],
              ] as const
            ).map(([label, val]) => (
              <div key={label} className="rounded-lg border border-white/10 bg-black/25 px-2.5 py-2">
                <p className="text-[10px] text-genesis-muted">{label}</p>
                <p className="text-base font-semibold text-white">{val ?? 0}</p>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] text-genesis-muted">{data.proof.criterion_ru}</p>
          <p className="mt-1 text-[12px] text-zinc-200">{data.proof.message_ru}</p>
        </section>
      ) : null}

      <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
        <h2 className="text-sm font-semibold text-white">Connectors (roadmap)</h2>
        <p className="mt-1 text-[11px] text-genesis-muted">
          Сейчас в работе только <span className="text-emerald-200">Opire · live</span>.
          Polar / Algora / GitHub — после идеального Opire. Tier B/C не смешиваются.
        </p>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {(data?.connectors || [])
            .filter((c) => c.id === "opire" || c.tier === "A")
            .map((c) => {
            const st = c.runtime_status || c.status || "?";
            const tone =
              st === "live"
                ? "border-emerald-500/30 text-emerald-100"
                : "border-white/10 text-zinc-400";
            return (
              <li
                key={c.id}
                className={`rounded-lg border bg-black/20 px-3 py-2 ${tone}`}
              >
                <div className="flex items-baseline justify-between gap-2">
                  <p className="font-medium text-white">{c.display_name || c.id}</p>
                  <p className="text-[10px] uppercase tracking-wide">
                    Tier {c.tier} · {st}
                  </p>
                </div>
                <p className="mt-1 text-[11px] text-genesis-muted">{c.notes_ru}</p>
              </li>
            );
          })}
        </ul>
      </section>

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
                ["Execution", data.funnel.executed],
                ["Готово к Submit", data.funnel.execution_ready_for_submit],
                ["PR отправлено", data.funnel.pr_submitted],
                ["PR принято", data.funnel.pr_merged],
                ["После правок", data.funnel.pr_changes_requested],
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
        {data?.execution_success ? (
          <div className="mt-3 rounded-lg border border-sky-500/25 bg-sky-950/20 p-3">
            <p className="text-xs font-semibold text-sky-100">Execution Success Rate</p>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-5 text-xs">
              {(
                [
                  ["Approved", data.execution_success.approved],
                  ["Started", data.execution_success.started],
                  ["Execution", data.execution_success.execution ?? data.execution_success.started],
                  ["Completed", data.execution_success.completed],
                  ["Failed", data.execution_success.failed],
                  ["Skipped", data.execution_success.skipped],
                  ["Draft PR", data.execution_success.draft_pr],
                ] as const
              ).map(([label, val]) => (
                <div key={label}>
                  <p className="text-[10px] text-zinc-500">{label}</p>
                  <p className="font-semibold text-white">{val ?? 0}</p>
                </div>
              ))}
            </div>
            <p className="mt-2 text-[10px] text-zinc-400">
              Start rate:{" "}
              {data.execution_success.start_rate != null
                ? `${Math.round(data.execution_success.start_rate * 100)}%`
                : "—"}
              {" · "}
              Complete rate:{" "}
              {data.execution_success.complete_rate != null
                ? `${Math.round(data.execution_success.complete_rate * 100)}%`
                : "—"}
              {" · "}
              Avg execution:{" "}
              {data.execution_success.avg_execution_s != null
                ? `${data.execution_success.avg_execution_s}s`
                : "—"}
            </p>
            {data.execution_success.note_ru ? (
              <p className="mt-1 text-[10px] text-sky-100/80">{data.execution_success.note_ru}</p>
            ) : null}
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
          disabled={Boolean(busy)}
          onClick={() => void refresh({ enrich: false, forceScan: true })}
          className="mt-3 rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5 disabled:opacity-40"
        >
          Обновить Scanner
        </button>
      </section>

      {data?.scan?.analytics ? (
        <section className="space-y-4 rounded-xl border border-violet-500/20 bg-violet-950/10 p-4 text-sm">
          <div>
            <h2 className="text-sm font-semibold text-white">Scan Analytics</h2>
            <p className="mt-1 text-[11px] text-genesis-muted">
              {data.scan.analytics.north_star_ru ||
                "Статистика скана — где узкое место. Potential ≠ REAL payout."}
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">Языки</p>
              <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto text-xs text-zinc-300">
                {(data.scan.analytics.languages || []).slice(0, 12).map((r) => (
                  <li key={r.name} className="flex justify-between gap-2">
                    <span>{r.name}</span>
                    <span className="text-white">{r.count}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                Почему отказ
              </p>
              <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto text-xs text-zinc-300">
                {(data.scan.analytics.reject_reasons || []).slice(0, 12).map((r) => (
                  <li key={r.reason} className="flex justify-between gap-2">
                    <span>{r.reason}</span>
                    <span className="text-amber-100">{r.count}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                Potential Reward
              </p>
              <ul className="mt-2 space-y-1.5 text-xs text-zinc-300">
                {(
                  [
                    ["high", data.scan.analytics.potential_reward?.high],
                    ["medium", data.scan.analytics.potential_reward?.medium],
                    ["low", data.scan.analytics.potential_reward?.low],
                  ] as const
                ).map(([key, block]) => (
                  <li key={key} className="rounded-lg border border-white/10 bg-black/20 px-2 py-1.5">
                    <span className="text-zinc-500">{block?.label || key}</span>
                    <p className="font-semibold text-white">
                      ${Number(block?.usd || 0).toFixed(0)}
                      <span className="ml-2 text-[10px] font-normal text-zinc-500">
                        n={block?.count ?? 0}
                      </span>
                    </p>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-[10px] text-zinc-600">
                {data.scan.analytics.potential_reward?.note_ru}
              </p>
            </div>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">
              Capability Coverage ·{" "}
              {data.scan.analytics.capability_coverage?.coverage_pct ?? "—"}%
            </p>
            <ul className="mt-2 space-y-2">
              {(data.scan.analytics.capability_coverage?.rows || [])
                .slice(0, 10)
                .map((r) => (
                  <li key={r.capability} className="text-xs">
                    <div className="mb-0.5 flex justify-between gap-2 text-zinc-300">
                      <span>
                        {r.capability}
                        {!r.covered ? (
                          <span className="ml-2 text-amber-200">
                            lost {r.lost_bounties}
                          </span>
                        ) : null}
                      </span>
                      <span>{r.coverage_pct}%</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                      <div
                        className={`h-full rounded-full ${
                          r.covered ? "bg-emerald-400/80" : "bg-rose-400/50"
                        }`}
                        style={{ width: `${Math.max(4, r.coverage_pct)}%` }}
                      />
                    </div>
                  </li>
                ))}
            </ul>
          </div>
          {(data.scan.analytics.top_roi || []).length > 0 ? (
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                Top ROI (стоит ли делать)
              </p>
              <ul className="mt-2 max-h-48 space-y-1.5 overflow-y-auto text-xs text-zinc-300">
                {(data.scan.analytics.top_roi || []).map((r, i) => (
                  <li
                    key={`${r.title}-${i}`}
                    className="flex flex-wrap items-baseline justify-between gap-2 rounded-lg border border-white/10 bg-black/20 px-2 py-1.5"
                  >
                    <span className="min-w-0 flex-1 truncate">{r.title}</span>
                    <span className="shrink-0 text-amber-100">
                      {r.roi_label || "⭐"}
                    </span>
                    <span className="shrink-0 text-emerald-200">
                      ${Number(r.reward_usd || 0).toFixed(0)}
                    </span>
                    <span className="shrink-0 text-zinc-500">
                      ~{Number(r.estimated_minutes || 0).toFixed(0)} мин
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}

      {data?.learning_ledger ? (
        <section className="space-y-3 rounded-xl border border-amber-500/20 bg-amber-950/10 p-4 text-sm">
          <div>
            <h2 className="text-sm font-semibold text-white">Learning Ledger</h2>
            <p className="mt-1 text-[11px] text-genesis-muted">
              {data.learning_ledger.note_ru ||
                "После каждого bounty: win/lose, время, ревью, payout."}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {(
              [
                ["Closed", data.learning_ledger.closed],
                ["Wins", data.learning_ledger.wins],
                ["Losses", data.learning_ledger.losses],
                ["Earned $", data.learning_ledger.earned_usd],
              ] as const
            ).map(([label, val]) => (
              <div
                key={label}
                className="rounded-lg border border-white/10 bg-black/20 px-2 py-1.5"
              >
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                  {label}
                </p>
                <p className="text-sm font-semibold text-white">{val ?? 0}</p>
              </div>
            ))}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                Почему выиграли
              </p>
              <ul className="mt-2 max-h-32 space-y-1 overflow-y-auto text-xs text-zinc-300">
                {(data.learning_ledger.why_won || []).length === 0 ? (
                  <li className="text-zinc-600">Пока нет win — ждём первый payout.</li>
                ) : (
                  (data.learning_ledger.why_won || []).map((r) => (
                    <li key={r.reason} className="flex justify-between gap-2">
                      <span>{r.reason}</span>
                      <span>{r.count}</span>
                    </li>
                  ))
                )}
              </ul>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                Почему проиграли
              </p>
              <ul className="mt-2 max-h-32 space-y-1 overflow-y-auto text-xs text-zinc-300">
                {(data.learning_ledger.why_lost || []).length === 0 ? (
                  <li className="text-zinc-600">Пока пусто.</li>
                ) : (
                  (data.learning_ledger.why_lost || []).map((r) => (
                    <li key={r.reason} className="flex justify-between gap-2">
                      <span className="truncate">{r.reason}</span>
                      <span>{r.count}</span>
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
          {(data.learning_ledger.recent || []).length > 0 ? (
            <ul className="space-y-1.5 text-xs text-zinc-300">
              {(data.learning_ledger.recent || []).slice(0, 6).map((r, i) => (
                <li
                  key={`${r.title}-${i}`}
                  className="rounded-lg border border-white/10 bg-black/20 px-2 py-1.5"
                >
                  <span
                    className={
                      r.outcome === "win"
                        ? "text-emerald-200"
                        : "text-rose-200/90"
                    }
                  >
                    {r.outcome === "win" ? "WIN" : String(r.outcome || "lose").toUpperCase()}
                  </span>
                  <span className="ml-2 text-white">{r.title}</span>
                  {r.outcome === "win" ? (
                    <span className="ml-2 text-emerald-200">
                      +${Number(r.earned_usd || 0).toFixed(0)}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      <section className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold text-white">
              {moneyMode ? "Money Mode · Approve / Skip" : "All TAKE · Approve / Skip"}
            </h2>
            <p className="mt-1 text-[11px] text-genesis-muted">
              {mmMeta?.note_ru ||
                "Только bounty с высоким шансом довести до Draft PR / Merge."}
            </p>
            {marketNote ? (
              <p className="mt-1 text-[11px] text-emerald-200/85">{marketNote}</p>
            ) : null}
            {data?.scan?.from_cache ? (
              <p className="mt-1 text-[11px] text-zinc-500">
                Кэш последнего скана · «Обновить Scanner» = live api.opire.dev
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => setMoneyMode((v) => !v)}
            className={`rounded-lg border px-3 py-1.5 text-xs ${
              moneyMode
                ? "border-emerald-400/40 bg-emerald-950/40 text-emerald-100"
                : "border-white/15 text-zinc-300"
            }`}
          >
            Money Mode {moneyMode ? "ON" : "OFF"}
            {mmMeta?.count != null ? ` · ${mmMeta.count}` : ""}
            {mmMeta?.hidden_count ? ` · +${mmMeta.hidden_count} в All` : ""}
          </button>
        </div>
        {candidates.length === 0 ? (
          <p className="rounded-lg border border-white/10 bg-black/20 px-3 py-4 text-sm text-genesis-muted">
            Нет новых кандидатов выше порога.
            {(data?.scan?.excluded_already_active ?? 0) > 0
              ? ` Уже в работе/пропущено: ${data?.scan?.excluded_already_active}.`
              : ""}
            {(data?.scan?.sniper_skipped ?? 0) > 0
              ? ` Sniper отсеял мёртвые repo: ${data?.scan?.sniper_skipped}.`
              : ""}{" "}
            🔍 Researching… Scanner сам подтянет другие Opire bounty (или Skip активные с 404).
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
                    <ExternalOpenButton
                      href={c.url || ""}
                      className="font-medium text-white hover:underline"
                    >
                      {c.title}
                    </ExternalOpenButton>
                    <p className="mt-0.5 text-[11px] text-genesis-muted">
                      <span className="text-sky-200">{c.platform || "opire"}</span>
                      {(c.also_on || []).length
                        ? ` (+${(c.also_on || []).join(", ")})`
                        : ""}{" "}
                      · {c.repository} · #{c.issue_id} ·{" "}
                      {(c.languages || []).join(", ") || "lang?"}
                      {c.bot_installed ? " · Opire bot" : ""}
                    </p>
                  </div>
                  <p className="text-lg font-semibold text-emerald-200">
                    ${c.reward_usd?.toFixed(0)}
                  </p>
                </div>
                <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-sky-100/80">
                  <span className="font-semibold text-amber-100">
                    ROI {c.roi_label || "—"}
                    {c.roi_usd_per_hour != null
                      ? ` · $${Number(c.roi_usd_per_hour).toFixed(0)}/h`
                      : ""}
                  </span>
                  <span className="font-semibold text-emerald-100">
                    Overall Success{" "}
                    {c.overall_success_probability_pct ??
                      c.success_probability_pct ??
                      c.overall_confidence_pct}
                    %
                  </span>
                  <span>Confidence {c.overall_confidence_pct}%</span>
                  <span>Acceptance {c.acceptance_pct}%</span>
                  <span>
                    ~
                    {c.estimated_minutes != null
                      ? `${Number(c.estimated_minutes).toFixed(0)} мин`
                      : `${c.estimated_hours}h`}
                  </span>
                  <span>Risk {c.risk}</span>
                  <span>Difficulty {c.difficulty || "—"}</span>
                  <span>Competitors {c.competitors}</span>
                  <span
                    className={
                      c.recommendation === "SKIP"
                        ? "font-semibold text-rose-200"
                        : c.recommendation === "TAKE"
                          ? "font-semibold text-emerald-200"
                          : "font-semibold text-amber-200"
                    }
                  >
                    {c.recommendation === "SKIP"
                      ? "❌ SKIP"
                      : c.recommendation === "TAKE"
                        ? "✅ TAKE"
                        : `⚠ ${c.recommendation || "REVIEW"}`}
                  </span>
                  <span
                    className={
                      c.repo_status === "ok"
                        ? "text-emerald-200/90"
                        : c.repo_status === "unreachable" ||
                            c.repo_status === "auth_required"
                          ? "font-semibold text-rose-200"
                          : "text-genesis-muted"
                    }
                  >
                    {c.repo_status === "ok"
                      ? "repo: OK"
                      : c.repo_status === "unreachable"
                        ? "repo: unreachable"
                        : c.repo_status === "auth_required"
                          ? "repo: auth required"
                          : c.repo_status
                            ? `repo: ${c.repo_status}`
                            : "repo: —"}
                  </span>
                </div>
                {c.preflight?.checks?.length ? (
                  <div className="mt-2 rounded-lg border border-white/10 bg-black/25 px-3 py-2">
                    <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                      Pre-flight{" "}
                      <span
                        className={
                          c.preflight.verdict === "GO"
                            ? "font-semibold text-emerald-200"
                            : c.preflight.verdict === "SKIP"
                              ? "font-semibold text-rose-200"
                              : "font-semibold text-amber-100"
                        }
                      >
                        {c.preflight.verdict || "—"}
                      </span>
                      {c.task_type ? (
                        <span className="ml-2 text-zinc-400">· {c.task_type}</span>
                      ) : null}
                    </p>
                    <ul className="mt-1.5 grid gap-0.5 sm:grid-cols-2">
                      {c.preflight.checks.map((item) => (
                        <li
                          key={item.id}
                          className={`text-[11px] ${
                            item.ok ? "text-emerald-200/90" : "text-zinc-500"
                          }`}
                        >
                          {item.mark || (item.ok ? "✓" : "○")} {item.label}
                          {item.detail ? (
                            <span className="text-zinc-600"> · {item.detail}</span>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {c.success_checklist?.length ? (
                  <div className="mt-2 rounded-lg border border-white/10 bg-black/25 px-3 py-2">
                    <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                      Overall Success Probability{" "}
                      <span className="font-semibold text-emerald-200">
                        {c.overall_success_probability_pct ??
                          c.success_probability_pct ??
                          c.overall_confidence_pct}
                        %
                      </span>
                    </p>
                    <ul className="mt-1.5 grid gap-0.5 sm:grid-cols-2">
                      {c.success_checklist.map((item) => (
                        <li
                          key={item.id}
                          className={`text-[11px] ${
                            item.ok ? "text-emerald-200/90" : "text-zinc-500"
                          }`}
                        >
                          {item.ok ? "✓" : "○"} {item.label}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {c.sniper_detail_ru ? (
                  <p className="mt-2 text-[11px] text-rose-200/90">{c.sniper_detail_ru}</p>
                ) : null}
                {c.issue_analysis?.summary_ru ? (
                  <p className="mt-2 text-[11px] text-zinc-300">{c.issue_analysis.summary_ru}</p>
                ) : null}
                {c.issue_body_preview ? (
                  <p className="mt-1 max-h-16 overflow-hidden text-[10px] text-genesis-muted">
                    {c.issue_body_preview}
                  </p>
                ) : null}
                <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
                  {c.ceo_action_links?.issue ? (
                    <ExternalOpenButton
                      href={c.ceo_action_links.issue}
                      title="Открывает github.com только после клика — не вход в Farm"
                      className="rounded border border-white/15 px-2 py-0.5 text-sky-200 hover:bg-white/5"
                    >
                      Issue ↗
                    </ExternalOpenButton>
                  ) : null}
                  {c.ceo_action_links?.repository ? (
                    <ExternalOpenButton
                      href={c.ceo_action_links.repository}
                      title="Открывает github.com только после клика — не OAuth Farm"
                      className="rounded border border-white/15 px-2 py-0.5 text-sky-200 hover:bg-white/5"
                    >
                      Repo ↗
                    </ExternalOpenButton>
                  ) : null}
                  <button
                    type="button"
                    className="rounded border border-amber-400/30 px-2 py-0.5 text-amber-100"
                    onClick={() => {
                      void navigator.clipboard.writeText(
                        c.ceo_action_links?.try_comment_text || "/try",
                      );
                      setInfo("Скопировано: /try — вставьте новым комментарием на Issue");
                    }}
                  >
                    Copy /try
                  </button>
                  <button
                    type="button"
                    className="rounded border border-amber-400/30 px-2 py-0.5 text-amber-100"
                    onClick={() => {
                      void navigator.clipboard.writeText(
                        c.ceo_action_links?.claim_pr_text ||
                          `/claim #${c.issue_id || "N"}`,
                      );
                      setInfo("Скопировано: /claim — в тело PR при Submit");
                    }}
                  >
                    Copy /claim
                  </button>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={
                      Boolean(busy) ||
                      c.repo_status === "unreachable" ||
                      (c.blockers || []).includes("repo_unreachable") ||
                      (c.blockers || []).includes("missing_repo")
                    }
                    title={
                      moneyMode && c.money_mode_eligible === false
                        ? "Money Mode soft-warn: Approve всё равно запускает Execution"
                        : c.preflight?.approve_allowed === false
                          ? "Preflight soft-warn — backend может отклонить"
                          : "Approve → lock → Execution Engine"
                    }
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
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold text-white">Review All · почему отклонили</h2>
            <p className="mt-1 text-[11px] text-genesis-muted">
              Все найденные bounty (не только TAKE). Смотрите blockers / reject_reasons — так видно,
              строгий порог или реально неподходящие задачи.
            </p>
          </div>
          <div className="flex flex-wrap gap-1">
            {(["all", "80+", "60+", "40+", "20+"] as const).map((b) => (
              <button
                key={b}
                type="button"
                onClick={() => setReviewBand(b)}
                className={`rounded-lg border px-2 py-1 text-[11px] ${
                  reviewBand === b
                    ? "border-sky-400/50 bg-sky-950/40 text-sky-100"
                    : "border-white/10 text-zinc-400 hover:bg-white/5"
                }`}
              >
                {b === "all" ? `All (${bands.all ?? reviewAll.length})` : `${b} (${bands[b] ?? "—"})`}
              </button>
            ))}
          </div>
        </div>
        {reviewFiltered.length === 0 ? (
          <p className="rounded-lg border border-white/10 bg-black/20 px-3 py-3 text-sm text-genesis-muted">
            Пусто в этом диапазоне. Обновите Scanner.
          </p>
        ) : (
          <ul className="max-h-[28rem] space-y-2 overflow-y-auto">
            {reviewFiltered.map((c) => {
              const reasons = [
                ...new Set([...(c.reject_reasons || []), ...(c.blockers || [])]),
              ];
              const pct = c.overall_confidence_pct ?? c.confidence_pct ?? 0;
              return (
                <li
                  key={`review-${c.id}`}
                  className="rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-sm"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <ExternalOpenButton
                        href={c.url || ""}
                        className="font-medium text-white hover:underline"
                      >
                        {c.title || c.id}
                      </ExternalOpenButton>
                      <p className="mt-0.5 text-[11px] text-genesis-muted">
                        {pct}% · ROI {c.roi_label || "—"} · {c.recommendation || "?"} · $
                        {Number(c.reward_usd || 0).toFixed(0)} ·{" "}
                        {(c.languages || []).join(", ") || "lang?"}
                      </p>
                      {reasons.length > 0 ? (
                        <p className="mt-1 text-[11px] text-amber-100/90">
                          Почему не TAKE: {reasons.join(" · ")}
                        </p>
                      ) : (
                        <p className="mt-1 text-[11px] text-emerald-200/80">
                          Без blockers — можно Approve из High-confidence или ниже.
                        </p>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <button
                        type="button"
                        disabled={Boolean(busy)}
                        onClick={() => void decide(c.id, "approve")}
                        className="rounded border border-emerald-400/40 px-2 py-1 text-[11px] text-emerald-100 disabled:opacity-40"
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        disabled={Boolean(busy)}
                        onClick={() => void decide(c.id, "skip")}
                        className="rounded border border-white/15 px-2 py-1 text-[11px] text-zinc-300 disabled:opacity-40"
                      >
                        Skip
                      </button>
                    </div>
                  </div>
                </li>
              );
            })}
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
                      {t.repository} · pipeline{" "}
                      <span className="font-semibold text-amber-100">
                        {t.pipeline_state || t.pipeline_label || t.status || "—"}
                      </span>
                      {" · "}
                      status <span className="text-sky-200">{t.status}</span> ·
                      repo{" "}
                      <span
                        className={
                          t.repo_status === "ok"
                            ? "text-emerald-200"
                            : t.repo_status === "unreachable" ||
                                t.repo_status === "auth_required"
                              ? "text-rose-200"
                              : "text-sky-200"
                        }
                      >
                        {t.repo_status || "—"}
                      </span>{" "}
                      · est ${t.estimated_reward_usd ?? t.reward_usd} · REAL{" "}
                      {t.real_income ? "yes" : "no"}
                    </p>
                    {t.opire_commands ? (
                      <p className="mt-1 font-mono text-[11px] text-amber-100/80">
                        {t.opire_commands.try} → PR body: {t.opire_commands.claim}
                      </p>
                    ) : null}
                  </div>
                  <ExternalOpenButton
                    href={t.url || ""}
                    className="text-xs text-sky-300 hover:underline"
                  >
                    Issue ↗
                  </ExternalOpenButton>
                </div>
                <FarmExecutionTimeline
                  task={t}
                  githubTokenReady={data?.readiness?.github_token_ready}
                />
                {t.execution?.ready_for_ceo?.message_ru ? (
                  <p className="mt-2 text-[11px] text-emerald-100/90">
                    {t.execution.ready_for_ceo.message_ru}
                    {t.execution.branch ? ` · branch ${t.execution.branch}` : ""}
                    {t.execution.ready_for_ceo.route
                      ? ` · route ${t.execution.ready_for_ceo.route}`
                      : ""}
                  </p>
                ) : null}
                {t.execution_estimate ? (
                  <p className="mt-1 text-[11px] text-sky-100/80">
                    Оценка: P(success) {t.execution_estimate.success_probability_pct}% · ~
                    {t.execution_estimate.estimated_hours}h · reward $
                    {t.execution_estimate.reward_usd} (estimated)
                  </p>
                ) : null}
                {t.execution_error &&
                !String(t.execution_error).startsWith("zombie_queued") &&
                t.execution_error !== "factory_busy" ? (
                  <p className="mt-2 text-[11px] text-rose-200">
                    Execution error: {t.execution_error}
                  </p>
                ) : null}
                {t.execution_heal && !t.execution_error ? (
                  <p className="mt-2 text-[11px] text-amber-100/90">
                    Очередь сброшена ({t.execution_heal}). 🧠 Thinking… агент
                    перезапускает Execution сам
                    {t.auto_retry_execution ? " (в фоне)" : ""}.
                  </p>
                ) : null}
                {t.execution?.error_detail && !t.execution_error ? (
                  <p className="mt-2 text-[11px] text-rose-200">
                    {t.execution.error_detail}
                  </p>
                ) : null}
                {t.ceo_action_links ? (
                  <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
                    {t.ceo_action_links.issue ? (
                      <ExternalOpenButton
                        href={t.ceo_action_links.issue}
                        className="rounded border border-white/15 px-2 py-0.5 text-sky-200"
                      >
                        Issue
                      </ExternalOpenButton>
                    ) : null}
                    {t.ceo_action_links.repository ? (
                      <ExternalOpenButton
                        href={t.ceo_action_links.repository}
                        className="rounded border border-white/15 px-2 py-0.5 text-sky-200"
                      >
                        Repo
                      </ExternalOpenButton>
                    ) : null}
                    <button
                      type="button"
                      className="rounded border border-amber-400/30 px-2 py-0.5 text-amber-100"
                      onClick={() => {
                        void navigator.clipboard.writeText(
                          t.ceo_action_links?.try_comment_text || "/try",
                        );
                        setInfo("Скопировано /try");
                      }}
                    >
                      Copy /try
                    </button>
                    <button
                      type="button"
                      className="rounded border border-amber-400/30 px-2 py-0.5 text-amber-100"
                      onClick={() => {
                        void navigator.clipboard.writeText(
                          t.ceo_action_links?.claim_pr_text ||
                            t.opire_commands?.claim ||
                            "/claim",
                        );
                        setInfo("Скопировано /claim");
                      }}
                    >
                      Copy /claim
                    </button>
                  </div>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-2">
                  {t.status === "ceo_approved" ||
                  t.status === "executing" ||
                  taskNeedsResearchRetry(t) ? (
                    <button
                      type="button"
                      disabled={
                        Boolean(busy) ||
                        t.repo_status === "unreachable" ||
                        (t.blockers || []).includes("repo_unreachable") ||
                        (t.blockers || []).includes("missing_repo")
                      }
                      onClick={() => void startExecution(t.id)}
                      className="rounded-lg bg-sky-500/90 px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-40"
                      title={
                        t.repo_status === "unreachable"
                          ? "Sniper: репозиторий недоступен — Execution заблокирован"
                          : taskNeedsResearchRetry(t)
                            ? "Повторить Research Agent + Codex (нужен перезапуск после обновления кода)"
                            : undefined
                      }
                    >
                      {taskNeedsResearchRetry(t)
                        ? "🔄 Fixing… Run снова"
                        : t.status === "ceo_approved"
                          ? t.execution_heal || t.auto_retry_execution
                            ? "🧠 Thinking… (авто-повтор)"
                            : "💻 Coding… (если не стартовал — повторить)"
                          : "💻 Coding… Запустить Execution"}
                    </button>
                  ) : null}
                  {t.status === "ceo_approved" ||
                  t.status === "executing" ||
                  taskNeedsResearchRetry(t) ||
                  t.repo_status === "unreachable" ||
                  Boolean(t.execution_error) ? (
                    <button
                      type="button"
                      disabled={Boolean(busy)}
                      onClick={() => void decide(t.id, "skip")}
                      className="rounded-lg border border-rose-400/40 px-3 py-1.5 text-xs text-rose-100 disabled:opacity-40"
                    >
                      Skip (снять с конвейера)
                    </button>
                  ) : null}
                  {t.status === "draft_pr" || t.status === "ceo_review" ? (
                    <button
                      type="button"
                      disabled={
                        Boolean(busy) ||
                        !(
                          t.execution?.patch_ready ||
                          (t.execution?.stages?.implementation as { files_touched?: string[] } | undefined)
                            ?.files_touched?.length
                        )
                      }
                      onClick={() => void ceoSubmit(t.id)}
                      className="rounded-lg bg-emerald-500/90 px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-40"
                      title={
                        t.execution?.patch_ready ||
                        (t.execution?.stages?.implementation as { files_touched?: string[] } | undefined)
                          ?.files_touched?.length
                          ? undefined
                          : "Нет патча — отправлять на GitHub нельзя"
                      }
                    >
                      Отправить Draft PR (auto)
                    </button>
                  ) : null}
                  {t.pr_url || t.status === "pr_submitted" || t.status === "maintainer_review" || t.status === "merged" || t.status === "payment_available" || t.status === "withdraw" ? (
                    <button
                      type="button"
                      disabled={Boolean(busy)}
                      onClick={() => void syncTask(t.id, false)}
                      className="rounded-lg border border-sky-400/40 px-3 py-1.5 text-xs text-sky-100 disabled:opacity-40"
                    >
                      Синхронизировать статус
                    </button>
                  ) : null}
                  {t.status === "payment_available" || t.status === "reward_approved" || t.status === "withdraw" || t.status === "merged" ? (
                    <button
                      type="button"
                      disabled={Boolean(busy)}
                      onClick={() => void syncTask(t.id, true)}
                      className="rounded-lg bg-emerald-500/90 px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-40"
                    >
                      Подтвердить REAL (auto)
                    </button>
                  ) : null}
                  {t.pr_url ? (
                    <ExternalOpenButton
                      href={t.pr_url}
                      className="rounded-lg border border-white/15 px-2.5 py-1 text-[10px] text-sky-200"
                    >
                      Open PR ↗
                    </ExternalOpenButton>
                  ) : null}
                </div>
                <p className="mt-2 text-[10px] text-genesis-muted">
                  ID вручную не вводятся. PR number / merge SHA / confirmation собирает Farm из
                  GitHub + Opire. Для live push нужен GITHUB_TOKEN в{" "}
                  <code className="text-[10px]">dashboard/backend/.env.local</code>{" "}
                  (один раз). Submit сам делает fork, если нет push в upstream — classic PAT
                  с <code className="text-[10px]">public_repo</code>, либо fine-grained с
                  правом создавать репозитории.
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
