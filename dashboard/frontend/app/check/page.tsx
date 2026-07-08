"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Check = { id: string; label: string; icon: string; state: string; message: string };

type SystemCheck = {
  ready: boolean;
  headline: string;
  technical_checks: Check[];
  business_checks: Check[];
  warnings: string[];
};

export default function SystemCheckPage() {
  const [data, setData] = useState<SystemCheck | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/owner/system-check`);
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
        <header className="rounded-2xl border border-genesis-border bg-genesis-panel p-6 text-center">
          <p className="text-xs uppercase tracking-[0.35em] text-genesis-muted">Проверка {BRAND_NAME}</p>
          <h1 className="mt-2 text-xl font-semibold">
            {loading ? "Проверка…" : data?.headline ?? "Сервер не отвечает"}
          </h1>
          {data && (
            <p className={`mt-2 text-sm ${data.ready ? "text-emerald-400" : "text-amber-400"}`}>
              {data.ready ? "🟢 Можно работать" : "⚠ Требуется внимание"}
            </p>
          )}
        </header>

        {data && (
          <>
            <CheckSection title="Техническое состояние" items={data.technical_checks} />
            <CheckSection title="Здоровье бизнеса" items={data.business_checks} />
            {data.warnings.length > 0 && (
              <section className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-sm">
                {data.warnings.map((w, i) => (
                  <p key={i} className="mt-1 first:mt-0">
                    ⚠ {w}
                  </p>
                ))}
              </section>
            )}
          </>
        )}

        <div className="flex justify-center gap-4 text-sm">
          <button
            type="button"
            onClick={refresh}
            className="rounded-lg border border-genesis-border px-4 py-2 hover:border-genesis-accent"
          >
            Проверить снова
          </button>
          <Link href="/" className="rounded-lg px-4 py-2 text-genesis-accent hover:underline">
            {BRAND_NAME}
          </Link>
        </div>
      </div>
    </main>
  );
}

function CheckSection({ title, items }: { title: string; items: Check[] }) {
  return (
    <section className="rounded-xl border border-genesis-border bg-genesis-panel p-5">
      <h2 className="mb-3 text-sm font-medium text-genesis-muted">{title}</h2>
      <ul className="space-y-2 text-sm">
        {items.map((item) => (
          <li key={item.id} className="flex justify-between gap-4">
            <span>
              {item.icon} {item.label}
            </span>
            <span className="text-right text-genesis-muted">{item.message}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
