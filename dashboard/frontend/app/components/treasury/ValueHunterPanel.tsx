"use client";

import { useCallback, useMemo, useState } from "react";

type Opportunity = {
  id: string;
  title: string;
  kind?: string;
  category?: string;
  asset?: string;
  protocol?: string;
  capital_required_eur?: number;
  gas_required_eur?: number;
  registration_required?: boolean;
  account_required?: boolean;
  kyc_required?: boolean;
  expected_gross?: number | string | null;
  expected?: { expected_net?: number | string; expected_gross?: number | string; probability?: string };
  withdrawal_path?: string;
  automatable?: string;
  risk?: string;
  status?: string;
  reject_reason?: string;
  url?: string;
  source_of_funds_type?: string;
  source_of_funds_description?: string;
  source_of_funds_evidence?: string;
  eligibility?: string;
  required_action?: string;
  reward_rule?: string;
  economic_proof?: { ok?: boolean; chain?: Record<string, string>; status?: string };
  simulation?: { ok?: boolean; status?: string; reason?: string; note?: string };
  real_verification?: {
    status?: string;
    reason?: string;
    unknowns?: string[];
    questions?: { id: string; label: string; answer?: unknown }[];
  };
  real_status?: string;
  owner_gate?: string;
  notes?: string;
};

type HuntCounts = {
  sources_found?: number;
  verified?: number;
  zero_capital?: number;
  candidates_for_test?: number;
  testable?: number;
  queued?: number;
  rejected?: number;
  exit_only?: number;
  pending?: number;
  executable_now?: number;
  realized?: number;
  real_external_assets?: number;
  counter_invariant?: string;
  accounting?: Record<string, number | string>;
};

type HuntReport = {
  ok?: boolean;
  version?: string;
  message?: string;
  counts?: HuntCounts;
  mission?: {
    id?: string;
    title?: string;
    current?: number;
    h5?: string;
    kpi?: string;
    requirements?: string[];
  };
  genesis?: { genesis_pass?: boolean; stage?: string; allow_send?: boolean; reason?: string | null };
  counter_invariant?: string;
  opportunities?: Opportunity[];
  queue?: Opportunity[];
  rejected?: Opportunity[];
  by_category?: Record<string, Opportunity[]>;
  pipeline?: string[];
  law?: string[];
  auto_broadcast?: boolean;
  viable_zero_capital?: boolean;
  error?: string;
};

type EvolveReport = {
  ok?: boolean;
  agent?: {
    agent_id?: string;
    parent_id?: string | null;
    epoch?: number;
    status?: string;
    remaining_sec?: number;
    sources_checked?: number;
    verified?: number;
    executable?: number;
    executable_now?: number;
    realized_eur?: number;
    experience?: string[];
    success_memory?: unknown[];
    rejected_reasons?: Record<string, number>;
    genome?: Record<string, unknown>;
    last_systematic?: { epoch_status?: string; scientific_result?: string };
  };
  hunt?: { message?: string; counts?: Record<string, number>; rejected_sample?: { id?: string; status?: string; reason?: string }[] };
  systematic?: { epoch_status?: string; scientific_result?: string; message?: string };
  success_definition?: { required?: string[]; not_success?: string[]; honest_negative?: string };
  error?: string;
};

type TabId =
  | "sources"
  | "rewards"
  | "incentives"
  | "claims"
  | "sponsored"
  | "compute"
  | "bounties"
  | "pipeline"
  | "evolution";

const TABS: { id: TabId; label: string; cat?: string }[] = [
  { id: "sources", label: "ИСТОЧНИКИ", cat: "SOURCES" },
  { id: "rewards", label: "НАГРАДЫ", cat: "REWARDS" },
  { id: "incentives", label: "ИНЦЕНТИВЫ", cat: "INCENTIVES" },
  { id: "claims", label: "КЛЕЙМЫ", cat: "CLAIMS" },
  { id: "sponsored", label: "СПОНСОР", cat: "SPONSORED" },
  { id: "compute", label: "ВЫЧИСЛЕНИЯ", cat: "COMPUTE" },
  { id: "bounties", label: "БАУНТИ", cat: "BOUNTIES" },
  { id: "pipeline", label: "КОНВЕЙЕР" },
  { id: "evolution", label: "ЭВОЛЮЦИЯ" },
];

function fmt(v: unknown): string {
  if (v === null || v === undefined || v === "") return "НЕИЗВЕСТНО";
  return String(v);
}

export function ValueHunterPanel() {
  const [hunt, setHunt] = useState<HuntReport | null>(null);
  const [evo, setEvo] = useState<EvolveReport | null>(null);
  const [tab, setTab] = useState<TabId>("sources");
  const [selected, setSelected] = useState<Opportunity | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const runHunt = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/value-hunter/sources", { cache: "no-store" });
      const json = (await res.json()) as HuntReport;
      if (!res.ok || json.ok === false) {
        setErr(json.error || `HTTP ${res.status}`);
        setHunt(null);
      } else {
        setHunt(json);
        setSelected(null);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка поиска источников");
    } finally {
      setBusy(false);
    }
  }, []);

  const runEvolve = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/value-hunter/evolve", { cache: "no-store" });
      const json = (await res.json()) as EvolveReport;
      if (!res.ok || json.ok === false) {
        setErr(json.error || `HTTP ${res.status}`);
      } else {
        setEvo(json);
        setTab("evolution");
        // refresh hunt snapshot from evolution side-effect
        await runHunt();
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка эволюции");
    } finally {
      setBusy(false);
    }
  }, [runHunt]);

  const counts = hunt?.counts;
  const rows = useMemo(() => {
    if (!hunt) return [] as Opportunity[];
    const meta = TABS.find((t) => t.id === tab);
    if (meta?.cat && hunt.by_category?.[meta.cat]) return hunt.by_category[meta.cat] || [];
    if (tab === "pipeline" || tab === "evolution") return [];
    return hunt.opportunities || [];
  }, [hunt, tab]);

  return (
    <section className="rounded-2xl border-2 border-emerald-700/50 bg-gradient-to-b from-emerald-950/40 to-zinc-950 p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-emerald-500">
            Virtus Core · Охотник источников v2.1.1 · миссия VH-1
          </p>
          <h2 className="mt-1 text-xl font-bold text-emerald-50">ПЕРВЫЙ РЕАЛЬНЫЙ ВНЕШНИЙ АКТИВ (MAX_CAPITAL = €0)</h2>
          <p className="mt-2 max-w-3xl text-xs leading-relaxed text-zinc-400">
            KPI = <span className="font-mono text-amber-200">REAL_EXTERNAL_ASSETS</span>, не число opportunities.
            Кандидаты в очереди ≠ исполнение. Успех только после tx + подтверждения + роста баланса.
            AI не читает mnemonic — только proposal → локальный signer → владелец.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => void runHunt()}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
          >
            {busy ? "Идёт поиск…" : "ИСКАТЬ ИСТОЧНИКИ"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void runEvolve()}
            className="rounded-lg border border-amber-600/60 bg-amber-950/40 px-4 py-2 text-xs font-bold text-amber-100 disabled:opacity-50"
          >
            ЭПОХА ЭВОЛЮЦИИ
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-3 text-xs space-y-1">
        <p className="font-mono text-[10px] uppercase tracking-widest text-rose-300">Миссия VH-1 · гипотеза H5</p>
        <p className="text-rose-50 font-semibold">
          REAL EXTERNAL ASSETS = {counts?.real_external_assets ?? counts?.realized ?? 0} · H5 ={" "}
          {hunt?.mission?.h5 || "RESEARCH"}
        </p>
        <p className="text-zinc-400">
          Цель: первый подтверждённый внешний актив &gt; 0 (не 300 BTC, не MODEL $1M). Сейчас доказательств нет — пока ноль.
        </p>
        {hunt?.genesis && (
          <p className="font-mono text-[10px] text-zinc-500">
            Genesis PASS={String(hunt.genesis.genesis_pass)} · stage={hunt.genesis.stage} · allowSend=
            {String(hunt.genesis.allow_send)} · EXECUTABLE_NOW={counts?.executable_now ?? 0}
          </p>
        )}
        <p className="font-mono text-[10px] text-zinc-500">
          counterInvariant={hunt?.counter_invariant || counts?.counter_invariant || "—"}
          {counts?.accounting
            ? ` · ${counts.accounting.DISCOVERED}=${counts.accounting.REJECTED}+${counts.accounting.EXIT_ONLY}+${counts.accounting.CANDIDATES}+${counts.accounting.PENDING}+${counts.accounting.EXPIRED}`
            : ""}
        </p>
      </div>

      <div className="grid gap-2 sm:grid-cols-4 lg:grid-cols-8 text-[11px]">
        {[
          ["Найдено", counts?.sources_found],
          ["REAL verified", counts?.verified],
          ["€0 фильтр", counts?.zero_capital],
          ["Кандидаты на тест", counts?.candidates_for_test ?? counts?.testable],
          ["EXECUTABLE_NOW", counts?.executable_now ?? 0],
          ["Отклонено", counts?.rejected],
          ["EXIT only", counts?.exit_only],
          ["REAL assets", counts?.real_external_assets ?? counts?.realized ?? 0],
        ].map(([label, val]) => (
          <div
            key={String(label)}
            className={`rounded-lg border bg-zinc-950/70 p-3 ${
              label === "EXECUTABLE_NOW" || label === "REAL assets"
                ? "border-amber-800/50"
                : "border-zinc-700"
            }`}
          >
            <p className="font-mono text-zinc-500">{label}</p>
            <p className="mt-1 text-xl font-bold text-emerald-100">{val ?? "—"}</p>
          </div>
        ))}
      </div>

      {hunt?.message && (
        <p
          className={`rounded-lg border px-3 py-2 text-xs ${
            hunt.viable_zero_capital
              ? "border-emerald-800 bg-emerald-950/30 text-emerald-100"
              : "border-amber-800/50 bg-amber-950/20 text-amber-100"
          }`}
        >
          {hunt.message}
        </p>
      )}

      <div className="flex flex-wrap gap-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded border px-2.5 py-1 text-[10px] font-mono ${
              tab === t.id
                ? "border-emerald-500 bg-emerald-950 text-emerald-100"
                : "border-zinc-700 text-zinc-400"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {err && (
        <div className="rounded border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">{err}</div>
      )}

      {tab === "pipeline" && (
        <div className="grid gap-3 lg:grid-cols-2 text-xs text-zinc-300">
          <ol className="list-decimal space-y-1 pl-5">
            {(hunt?.pipeline || []).map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ol>
          <ul className="space-y-1 text-zinc-400">
            {(hunt?.law || []).map((l) => (
              <li key={l}>• {l}</li>
            ))}
            <li className="text-rose-300">• Автоматический broadcast: ЗАПРЕЩЁН</li>
          </ul>
        </div>
      )}

      {tab === "evolution" && (
        <div className="space-y-3 text-xs">
          {!evo && <p className="text-zinc-500">Запустите «ЭПОХА ЭВОЛЮЦИИ» — агент на 60 минут, наследование уроков.</p>}
          {evo?.agent && (
            <>
              <div className="grid gap-2 sm:grid-cols-3">
                <div className="rounded-lg border border-zinc-700 p-3">
                  <p className="font-mono text-zinc-500">Агент</p>
                  <p className="font-bold text-amber-100">{evo.agent.agent_id}</p>
                  <p className="text-zinc-500">родитель: {fmt(evo.agent.parent_id)}</p>
                </div>
                <div className="rounded-lg border border-zinc-700 p-3">
                  <p className="font-mono text-zinc-500">Эпоха / осталось</p>
                  <p className="font-bold text-amber-100">
                    #{evo.agent.epoch} · {Math.round((evo.agent.remaining_sec || 0) / 60)} мин
                  </p>
                </div>
                <div className="rounded-lg border border-zinc-700 p-3">
                  <p className="font-mono text-zinc-500">Исполняемых сейчас / кандидаты</p>
                  <p className="font-bold text-amber-100">
                    {evo.agent.executable_now ?? 0} / {evo.agent.executable ?? 0}
                  </p>
                </div>
              </div>
              {(evo.systematic || evo.agent.last_systematic) && (
                <div
                  className={`rounded-lg border p-3 ${
                    (evo.systematic?.epoch_status || evo.agent.last_systematic?.epoch_status) ===
                    "NO_VALID_OPPORTUNITY"
                      ? "border-amber-700/50 bg-amber-950/20"
                      : "border-emerald-800/40 bg-emerald-950/20"
                  }`}
                >
                  <p className="font-semibold text-zinc-200">Systematic Discovery</p>
                  <p className="mt-1 font-mono text-amber-100">
                    {evo.systematic?.epoch_status || evo.agent.last_systematic?.epoch_status} ·{" "}
                    {evo.systematic?.scientific_result || evo.agent.last_systematic?.scientific_result}
                  </p>
                  {evo.systematic?.message && <p className="mt-1 text-zinc-400">{evo.systematic.message}</p>}
                  <p className="mt-1 text-[10px] text-zinc-500">
                    Честный негатив: {evo.success_definition?.honest_negative || "NO_VALID_OPPORTUNITY"} · статус
                    агента: {evo.agent.status || "—"}
                  </p>
                </div>
              )}
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-3">
                <p className="font-semibold text-zinc-200">Опыт (не мутирует security policy)</p>
                <ul className="mt-2 space-y-1 text-zinc-400">
                  {(evo.agent.experience || []).map((x) => (
                    <li key={x}>• {x}</li>
                  ))}
                </ul>
              </div>
              <div className="rounded-lg border border-zinc-800 p-3 text-zinc-400">
                <p className="text-zinc-200 font-semibold">Что считается успехом</p>
                <p className="mt-1">{(evo.success_definition?.required || []).join(" + ")}</p>
                <p className="mt-1 text-rose-300/90">
                  Не успех: {(evo.success_definition?.not_success || []).join(", ")}
                </p>
              </div>
              {(evo.hunt?.rejected_sample || []).length > 0 && (
                <div className="overflow-x-auto rounded-xl border border-zinc-800">
                  <table className="w-full text-left text-[11px]">
                    <thead className="bg-zinc-900/80 font-mono text-zinc-500">
                      <tr>
                        <th className="px-2 py-2">ID</th>
                        <th className="px-2 py-2">Статус</th>
                        <th className="px-2 py-2">Причина</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(evo.hunt?.rejected_sample || []).map((r) => (
                        <tr key={`${r.id}-${r.status}`} className="border-t border-zinc-800">
                          <td className="px-2 py-2 font-mono">{r.id}</td>
                          <td className="px-2 py-2 text-amber-200">{r.status}</td>
                          <td className="px-2 py-2 text-zinc-400">{r.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {tab !== "pipeline" && tab !== "evolution" && (
        <div className="grid gap-3 lg:grid-cols-[1.4fr_1fr]">
          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="w-full min-w-[56rem] text-left text-[11px]">
              <thead className="bg-zinc-900/80 font-mono text-zinc-500">
                <tr>
                  <th className="px-2 py-2">Актив</th>
                  <th className="px-2 py-2">Источник</th>
                  <th className="px-2 py-2">Протокол</th>
                  <th className="px-2 py-2">Капитал</th>
                  <th className="px-2 py-2">Газ</th>
                  <th className="px-2 py-2">Рег.</th>
                  <th className="px-2 py-2">KYC</th>
                  <th className="px-2 py-2">Gross</th>
                  <th className="px-2 py-2">Net</th>
                  <th className="px-2 py-2">Вывод</th>
                  <th className="px-2 py-2">Авто</th>
                  <th className="px-2 py-2">Риск</th>
                  <th className="px-2 py-2">Статус</th>
                </tr>
              </thead>
              <tbody>
                {!hunt && (
                  <tr>
                    <td colSpan={13} className="px-3 py-4 text-zinc-500">
                      Нажмите «ИСКАТЬ ИСТОЧНИКИ». Без фейковых строк.
                    </td>
                  </tr>
                )}
                {rows.map((s) => (
                  <tr
                    key={s.id}
                    className={`border-t border-zinc-800 align-top cursor-pointer ${
                      selected?.id === s.id ? "bg-emerald-950/30" : "hover:bg-zinc-900/40"
                    }`}
                    onClick={() => setSelected(s)}
                  >
                    <td className="px-2 py-2 font-mono text-zinc-300">{fmt(s.asset)}</td>
                    <td className="px-2 py-2">
                      <div className="text-emerald-100 font-medium max-w-[12rem]">{s.title}</div>
                      <div className="text-[10px] text-zinc-500">{fmt(s.source_of_funds_type || s.kind)}</div>
                    </td>
                    <td className="px-2 py-2 font-mono text-zinc-400">{fmt(s.protocol)}</td>
                    <td className="px-2 py-2 font-mono">€{s.capital_required_eur ?? 0}</td>
                    <td className="px-2 py-2 font-mono">€{s.gas_required_eur ?? 0}</td>
                    <td className="px-2 py-2">{s.registration_required || s.account_required ? "да" : "нет"}</td>
                    <td className="px-2 py-2">{s.kyc_required ? "да" : "нет"}</td>
                    <td className="px-2 py-2 font-mono">{fmt(s.expected?.expected_gross ?? s.expected_gross)}</td>
                    <td className="px-2 py-2 font-mono">{fmt(s.expected?.expected_net)}</td>
                    <td className="px-2 py-2 max-w-[8rem] text-zinc-400">{fmt(s.withdrawal_path)}</td>
                    <td className="px-2 py-2">{fmt(s.automatable)}</td>
                    <td className="px-2 py-2 max-w-[8rem] text-zinc-500">{fmt(s.risk)}</td>
                    <td className="px-2 py-2 font-mono text-amber-200">{fmt(s.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="rounded-xl border border-zinc-700 bg-zinc-950/60 p-4 space-y-3 text-xs">
            <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-500">Панель доказательства</p>
            {!selected && <p className="text-zinc-500">Выберите строку в таблице.</p>}
            {selected && (
              <>
                <h3 className="text-sm font-bold text-emerald-100">{selected.title}</h3>
                {(
                  [
                    ["ИСТОЧНИК", selected.source_of_funds_description || selected.title],
                    ["ПРАВИЛО", selected.reward_rule],
                    ["ДЕЙСТВИЕ", selected.required_action],
                    ["НАГРАДА / АКТИВ", selected.asset],
                    ["КАПИТАЛ", `€${selected.capital_required_eur ?? 0}`],
                    ["ГАЗ", `€${selected.gas_required_eur ?? 0}`],
                    ["НАЗНАЧЕНИЕ", selected.withdrawal_path],
                    ["ДОКАЗАТЕЛЬСТВО", selected.source_of_funds_evidence || selected.url],
                    ["СИМУЛЯЦИЯ", selected.simulation?.status || selected.simulation?.reason],
                    ["REAL VERIFY", selected.real_verification?.status || selected.real_status],
                    ["НЕИЗВЕСТНО", (selected.real_verification?.unknowns || []).join(", ") || "—"],
                    ["ОЖИДАЕМЫЙ NET", fmt(selected.expected?.expected_net)],
                    ["СТАТУС", selected.status],
                    ["ОТКЛОНЕНИЕ", selected.reject_reason],
                  ] as const
                ).map(([k, v]) => (
                  <div key={k} className="grid grid-cols-[7rem_1fr] gap-2 border-b border-zinc-800/80 pb-1">
                    <span className="font-mono text-[10px] text-zinc-500">{k}</span>
                    <span className="text-zinc-300 break-all">{fmt(v)}</span>
                  </div>
                ))}
                {!!selected.real_verification?.questions?.length && (
                  <div className="rounded border border-zinc-800 p-2 space-y-1">
                    <p className="font-mono text-[10px] text-zinc-500">9 вопросов REAL VERIFICATION</p>
                    {selected.real_verification.questions.map((q) => (
                      <p key={q.id} className="text-[10px] text-zinc-400">
                        <span className="text-zinc-500">{q.label}</span> → {fmt(q.answer)}
                      </p>
                    ))}
                  </div>
                )}
                <div className="flex flex-wrap gap-2 pt-2">
                  <button type="button" className="rounded border border-zinc-600 px-2 py-1 text-[10px] text-zinc-300" disabled>
                    ПРОВЕРИТЬ
                  </button>
                  <button type="button" className="rounded border border-zinc-600 px-2 py-1 text-[10px] text-zinc-300" disabled>
                    СИМУЛИРОВАТЬ
                  </button>
                  <button type="button" className="rounded border border-zinc-600 px-2 py-1 text-[10px] text-zinc-300" disabled>
                    В ОЧЕРЕДЬ
                  </button>
                  <button
                    type="button"
                    className="rounded border border-amber-700/50 px-2 py-1 text-[10px] text-amber-200"
                    disabled
                    title="Только после всех gates"
                  >
                    ОДОБРЕНИЕ ВЛАДЕЛЬЦА
                  </button>
                </div>
                <p className="text-[10px] text-zinc-600">
                  Кнопка исполнения появится только после всех gates. Broadcast mainnet — только вручную владельцем
                  (CLI без auto-broadcast).
                </p>
              </>
            )}
          </div>
        </div>
      )}

      <p className="text-[10px] text-zinc-600">
        CLI: <code className="text-zinc-400">npm run value:sources</code> ·{" "}
        <code className="text-zinc-400">value:verify</code> · <code className="text-zinc-400">value:simulate</code> ·{" "}
        <code className="text-zinc-400">value:evolve</code> · инфраструктура: Genesis · Route Finder · Reality Ledger ·
        Kill Switch
      </p>
    </section>
  );
}
