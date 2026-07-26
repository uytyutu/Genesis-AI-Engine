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

type StartResponse = {
  ok?: boolean;
  email?: string;
  delivery?: string;
  dev_code?: string;
  detail?: string;
};

type ConfirmResponse = {
  token?: string;
  name?: string;
  detail?: string;
};

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const nextPath = params.get("next") || "/client";
  const [step, setStep] = useState<"form" | "code">("form");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [devCode, setDevCode] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function safeNext(): string {
    return nextPath.startsWith("/") && !nextPath.startsWith("//")
      ? nextPath
      : "/client";
  }

  async function onStart(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setDevCode(null);
    try {
      const res = await fetch(`${publicApiBase()}/api/client/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
          locale: (navigator.language || "en").slice(0, 2),
        }),
      });
      const body = (await res.json().catch(() => ({}))) as StartResponse;
      if (!res.ok) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : `register_${res.status}`,
        );
      }
      if (body.dev_code) setDevCode(body.dev_code);
      setStep("code");
    } catch (err) {
      setError(err instanceof Error ? err.message : "register_failed");
    } finally {
      setBusy(false);
    }
  }

  async function onConfirm(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${publicApiBase()}/api/client/register/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          code: code.trim(),
        }),
      });
      const body = (await res.json().catch(() => ({}))) as ConfirmResponse;
      if (!res.ok || !body.token) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : `confirm_${res.status}`,
        );
      }
      setClientSession(body.token, body.name);
      await bridgePortalSession(email.trim(), password);
      router.replace(safeNext());
    } catch (err) {
      setError(err instanceof Error ? err.message : "confirm_failed");
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
        Optional. You can buy a website or AI bot without an account. Register
        only if you want your office — projects, bots, automation, package
        upgrades.
      </p>

      {step === "form" ? (
        <form onSubmit={onStart} className="mt-8 space-y-4">
          <label className="block text-sm text-zinc-300">
            Full name
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-base text-white"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              autoCapitalize="words"
              minLength={2}
              required
            />
          </label>
          <label className="block text-sm text-zinc-300">
            Email
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-base text-white"
              type="email"
              inputMode="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm text-zinc-300">
            Password (min 8 characters)
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-base text-white"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
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
            {busy ? "Sending code…" : "Send verification code"}
          </button>
        </form>
      ) : (
        <form onSubmit={onConfirm} className="mt-8 space-y-4">
          <p className="text-sm text-zinc-300">
            We sent a code to <span className="text-white">{email.trim()}</span>.
            Enter it below to finish registration.
          </p>
          {devCode ? (
            <p className="rounded-lg border border-amber-500/30 bg-amber-950/40 px-3 py-2 text-sm text-amber-100">
              Local mode — code: <strong className="tracking-widest">{devCode}</strong>
            </p>
          ) : null}
          <label className="block text-sm text-zinc-300">
            Verification code
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-center text-xl tracking-[0.35em] text-white"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 8))}
              minLength={4}
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
            {busy ? "Creating account…" : "Confirm and open office"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setStep("form");
              setCode("");
              setError(null);
            }}
            className="w-full text-sm text-zinc-400 hover:text-white"
          >
            ← Change email or password
          </button>
        </form>
      )}

      <p className="mt-6 text-sm text-zinc-400">
        Prefer to buy without an account?{" "}
        <Link href="/site" className="text-emerald-300 hover:underline">
          Back to services
        </Link>
      </p>
      <p className="mt-3 text-sm text-zinc-400">
        Already registered?{" "}
        <Link
          href={`/client/login${nextPath !== "/client" ? `?next=${encodeURIComponent(nextPath)}` : ""}`}
          className="text-emerald-300 hover:underline"
        >
          Sign in
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
