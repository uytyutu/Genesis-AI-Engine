"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type FeaturesSnap = {
  tiktok_enabled: boolean;
  media_engine_enabled?: boolean;
  path_a_independent?: boolean;
  status_ru?: string;
  principle_ru?: string;
  module?: string;
  config_path?: string;
};

export default function TikTokHorizonPage() {
  const [snap, setSnap] = useState<FeaturesSnap | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/features`);
      if (res.ok) setSnap(await res.json());
    } catch {
      setMessage("Backend недоступен — флаги не прочитаны.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function activate() {
    const ok = window.confirm(
      "Активировать TikTok Horizon?\n\n" +
        "Сейчас логика всё равно не публикует ролики — только снимает kill switch.\n" +
        "Path A (Stripe / Country Desk) не затрагивается.\n\n" +
        "Продолжить?"
    );
    if (!ok) return;
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/owner/features/tiktok/activate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ceo_confirmed: true }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Ошибка активации");
        return;
      }
      setSnap(body);
      setMessage("Флаг tiktok_enabled=true. Автопубликация не запущена.");
    } finally {
      setBusy(false);
    }
  }

  async function deactivate() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/features/tiktok/deactivate`, {
        method: "POST",
      });
      if (res.ok) {
        setSnap(await res.json());
        setMessage("Kill switch снова OFF — безопасно.");
      }
    } finally {
      setBusy(false);
    }
  }

  const enabled = snap?.tiktok_enabled === true;

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-3xl space-y-6 animate-fade-up">
        <header className="rounded-2xl border border-white/10 bg-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-amber-200/80">Horizon · dormant</p>
          <h1 className="mt-2 text-2xl font-semibold">TikTok Horizon</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Полка на будущее. Не Mission 1. Path A работает независимо.
          </p>
          <p className="mt-3 text-xs text-amber-100/90">
            {snap?.principle_ru ||
              "Ролик только из повторяющейся закономерности → человек → /order."}
          </p>
        </header>

        <section className="genesis-card space-y-3 p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold">Kill switch</h2>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs ${
                enabled
                  ? "bg-amber-500/20 text-amber-200"
                  : "bg-emerald-500/20 text-emerald-300"
              }`}
            >
              {snap?.status_ru ?? "…"}
            </span>
          </div>
          <p className="text-xs text-genesis-muted">
            Модуль: <code className="text-white/80">{snap?.module ?? "modules/tiktok_factory"}</code>
            <br />
            Конфиг: <code className="text-white/80">{snap?.config_path ?? "config/features.json"}</code>
          </p>
          <ul className="space-y-1 text-xs text-genesis-muted">
            <li>• При OFF: сценарии и API TikTok не выполняются.</li>
            <li>• Content Engine (TikTok / YouTube / LinkedIn / Blog) — Horizon.</li>
            <li>• Stripe → Factory Path A не зависит от этого флага.</li>
          </ul>
          <div className="flex flex-wrap gap-2 pt-2">
            {!enabled ? (
              <button
                type="button"
                disabled={busy}
                onClick={() => void activate()}
                className="rounded-lg bg-amber-600/90 px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
              >
                Активировать направление
              </button>
            ) : (
              <button
                type="button"
                disabled={busy}
                onClick={() => void deactivate()}
                className="rounded-lg border border-emerald-500/40 px-4 py-2 text-sm text-emerald-200 disabled:opacity-50"
              >
                Выключить (kill switch)
              </button>
            )}
            <Link
              href="/acquisition"
              className="rounded-lg border border-genesis-border px-4 py-2 text-sm hover:bg-white/5"
            >
              ← Country Desk (Path A)
            </Link>
            <Link
              href="/ceo-site"
              className="rounded-lg border border-genesis-border px-4 py-2 text-sm hover:bg-white/5"
            >
              Сайт клиентов
            </Link>
          </div>
          {message ? <p className="text-xs text-genesis-muted">{message}</p> : null}
        </section>

        <section className="genesis-card space-y-2 p-5 text-sm text-genesis-muted">
          <h2 className="text-sm font-semibold text-white">Принцип контента (когда включите)</h2>
          <pre className="overflow-x-auto rounded-lg bg-black/30 p-3 text-[11px] text-emerald-100/80 whitespace-pre-wrap">
            {`Spider
  → повторяющаяся проблема
  → Genesis проверил частоту
  → образовательный ролик (анонимный паттерн)
  → человек утверждает
  → публикация
  → клик на /order`}
          </pre>
          <p className="text-xs">Не делать ролики ради просмотров. Не doxx живые фирмы.</p>
        </section>
      </div>
    </main>
  );
}
