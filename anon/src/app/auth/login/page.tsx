"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useI18n } from "@/components/I18nProvider";

function LoginForm() {
  const { t } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const r = await fetch("/api/auth/login", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const d = await r.json();
    setBusy(false);
    if (!r.ok) {
      setError(d.error || t("error.generic"));
      return;
    }
    const next = params.get("next") || "/dashboard";
    router.refresh();
    window.location.href = next;
  }

  return (
    <main className="anon-card mx-auto max-w-md p-6">
      <h1 className="text-2xl font-semibold">{t("auth.loginTitle")}</h1>
      <form className="mt-6 space-y-4" onSubmit={onSubmit}>
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
          {t("auth.submitLogin")}
        </button>
      </form>
      <p className="mt-4 text-sm anon-muted">
        <Link href="/auth/register" className="underline">
          {t("nav.register")}
        </Link>
      </p>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
