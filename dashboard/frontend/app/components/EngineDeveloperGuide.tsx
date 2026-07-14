"use client";

import { useCallback, useEffect, useState } from "react";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type LogicStep = { step: string; name: string; detail: string };

type LiveAnalytics = {
  updated_at: string;
  events_last_hour: number;
  event_breakdown: Record<string, number>;
  harvest_balance_eur: number;
  hunter_value_eur: number;
  pattern_hits_total: number;
  developer_note: string;
  logic_chain: LogicStep[];
  market: {
    outreach_leads: number;
    recoverable_assets: number;
    junk_archive_targets: number;
    top_countries: { code: string; leads: number }[];
  };
  digital_dust: {
    recoverable_assets_count: number;
    recoverable_value_eur: number;
    legal_boundary: string;
    etherscan_configured: boolean;
  };
  smart_gate: {
    auto_executed_count: number;
    manual_review_count: number;
  };
};

const HELP: Record<string, string> = {
  "Public Scan": "Сканирует только публичные URL. Никаких паролей и закрытых систем.",
  PublicIntelMiner: "RegEx на слабых сайтах + Digital Dust (0x-контракты, orphan pool).",
  "Security Gate": "Уничтожает match при private key / mnemonic — страховка от Diebstahl.",
  "Digital Dust Validator": "Только withdraw/claim через публичный ABI. CEO вручную.",
  "Smart-Gate": "Авто только безопасные микро-сделки. Кошельки — всегда CEO.",
  "Harvest Ledger": "potential_recoverable_asset в harvest_ledger.jsonl.",
  Hunter: "4 сценария €0: Bounty · SEO · Outreach · Dataset.",
  "Global Spider": "Весь мир: seeds + Google Places. Без IP-скана.",
};

export function EngineDeveloperGuide() {
  const [live, setLive] = useState<LiveAnalytics | null>(null);
  const [open, setOpen] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/engine/analytics/live`);
      if (res.ok) setLive(await res.json());
    } catch {
      setLive(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = window.setInterval(refresh, 15_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  return (
    <section id="dev-guide" className="genesis-card border border-cyan-500/25 p-5">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-left"
      >
        <div>
          <h2 className="text-sm font-semibold text-cyan-100">Помощник разработчика · логика Engine</h2>
          <p className="mt-1 text-[11px] text-genesis-muted">
            Живая аналитика каждые 15 с · цепочка Hunter-Gatherer + Digital Dust
          </p>
        </div>
        <span className="text-cyan-300">{open ? "▾" : "▸"}</span>
      </button>

      {open && live ? (
        <div className="mt-4 space-y-4">
          <p className="rounded-lg bg-cyan-950/30 px-3 py-2 text-[11px] text-cyan-100">{live.developer_note}</p>

          <div className="grid gap-2 sm:grid-cols-4 text-[11px]">
            <div className="rounded-lg border border-white/10 p-3">
              <span className="text-genesis-muted">События / час</span>
              <p className="text-lg font-bold text-white">{live.events_last_hour}</p>
            </div>
            <div className="rounded-lg border border-white/10 p-3">
              <span className="text-genesis-muted">Outreach лидов</span>
              <p className="text-lg font-bold text-white">{live.market.outreach_leads}</p>
            </div>
            <div className="rounded-lg border border-white/10 p-3">
              <span className="text-genesis-muted">Recoverable</span>
              <p className="text-lg font-bold text-emerald-300">{live.digital_dust.recoverable_assets_count}</p>
            </div>
            <div className="rounded-lg border border-white/10 p-3">
              <span className="text-genesis-muted">Smart-Gate авто</span>
              <p className="text-lg font-bold text-amber-200">{live.smart_gate.auto_executed_count}</p>
            </div>
          </div>

          <div>
            <h3 className="text-xs font-semibold text-white">Цепочка логики (легальный Hunter-Gatherer)</h3>
            <ol className="mt-2 space-y-2">
              {live.logic_chain.map((s) => (
                <li
                  key={s.step}
                  className="rounded-lg border border-white/10 bg-black/20 px-3 py-2"
                  title={HELP[s.name] ?? s.detail}
                >
                  <div className="flex gap-2 text-[11px]">
                    <span className="font-mono text-cyan-400">{s.step}</span>
                    <span className="font-semibold text-white">{s.name}</span>
                  </div>
                  <p className="mt-1 text-[10px] text-genesis-muted">{HELP[s.name] ?? s.detail}</p>
                </li>
              ))}
            </ol>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 text-[11px]">
            <div className="rounded-lg border border-emerald-500/20 p-3">
              <p className="font-semibold text-emerald-200">Digital Dust · легально</p>
              <p className="mt-1 text-genesis-muted">{live.digital_dust.legal_boundary}</p>
              <p className="mt-2">
                Потенциал: {formatEur(live.digital_dust.recoverable_value_eur)} · Etherscan{" "}
                {live.digital_dust.etherscan_configured ? "ON" : "OFF (добавь ETHERSCAN_API_KEY)"}
              </p>
            </div>
            <div className="rounded-lg border border-violet-500/20 p-3">
              <p className="font-semibold text-violet-200">Рынок под задачи</p>
              <ul className="mt-2 space-y-1 text-genesis-muted">
                {live.market.top_countries.map((c) => (
                  <li key={c.code}>
                    {c.code}: {c.leads} целей
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <p className="text-[10px] text-genesis-muted">
            Обновлено: {live.updated_at?.slice(0, 19).replace("T", " ")} UTC · Manual Review:{" "}
            {live.smart_gate.manual_review_count}
          </p>
        </div>
      ) : null}
    </section>
  );
}
