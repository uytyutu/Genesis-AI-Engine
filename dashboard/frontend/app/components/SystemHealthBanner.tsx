"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { GenesisCard } from "./GenesisCard";
import { useToast } from "./ToastProvider";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Check = {
  id: string;
  label: string;
  icon: string;
  state: string;
  message: string;
};

type SystemCheck = {
  ready: boolean;
  headline: string;
  technical_checks: Check[];
  warnings: string[];
};

const FIX_HINTS: Record<string, { text: string; href?: string }> = {
  backend: {
    text: "Запустите Genesis через Launcher (кнопка «Запустить»).",
  },
  frontend: {
    text: "Перезапустите Genesis. Если ошибка в CSS — проверьте app/globals.css и frontend.log.",
    href: "/check",
  },
  api: {
    text: "Backend запущен частично — перезапустите Genesis и проверьте backend.log.",
    href: "/check",
  },
  payment_hub: {
    text: "Подключите Payment Hub после первого реального клиента — раздел Finance.",
    href: "/finance",
  },
  storage: {
    text: "Проверьте права на папку memory/ в каталоге Genesis.",
  },
  ai_models: {
    text: "Внешние модели подключаются по мере готовности — не блокирует работу.",
  },
};

export function SystemHealthBanner() {
  const { push } = useToast();
  const [data, setData] = useState<SystemCheck | null>(null);
  const [checkedOnce, setCheckedOnce] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/system-check`);
      if (!res.ok) throw new Error("offline");
      const json = (await res.json()) as SystemCheck;
      setData(json);
      if (json.ready && !checkedOnce) {
        push({ title: "Система проверена", tone: "success" });
        setCheckedOnce(true);
      }
    } catch {
      setData({
        ready: false,
        headline: "Backend не отвечает",
        technical_checks: [
          {
            id: "backend",
            label: "Backend",
            icon: "✘",
            state: "error",
            message: "Запустите Genesis через Launcher",
          },
        ],
        warnings: [],
      });
    }
  }, [checkedOnce, push]);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, 15000);
    return () => window.clearInterval(id);
  }, [refresh]);

  if (!data || data.ready) {
    return null;
  }

  const problems = data.technical_checks.filter((c) => c.state === "error");

  return (
    <GenesisCard className="mb-6 border-amber-500/30 bg-amber-950/20 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="genesis-label text-amber-400">Проверка при запуске</p>
          <h2 className="mt-1 text-lg font-semibold">{data.headline}</h2>
          <p className="mt-1 text-sm text-genesis-muted">
            Некоторые сервисы недоступны. Исправьте перед работой с клиентами.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          className="rounded-lg border border-genesis-border px-4 py-2 text-sm hover:border-genesis-accent"
        >
          Проверить снова
        </button>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {problems.map((check) => {
          const hint = FIX_HINTS[check.id];
          return (
            <div
              key={check.id}
              className="rounded-xl border border-genesis-border bg-genesis-panel/60 p-4"
            >
              <p className="text-sm font-medium">
                {check.icon} {check.label}
              </p>
              <p className="mt-1 text-xs text-genesis-muted">{check.message}</p>
              {hint && <p className="mt-2 text-xs text-amber-200/90">{hint.text}</p>}
              {hint?.href && (
                <Link
                  href={hint.href}
                  className="mt-3 inline-block rounded-lg bg-genesis-accent px-3 py-1.5 text-xs font-medium text-white"
                >
                  Исправить
                </Link>
              )}
            </div>
          );
        })}
      </div>

      {data.warnings.length > 0 && (
        <ul className="mt-4 space-y-1 text-xs text-amber-200/80">
          {data.warnings.map((w) => (
            <li key={w}>⚠ {w}</li>
          ))}
        </ul>
      )}
    </GenesisCard>
  );
}
