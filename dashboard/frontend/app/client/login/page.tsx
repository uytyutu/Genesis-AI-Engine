"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { publicApiBase } from "../../lib/publicApiBase";
import {
  bridgePortalSession,
  setClientSession,
} from "../../lib/clientAuth";
import { BRAND_NAME } from "../../lib/publicBrand";

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
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4 py-10">
      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-emerald-300/90">
        {BRAND_NAME}
      </p>
      <h1 className="mt-3 text-3xl font-semibold text-white">
        Sign in to your office
      </h1>
      <p className="mt-2 text-sm text-zinc-400">
        Your personal workspace for projects, bots, and automation. Buying a
        website or bot does not require sign-in.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block text-sm text-zinc-300">
          Email
          <input
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-base text-white"
            type="email"
            inputMode="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm text-zinc-300">
          Password
          <input
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-base text-white"
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
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="mt-6 text-sm text-zinc-300">
        New here?{" "}
        <Link
          href={`/client/register${nextPath !== "/client" ? `?next=${encodeURIComponent(nextPath)}` : ""}`}
          className="font-semibold text-emerald-300 hover:underline"
        >
          Create personal account
        </Link>
      </p>
      <p className="mt-4 text-sm text-zinc-400">
        <Link href="/site" className="text-emerald-300 hover:underline">
          ← Buy without account
        </Link>
      </p>
    </div>
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
