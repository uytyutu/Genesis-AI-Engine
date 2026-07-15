"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type StripeStep = { id: string; label_ru: string; done: boolean; detail_ru: string };

type StripeSetup = {
  configured: boolean;
  live_mode: boolean;
  test_mode: boolean;
  webhook_configured: boolean;
  mode_label_ru: string;
  implementation_status_ru?: string;
  operational_status_ru?: string;
  operational?: boolean;
  webhook_url: string;
  steps: StripeStep[];
  ceo_path_ru: string[];
  sync_hint_ru: string;
};

export function StripeSetupPanel() {
  const [data, setData] = useState<StripeSetup | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/stripe-setup`);
      if (res.ok) setData(await res.json());
    } catch {
      setData(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const syncStripe = async () => {
    setSyncing(true);
    setSyncMsg("");
    try {
      const res = await fetch(`${API}/api/owner/payment-sync`, { method: "POST" });
      const body = await res.json();
      setSyncMsg(body.stripe_available_eur != null ? `Stripe: ${body.stripe_available_eur} €` : "Синхронизировано");
      await refresh();
    } catch {
      setSyncMsg("Ошибка синхронизации");
    } finally {
      setSyncing(false);
    }
  };

  if (!data) return null;

  return (
    <section className="rounded-2xl border border-violet-500/35 bg-violet-950/20 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Stripe Live</h2>
          <p className="mt-1 text-sm text-violet-200/90">{data.implementation_status_ru ?? data.mode_label_ru}</p>
          <p className={`mt-1 text-xs ${data.operational ? "text-emerald-300" : "text-amber-200"}`}>
            {data.operational_status_ru ?? data.mode_label_ru}
          </p>
        </div>
        <button
          type="button"
          disabled={!data.configured || syncing}
          onClick={() => void syncStripe()}
          className="rounded-lg border border-violet-400/40 px-3 py-1.5 text-sm text-violet-100 hover:bg-violet-950/40 disabled:opacity-40"
        >
          {syncing ? "…" : "Синхронизировать Stripe"}
        </button>
      </div>

      <ul className="mt-4 space-y-2">
        {data.steps.map((step) => (
          <li key={step.id} className="flex gap-3 text-sm">
            <span className={step.done ? "text-emerald-400" : "text-genesis-muted"}>{step.done ? "✓" : "○"}</span>
            <div>
              <p className="text-white/90">{step.label_ru}</p>
              <p className="text-xs text-genesis-muted">{step.detail_ru}</p>
            </div>
          </li>
        ))}
      </ul>

      <ol className="mt-5 space-y-2 text-xs leading-relaxed text-genesis-muted">
        {data.ceo_path_ru.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ol>

      {syncMsg ? <p className="mt-3 text-sm text-emerald-300">{syncMsg}</p> : null}

      <p className="mt-4 text-xs text-genesis-muted">
        После оплаты клиента «Получено» обновится на{" "}
        <Link href="/business/kpi" className="text-emerald-400 underline">
          /business/kpi
        </Link>
        . CEO confirm pending — на этой странице ниже.
      </p>
    </section>
  );
}
