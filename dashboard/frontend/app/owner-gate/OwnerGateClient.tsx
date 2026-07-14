"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function OwnerGateClient() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") || "/";
  const [key, setKey] = useState("");
  const [error, setError] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim()) {
      setError("Введите ключ владельца");
      return;
    }
    const url = new URL(window.location.href);
    url.pathname = next;
    url.searchParams.set("owner", key.trim());
    url.searchParams.delete("next");
    router.replace(url.toString());
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-genesis-bg px-4">
      <div className="w-full max-w-md rounded-2xl border border-amber-500/30 bg-genesis-panel p-8">
        <p className="text-xs uppercase tracking-[0.35em] text-amber-300/80">Virtus Core</p>
        <h1 className="mt-2 text-2xl font-bold text-white">Доступ только для владельца</h1>
        <p className="mt-3 text-sm text-genesis-muted">
          Beta закрыта для публики. Ежедневная работа — через <strong className="text-white">Genesis.exe</strong>{" "}
          (localhost). Для beta нужен ключ CEO.
        </p>
        <form onSubmit={submit} className="mt-6 space-y-3">
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="Ключ владельца"
            className="w-full rounded-xl border border-genesis-border bg-genesis-bg px-4 py-3 text-sm"
          />
          {error ? <p className="text-xs text-rose-300">{error}</p> : null}
          <button type="submit" className="w-full rounded-xl bg-amber-600 py-3 text-sm font-semibold text-white">
            Войти
          </button>
        </form>
      </div>
    </main>
  );
}
