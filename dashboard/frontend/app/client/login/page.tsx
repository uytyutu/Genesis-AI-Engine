"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { ClientAuthShell } from "../../components/ClientAuthShell";
import { publicApiBase } from "../../lib/publicApiBase";
import {
  bridgePortalSession,
  setClientSession,
} from "../../lib/clientAuth";

type LoginResponse = {
  token?: string;
  name?: string;
  detail?: string;
};

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const nextPath = params.get("next") || "/client";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${publicApiBase()}/api/client/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const body = (await res.json().catch(() => ({}))) as LoginResponse;
      if (!res.ok || !body.token) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : "invalid_credentials",
        );
      }
      setClientSession(body.token, body.name);
      await bridgePortalSession(email.trim(), password);
      const safeNext =
        nextPath.startsWith("/") && !nextPath.startsWith("//")
          ? nextPath
          : "/client";
      router.replace(safeNext);
    } catch (err) {
      setError(err instanceof Error ? err.message : "login_failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ClientAuthShell
      title="Вход в кабинет"
      subtitle="Личный кабинет для проектов, ботов и автоматизации. Покупка сайта или AI Assistant не требует входа."
      footer={
        <>
          <p>
            Нет аккаунта?{" "}
            <Link
              href={`/client/register${nextPath !== "/client" ? `?next=${encodeURIComponent(nextPath)}` : ""}`}
              className="font-semibold text-emerald-300 hover:underline"
            >
              Создать аккаунт
            </Link>
          </p>
          <p>
            <Link href="/site" className="text-emerald-300 hover:underline">
              ← Купить без аккаунта
            </Link>
          </p>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block text-sm text-zinc-300">
          Email
          <input
            className="mt-1.5 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-base text-white outline-none ring-emerald-400/0 transition focus:border-emerald-400/40 focus:ring-2 focus:ring-emerald-400/20"
            type="email"
            inputMode="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm text-zinc-300">
          Пароль
          <input
            className="mt-1.5 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-base text-white outline-none ring-emerald-400/0 transition focus:border-emerald-400/40 focus:ring-2 focus:ring-emerald-400/20"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error ? (
          <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
            {error}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-50"
        >
          {busy ? "Вход…" : "Войти"}
        </button>
      </form>
    </ClientAuthShell>
  );
}

export default function ClientLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-md px-4 py-20 text-sm text-zinc-400">
          Loading…
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
