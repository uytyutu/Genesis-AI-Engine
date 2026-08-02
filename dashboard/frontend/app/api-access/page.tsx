"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { publicApiBase } from "../lib/publicApiBase";
import { BRAND_NAME } from "../lib/publicBrand";

const API = publicApiBase();

type ApiPackage = {
  id: string;
  name: string;
  price_eur: number;
  balance_eur: number;
  scopes: string[];
  note_ru?: string;
  best_for_ru?: string;
};

type CheckoutResult = {
  ok?: boolean;
  provider?: string;
  checkout_url?: string;
  session_id?: string;
  sandbox?: boolean;
  package_id?: string;
  price_eur?: number;
  fulfilled?: {
    ok?: boolean;
    api_key?: string;
    key_id?: string;
    balance_eur?: number;
    package_id?: string;
    email_sent?: boolean;
  };
};

type ConfirmResult = {
  ok?: boolean;
  api_key?: string;
  key_prefix?: string;
  balance_eur?: number;
  package_id?: string;
  customer_email?: string;
  note_ru?: string;
  already_processed?: boolean;
  email_sent?: boolean;
};

function ApiAccessInner() {
  const search = useSearchParams();
  const paid = search.get("paid") === "1";
  const sessionId = (search.get("session_id") || "").trim();
  const prePackage = (search.get("package") || "micro").trim() || "micro";

  const [packages, setPackages] = useState<ApiPackage[]>([]);
  const [packageId, setPackageId] = useState(prePackage);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [confirmNote, setConfirmNote] = useState("");
  const [confirmMeta, setConfirmMeta] = useState<ConfirmResult | null>(null);

  const selected = useMemo(
    () => packages.find((p) => p.id === packageId) || packages[0],
    [packages, packageId],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API}/api/v1/packages`);
        if (!res.ok) throw new Error("packages");
        const data = await res.json();
        const list = (data.packages || []) as ApiPackage[];
        if (!cancelled) {
          setPackages(list);
          if (!list.some((p) => p.id === packageId) && list[0]) {
            setPackageId(list[0].id);
          }
        }
      } catch {
        if (!cancelled) setError("Не удалось загрузить пакеты — запустите Genesis.exe");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [packageId]);

  useEffect(() => {
    if (!paid || !sessionId || sessionId.startsWith("sandbox-")) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${API}/api/v1/checkout/confirm?session_id=${encodeURIComponent(sessionId)}`,
        );
        const data = (await res.json().catch(() => ({}))) as ConfirmResult & {
          detail?: ConfirmResult;
        };
        const body = (data.detail && typeof data.detail === "object" ? data.detail : data) as ConfirmResult;
        if (cancelled) return;
        if (res.ok && body.ok) {
          setConfirmMeta(body);
          setConfirmNote(body.note_ru || "Оплата подтверждена.");
          if (body.api_key) setApiKey(body.api_key);
        } else {
          setConfirmNote(
            body.note_ru ||
              "Оплата принята. Ключ придёт на email (webhook) — обновите страницу через минуту.",
          );
        }
      } catch {
        if (!cancelled) {
          setConfirmNote("Не удалось подтвердить сессию — проверьте email или обновите позже.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [paid, sessionId]);

  const buy = useCallback(async () => {
    setError("");
    setApiKey("");
    setConfirmNote("");
    if (!email.includes("@")) {
      setError("Укажите email — туда придёт API-ключ.");
      return;
    }
    const pkg = selected?.id || packageId || "micro";
    setLoading(true);
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      const res = await fetch(`${API}/api/v1/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          package_id: pkg,
          customer_email: email.trim(),
          success_url: `${origin}/api-access?paid=1&session_id={CHECKOUT_SESSION_ID}`,
          cancel_url: `${origin}/api-access`,
        }),
      });
      const data = (await res.json().catch(() => ({}))) as CheckoutResult & {
        detail?: CheckoutResult | string;
      };
      if (!res.ok) {
        const detail = data.detail;
        const reason =
          typeof detail === "object" && detail
            ? String((detail as CheckoutResult & { reason?: string }).reason || "checkout_failed")
            : typeof detail === "string"
              ? detail
              : "checkout_failed";
        throw new Error(reason);
      }
      const fulfilled = data.fulfilled;
      if (data.sandbox && fulfilled?.api_key) {
        setApiKey(fulfilled.api_key);
        setConfirmNote(
          `Sandbox · пакет ${fulfilled.package_id || pkg} · баланс ${fulfilled.balance_eur ?? "?"} €`,
        );
        return;
      }
      const url = data.checkout_url;
      if (url) {
        window.location.href = url;
        return;
      }
      throw new Error("no_checkout_url");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "checkout_failed";
      if (msg.includes("payment_not_configured") || msg.includes("stripe")) {
        setError("Stripe не настроен. CEO: STRIPE_SECRET_KEY в .env.local или GENESIS_PAYMENT_SANDBOX=1.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }, [email, packageId, selected]);

  return (
    <PublicPageShell customerDecisionFlow>
      <div className="mx-auto max-w-2xl space-y-8 py-4">
        <header className="space-y-3 text-center">
          <p className="text-xs uppercase tracking-[0.2em] text-genesis-muted">
            Platform API · {BRAND_NAME}
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            API Access
          </h1>
          <p className="text-sm text-genesis-muted sm:text-base">
            Prepaid audit / leads через ключ. Начните с Micro за 5 € — ключ сразу после оплаты.
          </p>
        </header>

        {paid ? (
          <section className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-5 space-y-3">
            <h2 className="text-lg font-medium text-emerald-100">Оплата получена</h2>
            <p className="text-sm text-emerald-100/80">
              {confirmNote || "Спасибо. Ключ отправлен на email и показан ниже, если доступен."}
            </p>
            {confirmMeta?.key_prefix && !apiKey ? (
              <p className="text-xs text-genesis-muted">
                Префикс ключа: <code>{confirmMeta.key_prefix}…</code>
              </p>
            ) : null}
          </section>
        ) : null}

        {apiKey ? (
          <section className="rounded-2xl border border-white/15 bg-white/5 p-5 space-y-3">
            <h2 className="text-lg font-medium text-white">Ваш API-ключ</h2>
            <p className="text-xs text-amber-200/90">
              Сохраните сейчас — полный ключ больше не покажем (только email).
            </p>
            <pre className="overflow-x-auto rounded-xl bg-black/40 p-3 text-sm text-emerald-200">
              {apiKey}
            </pre>
            <pre className="overflow-x-auto rounded-xl bg-black/30 p-3 text-xs text-genesis-muted">{`curl -X POST ${typeof window !== "undefined" ? window.location.origin : ""}/api/v1/audit \\
  -H "X-API-Key: ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{"url":"https://example.com","locale":"de"}'`}</pre>
          </section>
        ) : null}

        <section className="space-y-4">
          <h2 className="text-lg font-medium text-white">Пакеты</h2>
          <div className="grid gap-3">
            {packages.map((pkg) => {
              const active = (selected?.id || packageId) === pkg.id;
              const isMicro = pkg.id === "micro";
              return (
                <button
                  key={pkg.id}
                  type="button"
                  onClick={() => setPackageId(pkg.id)}
                  className={`rounded-2xl border p-4 text-left transition ${
                    active
                      ? "border-genesis-accent bg-genesis-accent/10"
                      : "border-white/10 bg-white/[0.03] hover:border-white/25"
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">
                        {pkg.name}
                        {isMicro ? (
                          <span className="ml-2 text-xs font-normal text-genesis-accent">
                            первый шаг
                          </span>
                        ) : null}
                      </p>
                      <p className="mt-1 text-xs text-genesis-muted">
                        {pkg.best_for_ru || pkg.note_ru || pkg.scopes.join(", ")}
                      </p>
                    </div>
                    <p className="shrink-0 text-xl font-semibold text-white">
                      {Number(pkg.price_eur).toFixed(0)} €
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        <section className="space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <label className="block space-y-1.5">
            <span className="text-sm text-genesis-muted">Email для ключа</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="w-full rounded-xl border border-white/15 bg-black/30 px-3 py-2.5 text-white outline-none focus:border-genesis-accent"
              autoComplete="email"
            />
          </label>
          {error ? (
            <p className="rounded-xl border border-amber-500/30 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
              {error}
            </p>
          ) : null}
          <button
            type="button"
            disabled={loading || !selected}
            onClick={() => void buy()}
            className="w-full rounded-xl bg-genesis-accent px-4 py-3 text-sm font-semibold text-white shadow-glow disabled:opacity-50 hover:brightness-110"
          >
            {loading
              ? "Открываем оплату…"
              : `Купить ${selected?.name || "Micro"} · ${Number(selected?.price_eur || 5).toFixed(0)} €`}
          </button>
          <p className="text-center text-xs text-genesis-muted">
            Stripe Checkout · ключ `vk_live_…` · scopes: {(selected?.scopes || ["audit"]).join(", ")}
          </p>
        </section>

        <p className="text-center text-xs text-genesis-muted">
          Нужен сайт под ключ?{" "}
          <Link href="/services" className="text-genesis-accent hover:underline">
            Услуги
          </Link>
          {" · "}
          <Link href="/site" className="text-genesis-accent hover:underline">
            Vector
          </Link>
        </p>
      </div>
    </PublicPageShell>
  );
}

export default function ApiAccessPage() {
  return (
    <Suspense
      fallback={
        <PublicPageShell>
          <p className="py-16 text-center text-sm text-genesis-muted">Загрузка…</p>
        </PublicPageShell>
      }
    >
      <ApiAccessInner />
    </Suspense>
  );
}
