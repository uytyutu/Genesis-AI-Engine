"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Check = {
  id: string;
  label: string;
  icon: string;
  state: string;
  required: boolean;
  message: string;
};

type Launch = {
  sprint: string;
  kpi: string;
  launch_ready: boolean;
  soft_ready: boolean;
  public_url: string | null;
  payment_provider: string | null;
  checks: Check[];
  blocking_count: number;
  headline: string;
};

export default function PublicLaunchPage() {
  const [data, setData] = useState<Launch | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/owner/public-launch`);
      setData(await res.json());
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-lg space-y-5">
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/25 to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-400/90">
            {data?.sprint ?? "Public Launch v1"}
          </p>
          <h1 className="mt-2 text-xl font-semibold">
            {loading ? "Проверка…" : data?.headline ?? "Backend недоступен"}
          </h1>
          {data && (
            <>
              <p className="mt-3 text-sm text-genesis-muted">{data.kpi}</p>
              <p
                className={`mt-3 text-sm font-medium ${
                  data.launch_ready
                    ? "text-emerald-400"
                    : data.soft_ready
                      ? "text-amber-300"
                      : "text-genesis-muted"
                }`}
              >
                {data.launch_ready
                  ? "🟢 KPI спринта выполнен"
                  : data.soft_ready
                    ? "🟡 Сайт в сети — подключите Stripe для реальных €"
                    : `⚠ Блокирующих пунктов: ${data.blocking_count}`}
              </p>
            </>
          )}
        </header>

        {data && (
          <section className="space-y-2">
            {data.checks.map((c) => (
              <div
                key={c.id}
                className={`rounded-xl border px-4 py-3 ${
                  c.state === "ok"
                    ? "border-emerald-500/20 bg-emerald-950/10"
                    : c.state === "error"
                      ? "border-rose-500/30 bg-rose-950/10"
                      : "border-genesis-border bg-genesis-panel/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium">
                    {c.icon} {c.label}
                    {!c.required && (
                      <span className="ml-1 text-[10px] text-genesis-muted">(рекомендуется)</span>
                    )}
                  </p>
                </div>
                <p className="mt-1 text-xs text-genesis-muted">{c.message}</p>
              </div>
            ))}
          </section>
        )}

        <section className="rounded-xl border border-genesis-border bg-genesis-panel/60 p-4 text-xs text-genesis-muted">
          <p className="font-medium text-white/80">Переменные для продакшена</p>
          <ul className="mt-2 space-y-1 font-mono">
            <li>GENESIS_PUBLIC_URL — URL frontend (Vercel)</li>
            <li>GENESIS_CORS_ORIGINS — тот же URL</li>
            <li>NEXT_PUBLIC_API_URL — URL backend (Railway)</li>
            <li>STRIPE_SECRET_KEY — реальные оплаты</li>
          </ul>
        </section>

        <div className="flex flex-wrap justify-center gap-3 text-sm">
          <button
            type="button"
            onClick={refresh}
            className="rounded-lg border border-genesis-border px-4 py-2 hover:border-genesis-accent"
          >
            Проверить снова
          </button>
          <Link href="/company" className="rounded-lg px-4 py-2 text-genesis-accent hover:underline">
            Компания
          </Link>
          <Link href="/site" className="rounded-lg px-4 py-2 text-genesis-muted hover:underline">
            /site
          </Link>
        </div>
      </div>
    </main>
  );
}
