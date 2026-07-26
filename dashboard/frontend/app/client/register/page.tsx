"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { PortalApiError, portalFetch } from "../../lib/portalApi";
import { BRAND_NAME } from "../../lib/publicBrand";

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const nextPath = params.get("next") || "/client";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await portalFetch<{ authenticated: boolean }>(
        "/portal/register",
        {
          method: "POST",
          body: JSON.stringify({
            email: email.trim(),
            password,
            display_name: displayName.trim(),
          }),
        },
      );
      if (!res.authenticated) {
        throw new PortalApiError(400, "register_failed");
      }
      const safeNext =
        nextPath.startsWith("/") && !nextPath.startsWith("//")
          ? nextPath
          : "/client";
      router.replace(safeNext);
    } catch (err) {
      if (err instanceof PortalApiError) setError(err.detail);
      else if (err instanceof Error) setError(err.message);
      else setError("register_failed");
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
        Create personal account
      </h1>
      <p className="mt-2 text-sm text-zinc-400">
        One account for ordering a website, buying an AI bot, and managing your
        products. No owner approval needed.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block text-sm text-zinc-300">
          Name (optional)
          <input
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            autoComplete="name"
          />
        </label>
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
          Password (min 6 characters)
          <input
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={6}
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
          {busy ? "Creating…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-zinc-400">
        Already have an account?{" "}
        <Link
          href={`/client/login${nextPath !== "/client" ? `?next=${encodeURIComponent(nextPath)}` : ""}`}
          className="text-emerald-300 hover:underline"
        >
          Sign in
        </Link>
      </p>
      <p className="mt-4 text-sm text-zinc-400">
        <Link href="/site" className="text-emerald-300 hover:underline">
          ← Back to public site
        </Link>
      </p>
    </div>
  );
}

export default function ClientRegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-md px-4 py-20 text-sm text-zinc-400">
          Loading…
        </div>
      }
    >
      <RegisterForm />
    </Suspense>
  );
}
