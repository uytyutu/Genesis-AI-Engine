"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { PortalApiError, portalFetch } from "../../lib/portalApi";
import { BRAND_NAME } from "../../lib/publicBrand";

const DEMO_EMAIL = "client@virtus.local";
const DEMO_PASSWORD = "demo-vector";

export default function ClientLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await portalFetch<{ authenticated: boolean }>("/portal/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      if (!res.authenticated) {
        throw new PortalApiError(401, "login_failed");
      }
      router.replace("/client");
    } catch (err) {
      if (err instanceof PortalApiError) setError(err.detail);
      else if (err instanceof Error) setError(err.message);
      else setError("login_failed");
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
        Welcome to {BRAND_NAME}
      </h1>
      <p className="mt-2 text-sm text-zinc-400">
        Sign in to your digital workspace — products, Vector, orders, and billing.
        Not just a download page.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block text-sm text-zinc-300">
          Email
          <input
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm text-zinc-300">
          Password
          <input
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
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
          className="w-full rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-50"
        >
          {busy ? "Signing in…" : "Enter workspace"}
        </button>
      </form>

      <p className="mt-6 text-xs text-zinc-500">
        Demo: {DEMO_EMAIL} / {DEMO_PASSWORD}
      </p>
      <p className="mt-4 text-sm text-zinc-400">
        <Link href="/site" className="text-emerald-300 hover:underline">
          ← Back to public site
        </Link>
      </p>
    </div>
  );
}
