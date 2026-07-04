"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { PackageSkeleton } from "../components/Skeleton";
import { formatEur } from "../lib/formatEur";
import { formatApiDetail } from "../lib/formatApiError";
import { startOrderCheckout } from "../lib/orderCheckout";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const INPUT =
  "w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white outline-none focus:border-genesis-accent";

type Package = {
  id: string;
  name: string;
  price_eur: number;
  deliverables: string[];
};

function suggestPackage(needsLogo: boolean, needsDomain: boolean, extra: string): string {
  if (needsDomain) return "premium";
  if (needsLogo || extra.trim().length > 120) return "business";
  return "basic";
}

export default function OrderSitePage() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [packagesLoading, setPackagesLoading] = useState(true);
  const [businessName, setBusinessName] = useState("");
  const [description, setDescription] = useState("");
  const [city, setCity] = useState("");
  const [phone, setPhone] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [email, setEmail] = useState("");
  const [needsLogo, setNeedsLogo] = useState(false);
  const [needsDomain, setNeedsDomain] = useState(false);
  const [extraWishes, setExtraWishes] = useState("");
  const [packageId, setPackageId] = useState("basic");
  const [manualPackage, setManualPackage] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState<{
    order_id: string;
    message: string;
    package_name: string;
    price_eur: number;
    deliverables: string[];
  } | null>(null);
  const [payBusy, setPayBusy] = useState(false);
  const [payError, setPayError] = useState("");
  const [paymentReady, setPaymentReady] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/sales/payment-status`)
      .then((r) => r.json())
      .then((body) => setPaymentReady(Boolean(body.configured)))
      .catch(() => setPaymentReady(false));
  }, []);

  useEffect(() => {
    fetch(`${API}/api/sales/packages`)
      .then((r) => r.json())
      .then((body) => setPackages(body.packages ?? []))
      .catch(() => setPackages([]))
      .finally(() => setPackagesLoading(false));
  }, []);

  const suggestedId = useMemo(
    () => suggestPackage(needsLogo, needsDomain, extraWishes),
    [needsLogo, needsDomain, extraWishes]
  );

  useEffect(() => {
    if (!manualPackage) setPackageId(suggestedId);
  }, [suggestedId, manualPackage]);

  const selected = packages.find((p) => p.id === packageId) ?? packages[0];

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      setError("Укажите email — на него придёт подтверждение и ссылка на оплату");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/sales/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: businessName.trim(),
          description: description.trim(),
          city: city.trim() || null,
          phone: phone.trim() || null,
          whatsapp: whatsapp.trim() || null,
          email: email.trim() || null,
          needs_logo: needsLogo,
          needs_domain: needsDomain,
          extra_wishes: extraWishes.trim() || null,
          package_id: packageId,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(formatApiDetail(body.detail) || "Не удалось отправить заявку");
        return;
      }
      setDone({
        order_id: body.order_id,
        message: body.message,
        package_name: body.package_name,
        price_eur: body.price_eur,
        deliverables: body.deliverables ?? [],
      });
    } catch {
      setError("Сервер недоступен. Попробуйте позже.");
    } finally {
      setBusy(false);
    }
  }

  async function payNow() {
    if (!done) return;
    setPayBusy(true);
    setPayError("");
    try {
      const url = await startOrderCheckout(done.order_id);
      window.location.href = url;
    } catch (e) {
      setPayError(e instanceof Error ? e.message : "Сервер недоступен");
      setPayBusy(false);
    }
  }

  if (done) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-2xl py-4">
          <OrderSteps current={paymentReady ? 3 : 2} />
        <div className="rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/30 to-genesis-panel p-8 text-center shadow-glow">
          <p className="text-4xl">✓</p>
          <h1 className="mt-4 text-2xl font-bold">Спасибо!</h1>
          <p className="mt-3 text-genesis-muted">{done.message}</p>
          <p className="mt-2 text-xs text-genesis-muted">Заказ № {done.order_id}</p>
          <div className="mt-6 rounded-2xl border border-genesis-border-subtle bg-genesis-bg/40 p-5 text-left">
            <p className="text-sm text-genesis-muted">Ваш проект оценён</p>
            <p className="mt-1 text-xl font-semibold">
              {done.package_name} — {formatEur(done.price_eur)}
            </p>
            <p className="mt-4 genesis-label">Вы получите</p>
            <ul className="mt-2 space-y-1.5 text-sm">
              {done.deliverables.map((d) => (
                <li key={d} className="flex gap-2">
                  <span className="text-emerald-400">✔</span>
                  <span>{d}</span>
                </li>
              ))}
            </ul>
          </div>
          {paymentReady ? (
            <div className="mt-6 space-y-3">
              <button
                type="button"
                disabled={payBusy}
                onClick={payNow}
                className="w-full rounded-xl bg-gradient-to-r from-emerald-500 to-genesis-accent py-3.5 text-sm font-semibold text-white shadow-glow disabled:opacity-50"
              >
                {payBusy ? "Переход к оплате…" : `Оплатить ${formatEur(done.price_eur)}`}
              </button>
              {payError && <p className="text-xs text-rose-300">{payError}</p>}
            </div>
          ) : (
            <p className="mt-6 text-sm text-amber-200/90">
              Оплата временно недоступна — мы свяжемся с вами для выставления счёта.
            </p>
          )}
          <Link
            href={`/order/status/${done.order_id}`}
            className="mt-4 inline-block text-sm text-genesis-accent hover:underline"
          >
            Отслеживать статус заказа →
          </Link>
        </div>
        </main>
      </PublicPageShell>
    );
  }

  const step = 1;

  return (
    <PublicPageShell>
    <main className="mx-auto max-w-4xl py-2">
      <OrderSteps current={step} />
      <div className="mb-8 text-center">
        <p className="genesis-label tracking-[0.3em] text-genesis-accent">Genesis</p>
        <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Заказать сайт</h1>
        <p className="mt-2 text-genesis-muted">
          Ответьте на несколько вопросов — мы сразу покажем цену и что вы получите
        </p>
        <p className="mx-auto mt-4 max-w-2xl text-sm text-genesis-muted/90">
          Создано и сопровождается командой ИИ Genesis. Вы выходите онлайн быстрее и
          экономите недели работы и тысячи евро по сравнению с классической разработкой.
        </p>
      </div>

      <form onSubmit={submit} className="grid gap-6 lg:grid-cols-5">
        <div className="space-y-4 lg:col-span-3">
          <Field label="Название бизнеса" required>
            <input
              className={`${INPUT}`}
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="Например: Стоматология Дента"
              required
            />
          </Field>
          <Field label="Чем занимаетесь" required>
            <textarea
              className={`${INPUT} min-h-[88px]`}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Кратко: услуги, для кого, чем отличаетесь"
              required
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Город">
              <input
                className={`${INPUT}`}
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Берлин"
              />
            </Field>
            <Field label="Телефон">
              <input
                className={`${INPUT}`}
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+49 …"
              />
            </Field>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="WhatsApp">
              <input
                className={`${INPUT}`}
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                placeholder="+49 …"
              />
            </Field>
            <Field label="Email" required>
              <input
                className={`${INPUT}`}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="hello@…"
                required
              />
            </Field>
          </div>
          <div className="flex flex-wrap gap-4">
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={needsLogo}
                onChange={(e) => setNeedsLogo(e.target.checked)}
                className="rounded"
              />
              Нужен логотип
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={needsDomain}
                onChange={(e) => setNeedsDomain(e.target.checked)}
                className="rounded"
              />
              Нужен домен
            </label>
          </div>
          <Field label="Дополнительные пожелания">
            <textarea
              className={`${INPUT} min-h-[72px]`}
              value={extraWishes}
              onChange={(e) => setExtraWishes(e.target.value)}
              placeholder="Цвета, примеры сайтов, особые блоки…"
            />
          </Field>
        </div>

        <aside className="lg:col-span-2">
          <div className="sticky top-4 space-y-4 rounded-2xl border border-genesis-accent/25 bg-genesis-panel/80 p-5">
            <p className="genesis-label">Пакет и стоимость</p>
            {packagesLoading ? (
              <PackageSkeleton />
            ) : (
            <div className="space-y-2">
              {packages.map((p) => (
                <label
                  key={p.id}
                  className={`flex cursor-pointer items-center justify-between rounded-xl border px-3 py-2.5 text-sm transition ${
                    packageId === p.id
                      ? "border-genesis-accent/50 bg-genesis-accent/10"
                      : "border-genesis-border-subtle hover:border-genesis-accent/30"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="package"
                      checked={packageId === p.id}
                      onChange={() => {
                        setManualPackage(true);
                        setPackageId(p.id);
                      }}
                    />
                    {p.name}
                  </span>
                  <span className="font-semibold tabular-nums">{formatEur(p.price_eur)}</span>
                </label>
              ))}
            </div>
            )}
            {!manualPackage && selected && (
              <p className="text-xs text-genesis-muted">
                Рекомендуем: {selected.name} — по вашим ответам
              </p>
            )}
            {selected && (
              <>
                <p className="genesis-label mt-4">Что вы получите</p>
                <ul className="space-y-1.5 text-xs">
                  {selected.deliverables.map((d) => (
                    <li key={d} className="flex gap-2">
                      <span className="text-emerald-400">✔</span>
                      <span>{d}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
            <button
              type="submit"
              disabled={busy}
              className="mt-4 w-full rounded-xl bg-gradient-to-r from-genesis-accent to-blue-600 py-3 text-sm font-semibold text-white shadow-glow disabled:opacity-50"
            >
              {busy ? "Отправка…" : "Оставить заявку"}
            </button>
            {error && <p className="text-xs text-rose-300">{error}</p>}
            <p className="text-[10px] text-genesis-muted">
              Оплата — после подтверждения. Без скрытых платежей.
            </p>
          </div>
        </aside>
      </form>

      <p className="mt-6 text-center text-xs text-genesis-muted">
        Нажимая «Оставить заявку», вы соглашаетесь с{" "}
        <Link href="/agb" className="text-genesis-accent hover:underline">
          AGB
        </Link>{" "}
        и{" "}
        <Link href="/datenschutz" className="text-genesis-accent hover:underline">
          Datenschutz
        </Link>
        .
      </p>
    </main>
    </PublicPageShell>
  );
}

function OrderSteps({ current }: { current: number }) {
  const steps = [
    { n: 1, label: "Анкета" },
    { n: 2, label: "Подтверждение" },
    { n: 3, label: "Оплата" },
  ];
  return (
    <ol className="mb-8 flex justify-center gap-2 sm:gap-4" aria-label="Шаги заказа">
      {steps.map((s) => (
        <li
          key={s.n}
          className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs sm:text-sm ${
            s.n === current
              ? "bg-genesis-accent/20 text-white"
              : s.n < current
                ? "text-emerald-400"
                : "text-genesis-muted"
          }`}
        >
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold ${
              s.n === current ? "bg-genesis-accent text-white" : "bg-white/5"
            }`}
          >
            {s.n}
          </span>
          {s.label}
        </li>
      ))}
    </ol>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="genesis-label">
        {label}
        {required && <span className="text-rose-400"> *</span>}
      </span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}
