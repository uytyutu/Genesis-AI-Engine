"use client";

/**
 * Virtus Autonomous Agent — честная панель «машины».
 * LIVE: BTC agent (терминал) + ETH MetaMask (ниже).
 * Compute providers: только статус — без фейкового Connect.
 */

type AgentStage = {
  id: string;
  label: string;
  detail: string;
  status: "live" | "hitl" | "skip" | "model";
};

type ProviderRow = {
  id: string;
  name: string;
  netHint: string;
  status: "LIVE" | "HITL" | "SKIPPED" | "MODELING";
  reason: string;
};

const PIPELINE: AgentStage[] = [
  { id: "scan", label: "Скан", detail: "mempool.space / RPC · свои адреса", status: "live" },
  { id: "profit", label: "Расчёт", detail: "комиссия · net · фильтр пыли", status: "live" },
  { id: "hitl", label: "Подтверждение", detail: "y/N в терминале или MetaMask", status: "hitl" },
  { id: "exec", label: "Исполнение", detail: "подпись на ПК · broadcast", status: "hitl" },
  { id: "wallet", label: "Vault", detail: "локальный / корпоративный адрес", status: "live" },
];

const PROVIDERS: ProviderRow[] = [
  {
    id: "btc-agent",
    name: "BTC Agent (локальный)",
    netHint: "net = сумма UTXO − fee",
    status: "HITL",
    reason: "npm run agent:sweep · ключи в .env.btc · подтверждение y/N",
  },
  {
    id: "eth-metamask",
    name: "ETH MetaMask",
    netHint: "balance > gas → выгодно",
    status: "HITL",
    reason: "Панель ниже · только подключённый аккаунт",
  },
  {
    id: "golem",
    name: "Golem Provider",
    netHint: "модель GLM/h",
    status: "SKIPPED",
    reason: "Требует Linux+KVM · ручная установка Yagna · не zero-setup",
  },
  {
    id: "mining",
    name: "BTC Mining (GTX 1650)",
    netHint: "ожид. net < 0",
    status: "SKIPPED",
    reason: "Profit engine: электричество > награда · SKIP",
  },
  {
    id: "value-hunter",
    name: "Value Hunter (bug bounty)",
    netHint: "EV = p × mid bounty",
    status: "HITL",
    reason: "/value-hunter · Immunefi/Code4rena · report→payout, не sweep",
  },
  {
    id: "compute",
    name: "Compute Engine (PoW/PoUW research)",
    netHint: "measured → then economics",
    status: "HITL",
    reason: "Открыть /compute · npm run compute:audit · REAL=0 пока нет CONFIRMED payout",
  },
];

function statusColor(s: AgentStage["status"] | ProviderRow["status"]) {
  switch (s) {
    case "live":
    case "LIVE":
      return "border-emerald-600 bg-emerald-950/40 text-emerald-300";
    case "hitl":
    case "HITL":
      return "border-amber-500 bg-amber-950/40 text-amber-200";
    case "skip":
    case "SKIPPED":
      return "border-zinc-600 bg-zinc-900/80 text-zinc-400";
    default:
      return "border-cyan-800 bg-cyan-950/30 text-cyan-300";
  }
}

export function AutonomousAgentPanel() {
  return (
    <section className="rounded-2xl border-2 border-cyan-800/60 bg-gradient-to-b from-cyan-950/30 to-zinc-950 p-5 space-y-5">
      <div>
        <p className="text-[10px] font-mono uppercase tracking-widest text-cyan-500">Virtus Autonomous Agent</p>
        <h2 className="mt-1 text-lg font-bold text-cyan-200">Машина поиска ценности · Human-in-the-Loop</h2>
        <p className="mt-2 max-w-3xl text-xs leading-relaxed text-zinc-400">
          Один принцип: <strong className="text-zinc-200">NO ACCOUNT = NO BLOCKER</strong> — если нужна регистрация или
          API-ключ, адаптер помечается SKIPPED и агент идёт дальше. Реальные €/BTC только после подтверждения
          человека или MetaMask. Симуляция ≠ REAL до External Payout ID.
        </p>
      </div>

      {/* Pipeline */}
      <div className="flex flex-wrap gap-2">
        {PIPELINE.map((st, i) => (
          <div key={st.id} className="flex items-center gap-2">
            <div
              className={`rounded-lg border px-3 py-2 text-xs ${statusColor(st.status)}`}
              title={st.detail}
            >
              <div className="font-bold">{st.label}</div>
              <div className="text-[10px] opacity-80">{st.detail}</div>
            </div>
            {i < PIPELINE.length - 1 && <span className="text-zinc-600">→</span>}
          </div>
        ))}
      </div>

      {/* Providers table */}
      <div className="overflow-x-auto rounded-xl border border-zinc-800">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-zinc-800 bg-zinc-900/80 text-[10px] uppercase text-zinc-500">
            <tr>
              <th className="px-3 py-2">Адаптер</th>
              <th className="px-3 py-2">Net</th>
              <th className="px-3 py-2">Статус</th>
              <th className="px-3 py-2">Причина</th>
            </tr>
          </thead>
          <tbody className="font-mono text-zinc-300">
            {PROVIDERS.map((p) => (
              <tr key={p.id} className="border-b border-zinc-900/80">
                <td className="px-3 py-2.5 text-zinc-100">{p.name}</td>
                <td className="px-3 py-2.5 text-zinc-400">{p.netHint}</td>
                <td className="px-3 py-2.5">
                  <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${statusColor(p.status)}`}>
                    {p.status}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-zinc-500">{p.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Commands */}
      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-amber-700/50 bg-amber-950/25 p-4">
          <h3 className="text-sm font-semibold text-amber-200">BTC · локальный агент</h3>
          <p className="mt-1 text-[11px] text-zinc-400">
            HITL: <code className="text-amber-200/90">npm run agent:sweep</code>
          </p>
        </div>
        <div className="rounded-xl border border-emerald-800/50 bg-emerald-950/20 p-4">
          <h3 className="text-sm font-semibold text-emerald-300">ETH · MetaMask</h3>
          <p className="mt-1 text-[11px] text-zinc-400">Панель живого аудита ниже — подпись в расширении.</p>
        </div>
        <div className="rounded-xl border border-cyan-800/50 bg-cyan-950/20 p-4">
          <h3 className="text-sm font-semibold text-cyan-300">Compute Engine</h3>
          <p className="mt-1 text-[11px] text-zinc-400">
            <a href="/compute" className="text-cyan-300 underline">
              /compute
            </a>{" "}
            · <code className="text-amber-200/90">npm run compute:audit</code>
          </p>
        </div>
      </div>
    </section>
  );
}
