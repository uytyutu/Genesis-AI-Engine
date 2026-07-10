"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { PackageSkeleton } from "../components/Skeleton";
import { formatEur } from "../lib/formatEur";
import { formatApiDetail } from "../lib/formatApiError";
import { startOrderCheckout } from "../lib/orderCheckout";
import { parseOrderPurchaseType } from "../lib/orderTrustCard";
import { OrderTrustCard } from "../components/OrderTrustCard";
import { Badge, Button, ButtonLink, Card, Field, Input, Textarea } from "../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  const [purchaseType, setPurchaseType] = useState<"one_time" | "subscription">("one_time");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const pkg = params.get("package");
    if (pkg && ["basic", "business", "premium"].includes(pkg)) {
      setPackageId(pkg);
      setManualPackage(true);
    }
    setPurchaseType(parseOrderPurchaseType(params.get("purchase_type")));
  }, []);

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
          <Card glow className="text-center" padding="lg">
            <p className="text-4xl text-emerald-400" aria-hidden>
              ✓
            </p>
            <h1 className="mt-4 text-2xl font-bold">Спасибо!</h1>
            <p className="mt-3 text-genesis-muted">{done.message}</p>
            <Badge variant="muted" className="mt-3">
              № {done.order_id}
            </Badge>
            <Card hover={false} className="mt-6 text-left" padding="md">
              <p className="text-sm text-genesis-muted">Ваш проект оценён</p>
              <p className="mt-1 text-xl font-semibold">
                {done.package_name} — {formatEur(done.price_eur)}
              </p>
              <p className="genesis-label mt-4">Вы получите</p>
              <ul className="mt-2 space-y-1.5 text-sm">
                {done.deliverables.map((d) => (
                  <li key={d} className="flex gap-2">
                    <span className="text-emerald-400">✔</span>
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            </Card>
            {paymentReady ? (
              <div className="mt-6 space-y-3">
                <OrderTrustCard purchaseType={purchaseType} />
                <Button variant="success" size="lg" fullWidth loading={payBusy} onClick={payNow}>
                  {payBusy ? "Переход к оплате…" : `Оплатить ${formatEur(done.price_eur)}`}
                </Button>
                {payError && (
                  <p className="text-xs text-rose-300" role="alert">
                    {payError}
                  </p>
                )}
              </div>
            ) : (
              <p className="mt-6 text-sm text-amber-200/90">
                Оплата временно недоступна — мы свяжемся с вами для выставления счёта.
              </p>
            )}
            <ButtonLink
              href={`/order/status/${done.order_id}`}
              variant="ghost"
              size="sm"
              className="mt-4"
            >
              Отслеживать статус заказа →
            </ButtonLink>
          </Card>
        </main>
      </PublicPageShell>
    );
  }

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-4xl py-2">
        <OrderSteps current={1} />
        <div className="mb-8 text-center animate-fade-up">
          <Badge variant="accent" className="tracking-[0.2em]">
            Virtus Core
          </Badge>
          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">Заказать сайт</h1>
          <p className="mt-2 text-genesis-muted">
            Ответьте на несколько вопросов — мы сразу покажем цену и что вы получите
          </p>
        </div>

        <form onSubmit={submit} className="grid gap-6 lg:grid-cols-5">
          <div className="space-y-4 lg:col-span-3">
            <Field label="Название бизнеса" required>
              <Input
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="Например: Стоматология Дента"
                required
              />
            </Field>
            <Field label="Чем занимаетесь" required>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Кратко: услуги, для кого, чем отличаетесь"
                required
              />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Город">
                <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Берлин" />
              </Field>
              <Field label="Телефон">
                <Input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+49 …"
                />
              </Field>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="WhatsApp">
                <Input value={whatsapp} onChange={(e) => setWhatsapp(e.target.value)} placeholder="+49 …" />
              </Field>
              <Field label="Email" required error={error && !email.trim() ? error : undefined}>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="hello@…"
                  required
                  error={Boolean(error && !email.trim())}
                />
              </Field>
            </div>
            <div className="flex flex-wrap gap-4">
              <label className="flex cursor-pointer items-center gap-2 text-sm transition-smooth hover:text-white">
                <input
                  type="checkbox"
                  checked={needsLogo}
                  onChange={(e) => setNeedsLogo(e.target.checked)}
                  className="rounded border-genesis-border accent-genesis-accent"
                />
                Нужен логотип
              </label>
              <label className="flex cursor-pointer items-center gap-2 text-sm transition-smooth hover:text-white">
                <input
                  type="checkbox"
                  checked={needsDomain}
                  onChange={(e) => setNeedsDomain(e.target.checked)}
                  className="rounded border-genesis-border accent-genesis-accent"
                />
                Нужен домен
              </label>
            </div>
            <Field label="Дополнительные пожелания">
              <Textarea
                className="min-h-[72px]"
                value={extraWishes}
                onChange={(e) => setExtraWishes(e.target.value)}
                placeholder="Цвета, примеры сайтов, особые блоки…"
              />
            </Field>
          </div>

          <aside className="lg:col-span-2">
            <Card glow className="sticky top-4" padding="md">
              <p className="genesis-label">Пакет и стоимость</p>
              {packagesLoading ? (
                <PackageSkeleton />
              ) : packages.length === 0 ? (
                <p className="mt-4 text-sm text-genesis-muted">Не удалось загрузить пакеты</p>
              ) : (
                <div className="mt-3 space-y-2">
                  {packages.map((p) => (
                    <label
                      key={p.id}
                      className={`flex cursor-pointer items-center justify-between rounded-xl border px-3 py-2.5 text-sm transition-smooth ${
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
                          className="accent-genesis-accent"
                        />
                        {p.name}
                      </span>
                      <span className="font-semibold tabular-nums">{formatEur(p.price_eur)}</span>
                    </label>
                  ))}
                </div>
              )}
              {!manualPackage && selected && (
                <p className="mt-2 text-xs text-genesis-muted">
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
              <Button type="submit" variant="primary" size="lg" fullWidth loading={busy} className="mt-4">
                {busy ? "Отправка…" : "Оставить заявку"}
              </Button>
              {error && email.trim() && (
                <p className="mt-2 text-xs text-rose-300" role="alert">
                  {error}
                </p>
              )}
              <p className="mt-3 text-[10px] text-genesis-muted">
                Оплата — после подтверждения. Без скрытых платежей.
              </p>
            </Card>
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
          className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs transition-smooth sm:text-sm ${
            s.n === current
              ? "bg-genesis-accent/20 text-white"
              : s.n < current
                ? "text-emerald-400"
                : "text-genesis-muted"
          }`}
          aria-current={s.n === current ? "step" : undefined}
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
