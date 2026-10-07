"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useI18n } from "@/components/I18nProvider";

function RegisterForm() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const r = await fetch("/api/auth/register", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, displayName, language: locale }),
    });
    const d = await r.json();
    setBusy(false);
    if (!r.ok) {
      setError(d.error || t("error.generic"));
      return;
    }
    // Session cookie is already set by the API — land in cabinet as logged-in.
    const next = params.get("next") || "/dashboard";
    router.refresh();
    window.location.href = next;
  }

  return (
    <main className="anon-card mx-auto max-w-md p-6">
      <h1 className="text-2xl font-semibold">{t("auth.registerTitle")}</h1>
      <p className="mt-2 text-sm anon-muted">{t("auth.registerSub")}</p>
      <form className="mt-6 space-y-4" onSubmit={onSubmit}>
        <label className="block text-sm">
          {t("auth.name")}
          <input
            className="anon-input mt-2"
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          {t("auth.email")}
          <input
            className="anon-input mt-2"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          {t("auth.password")}
          <input
            className="anon-input mt-2"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="text-sm text-rose-300">{error}</p>}
        <button className="anon-btn anon-btn-primary w-full" disabled={busy} type="submit">
          {t("auth.submitRegister")}
        </button>
      </form>
      <p className="mt-4 text-sm anon-muted">
        <Link href="/auth/login" className="underline">
          {t("nav.login")}
        </Link>
      </p>
    </main>
  );
}

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}
