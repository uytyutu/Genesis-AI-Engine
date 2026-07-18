"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { PackageSkeleton } from "../components/Skeleton";
import { formatLocalizedMoney } from "../lib/formatEur";
import { formatApiDetail } from "../lib/formatApiError";
import { startOrderCheckout } from "../lib/orderCheckout";
import { parseOrderPurchaseType } from "../lib/orderTrustCard";
import { OrderTrustCard } from "../components/OrderTrustCard";
import { OrderProjectSummary } from "../components/OrderProjectSummary";
import { fetchProjectPlatform } from "../lib/projectApi";
import { buildOrderLaunchContext, type OrderLaunchContext } from "../lib/orderProjectLaunch";
import { Badge, Button, ButtonLink, Card, Field, Input, Textarea } from "../components/ui";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type Package = {
  id: string;
  name: string;
  price_eur: number;
  deliverables: string[];
  currency?: string;
  symbol?: string;
  market_code?: string;
  price_label?: string;
};

type CommerceContext = {
  currency: string;
  symbol: string;
  market_code: string;
};

function suggestPackage(needsLogo: boolean, needsDomain: boolean, extra: string): string {
  if (needsDomain) return "premium";
  // Logo-Einbindung allein ist kein Premium-Upsell — nur komplexere Wünsche → Business
  if (extra.trim().length > 120) return "business";
  if (needsLogo) return "business";
  return "basic";
}

export default function OrderSitePage() {
  const { t } = useTranslation("site");
  const launchDeliverables = useMemo(
    () => [t("order.launchD1"), t("order.launchD2"), t("order.launchD3"), t("order.launchD4")],
    [t],
  );
  const [packages, setPackages] = useState<Package[]>([]);
  const [commerce, setCommerce] = useState<CommerceContext>({
    currency: "EUR",
    symbol: "€",
    market_code: "DE",
  });
  const [packagesLoading, setPackagesLoading] = useState(true);
  const [businessName, setBusinessName] = useState("");
  const [description, setDescription] = useState("");
  const [companyWebsite, setCompanyWebsite] = useState("");
  const [city, setCity] = useState("");
  const [phone, setPhone] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [email, setEmail] = useState("");
  const [needsLogo, setNeedsLogo] = useState(false);
  const [needsDomain, setNeedsDomain] = useState(false);
  const [extraWishes, setExtraWishes] = useState("");
  const [legalOwner, setLegalOwner] = useState("");
  const [legalForm, setLegalForm] = useState("");
  const [legalStreet, setLegalStreet] = useState("");
  const [legalZip, setLegalZip] = useState("");
  const [legalCity, setLegalCity] = useState("");
  const [legalDirector, setLegalDirector] = useState("");
  const [legalVat, setLegalVat] = useState("");
  const [legalMaps, setLegalMaps] = useState(false);
  const [legalAnalytics, setLegalAnalytics] = useState(false);
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
    currency?: string;
    price_label?: string;
  } | null>(null);
  const [payBusy, setPayBusy] = useState(false);
  const [payError, setPayError] = useState("");
  const [paymentReady, setPaymentReady] = useState(false);
  const [purchaseType, setPurchaseType] = useState<"one_time" | "subscription">("one_time");
  const [visitorId, setVisitorId] = useState<string | null>(null);
  const [launch, setLaunch] = useState<OrderLaunchContext | null>(null);
  const [launchLoading, setLaunchLoading] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const pkg = params.get("package");
    if (pkg && ["basic", "business", "premium"].includes(pkg)) {
      setPackageId(pkg);
      setManualPackage(true);
    }
    setPurchaseType(parseOrderPurchaseType(params.get("purchase_type")));
    const vid = params.get("visitor_id")?.trim();
    if (vid) setVisitorId(vid);
  }, []);

  useEffect(() => {
    if (!visitorId) return;
    let cancelled = false;
    setLaunchLoading(true);
    fetchProjectPlatform(visitorId)
      .then((state) => {
        if (cancelled) return;
        const ctx = buildOrderLaunchContext(state);
        setLaunch(ctx);
        if (ctx) {
          setBusinessName(ctx.company);
          setDescription(ctx.description);
          if (ctx.logoResolved) setNeedsLogo(false);
        }
      })
      .finally(() => {
        if (!cancelled) setLaunchLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [visitorId]);

  useEffect(() => {
    fetch(`${API}/api/sales/payment-status`)
      .then((r) => r.json())
      .then((body) => setPaymentReady(Boolean(body.configured)))
      .catch(() => setPaymentReady(false));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams();
      if (visitorId) params.set("visitor_id", visitorId);
      if (city.trim()) params.set("city", city.trim());
      if (description.trim()) params.set("text", description.trim());
      const qs = params.toString();
      fetch(`${API}/api/sales/packages${qs ? `?${qs}` : ""}`)
        .then((r) => r.json())
        .then((body) => {
          setPackages(body.packages ?? []);
          setCommerce({
            currency: body.currency ?? "EUR",
            symbol: body.symbol ?? "€",
            market_code: body.market_code ?? "DE",
          });
        })
        .catch(() => setPackages([]))
        .finally(() => setPackagesLoading(false));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [visitorId, city, description]);

  const suggestedId = useMemo(
    () => suggestPackage(needsLogo, needsDomain, extraWishes),
    [needsLogo, needsDomain, extraWishes]
  );

  useEffect(() => {
    if (!manualPackage) setPackageId(suggestedId);
  }, [suggestedId, manualPackage]);

  const formatPrice = (
    amount: number,
    pkg?: { currency?: string; price_label?: string }
  ) =>
    pkg?.price_label ??
    formatLocalizedMoney(amount, pkg?.currency ?? commerce.currency);

  const selected = packages.find((p) => p.id === packageId) ?? packages[0];

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      setError(t("order.emailRequired"));
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
          company_website: companyWebsite.trim() || null,
          client_legal: {
            owner_name: legalOwner.trim() || businessName.trim() || null,
            legal_form: legalForm.trim() || null,
            street: legalStreet.trim() || null,
            zip: legalZip.trim() || null,
            city: legalCity.trim() || city.trim() || null,
            country: "DE",
            email: email.trim() || null,
            phone: phone.trim() || null,
            managing_director: legalDirector.trim() || null,
            vat_id: legalVat.trim() || null,
            uses_maps: legalMaps,
            uses_analytics: legalAnalytics,
          },
          package_id: packageId,
          visitor_id: visitorId,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(formatApiDetail(body.detail) || t("order.submitFail"));
        return;
      }
      setDone({
        order_id: body.order_id,
        message: body.message,
        package_name: body.package_name,
        price_eur: body.price_eur,
        deliverables: body.deliverables ?? [],
        currency: body.currency ?? commerce.currency,
        price_label: body.price_label,
      });
    } catch {
      setError(t("order.serverDown"));
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
      setPayError(e instanceof Error ? e.message : t("order.serverDown"));
      setPayBusy(false);
    }
  }

  if (done) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-2xl py-4">
          <OrderSteps current={paymentReady ? 3 : 2} launch={Boolean(launch)} />
          <Card glow className="text-center" padding="lg">
            <p className="text-4xl text-emerald-400" aria-hidden>
              ✓
            </p>
            <h1 className="mt-4 text-2xl font-bold">
              {launch ? t("order.projectLocked") : t("order.thanks")}
            </h1>
            <p className="mt-3 text-genesis-muted">{done.message}</p>
            <Badge variant="muted" className="mt-3">
              № {done.order_id}
            </Badge>
            <Card hover={false} className="mt-6 text-left" padding="md">
              {launch ? (
                <>
                  <p className="text-sm text-genesis-muted">{t("order.toPay")}</p>
                  <p className="mt-1 text-xl font-semibold">
                    {launch.projectLabel} {launch.company} — {formatPrice(done.price_eur, done)}
                  </p>
                  <p className="genesis-label mt-4">{t("order.afterPay")}</p>
                  <ul className="mt-2 space-y-1.5 text-sm">
                    {(launch && done.deliverables.length > 0
                      ? done.deliverables
                      : launchDeliverables
                    ).map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400">✔</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <>
                  <p className="text-sm text-genesis-muted">{t("order.projectPriced")}</p>
                  <p className="mt-1 text-xl font-semibold">
                    {done.package_name} — {formatPrice(done.price_eur, done)}
                  </p>
                  <p className="genesis-label mt-4">{t("order.youReceive")}</p>
                  <ul className="mt-2 space-y-1.5 text-sm">
                    {done.deliverables.map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400">✔</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </Card>
            {paymentReady ? (
              <div className="mt-6 space-y-3">
                <OrderTrustCard purchaseType={purchaseType} />
                <Button variant="success" size="lg" fullWidth loading={payBusy} onClick={payNow}>
                  {payBusy
                    ? t("order.payBusy")
                    : t("order.payNow", { price: formatPrice(done.price_eur, done) })}
                </Button>
                {payError && (
                  <p className="text-xs text-rose-300" role="alert">
                    {payError}
                  </p>
                )}
              </div>
            ) : (
              <p className="mt-6 text-sm text-amber-200/90">{t("order.payUnavailable")}</p>
            )}
            <ButtonLink
              href={`/order/status/${done.order_id}`}
              variant="ghost"
              size="sm"
              className="mt-4"
            >
              {t("order.trackStatus")}
            </ButtonLink>
          </Card>
        </main>
      </PublicPageShell>
    );
  }

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-4xl py-2">
        <OrderSteps current={1} launch={Boolean(launch)} />
        <div className="mb-8 text-center animate-fade-up">
          <Badge variant="accent" className="tracking-[0.2em]">
            {t("order.badge")}
          </Badge>
          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">
            {launch ? t("order.titleLaunch") : t("order.title")}
          </h1>
          <p className="mt-2 text-genesis-muted">
            {launch ? t("order.subtitleLaunch") : t("order.subtitle")}
          </p>
          {!launch ? (
            <ul className="mx-auto mt-4 max-w-lg space-y-1 text-left text-sm text-white/75">
              <li>• {t("order.bulletPkg")}</li>
              <li>• {t("order.bulletAfterPay")}</li>
              <li>• {t("order.bulletSorglos")}</li>
            </ul>
          ) : null}
          {!launch ? (
            <ul className="mx-auto mt-4 flex max-w-xl flex-wrap justify-center gap-2 text-xs">
              {[t("pathA.benefitMobile"), t("pathA.benefitSeo"), t("pathA.benefitSpeed")].map(
                (label) => (
                  <li
                    key={label}
                    className="rounded-full border border-emerald-500/30 bg-emerald-950/30 px-3 py-1 text-emerald-100/90"
                  >
                    ✓ {label}
                  </li>
                ),
              )}
            </ul>
          ) : null}
        </div>

        {launch ? <OrderProjectSummary launch={launch} /> : null}
        {launchLoading && !launch ? (
          <p className="mb-6 text-center text-sm text-genesis-muted">{t("order.loadingProject")}</p>
        ) : null}

        <form onSubmit={submit} className={`grid gap-6 lg:grid-cols-5 ${launch ? "mt-6" : ""}`}>
          <div className="space-y-4 lg:col-span-3">
            {!launch ? (
              <>
            <Field label={t("order.businessName")} required>
              <Input
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder={t("order.businessNamePh")}
                required
              />
            </Field>
            <Field label={t("order.description")} required>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t("order.descriptionPh")}
                required
              />
            </Field>
            <Field label={t("order.companyWebsite")} hint={t("order.companyWebsiteHint")}>
              <Input
                type="text"
                inputMode="url"
                value={companyWebsite}
                onChange={(e) => setCompanyWebsite(e.target.value)}
                placeholder={t("order.companyWebsitePh")}
                autoComplete="url"
              />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t("order.city")}>
                <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder={t("order.cityPh")} />
              </Field>
              <Field label={t("order.phone")}>
                <Input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+49 …"
                />
              </Field>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t("order.whatsapp")}>
                <Input value={whatsapp} onChange={(e) => setWhatsapp(e.target.value)} placeholder="+49 …" />
              </Field>
              <Field label={t("order.email")} required error={error && !email.trim() ? error : undefined}>
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
                {t("order.needsLogo")}
              </label>
              <label className="flex cursor-pointer items-center gap-2 text-sm transition-smooth hover:text-white">
                <input
                  type="checkbox"
                  checked={needsDomain}
                  onChange={(e) => setNeedsDomain(e.target.checked)}
                  className="rounded border-genesis-border accent-genesis-accent"
                />
                {t("order.needsDomain")}
              </label>
            </div>
            <p className="text-xs leading-relaxed text-genesis-muted">{t("order.logoNote")}</p>
            <p className="text-xs leading-relaxed text-genesis-muted">{t("order.domainHostingNote")}</p>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-3">
              <p className="text-sm font-medium text-white">{t("order.legalTitle")}</p>
              <p className="text-xs text-genesis-muted">{t("order.legalHint")}</p>
              <Field label={t("order.legalOwner")}>
                <Input
                  value={legalOwner}
                  onChange={(e) => setLegalOwner(e.target.value)}
                  placeholder={t("order.businessNamePh")}
                />
              </Field>
              <Field label={t("order.legalForm")}>
                <Input
                  value={legalForm}
                  onChange={(e) => setLegalForm(e.target.value)}
                  placeholder={t("order.legalFormPh")}
                />
              </Field>
              <Field label={t("order.legalStreet")}>
                <Input value={legalStreet} onChange={(e) => setLegalStreet(e.target.value)} />
              </Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label={t("order.legalZip")}>
                  <Input value={legalZip} onChange={(e) => setLegalZip(e.target.value)} placeholder="50667" />
                </Field>
                <Field label={t("order.legalCity")}>
                  <Input value={legalCity} onChange={(e) => setLegalCity(e.target.value)} placeholder={t("order.cityPh")} />
                </Field>
              </div>
              <Field label={t("order.legalDirector")}>
                <Input value={legalDirector} onChange={(e) => setLegalDirector(e.target.value)} />
              </Field>
              <Field label={t("order.legalVat")}>
                <Input value={legalVat} onChange={(e) => setLegalVat(e.target.value)} placeholder="DE…" />
              </Field>
              <div className="flex flex-wrap gap-4">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-genesis-muted">
                  <input
                    type="checkbox"
                    checked={legalMaps}
                    onChange={(e) => setLegalMaps(e.target.checked)}
                    className="rounded border-genesis-border accent-genesis-accent"
                  />
                  {t("order.legalMaps")}
                </label>
                <label className="flex cursor-pointer items-center gap-2 text-sm text-genesis-muted">
                  <input
                    type="checkbox"
                    checked={legalAnalytics}
                    onChange={(e) => setLegalAnalytics(e.target.checked)}
                    className="rounded border-genesis-border accent-genesis-accent"
                  />
                  {t("order.legalAnalytics")}
                </label>
              </div>
            </div>
            <Field label={t("order.extraWishes")}>
              <Textarea
                className="min-h-[72px]"
                value={extraWishes}
                onChange={(e) => setExtraWishes(e.target.value)}
                placeholder={t("order.extraWishesPh")}
              />
            </Field>
              </>
            ) : (
              <>
                <Field
                  label={t("order.emailLaunch")}
                  required
                  error={error && !email.trim() ? error : undefined}
                >
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="hello@…"
                    required
                    error={Boolean(error && !email.trim())}
                  />
                </Field>
                <Field label={t("order.phoneOptional")}>
                  <Input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+49 …"
                  />
                </Field>
              </>
            )}
          </div>

          <aside className="lg:col-span-2">
            <Card glow className="sticky top-4" padding="md">
              <p className="genesis-label">
                {launch ? t("order.launchTitle") : t("order.packageAndPrice")}
              </p>
              {packagesLoading ? (
                <PackageSkeleton />
              ) : packages.length === 0 ? (
                <p className="mt-4 text-sm text-genesis-muted">{t("order.packagesFail")}</p>
              ) : launch && selected ? (
                <div className="mt-3">
                  <p className="text-lg font-semibold">
                    {launch.projectLabel} {launch.company}
                  </p>
                  <p className="mt-2 text-3xl font-bold tabular-nums">
                    {formatPrice(selected.price_eur, selected)}
                  </p>
                  <p className="mt-2 text-xs text-genesis-muted leading-relaxed">
                    {t("order.launchFixed")}
                  </p>
                  <p className="genesis-label mt-4">{t("order.launchIncludes")}</p>
                  <ul className="space-y-1.5 text-xs">
                    {launchDeliverables.map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400">✔</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </div>
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
                      <span className="font-semibold tabular-nums">{formatPrice(p.price_eur, p)}</span>
                    </label>
                  ))}
                </div>
              )}
              {!launch && !manualPackage && selected && (
                <p className="mt-2 text-xs text-genesis-muted">
                  {t("order.recommend", { name: selected.name })}
                </p>
              )}
              {!launch && selected && (
                <>
                  <p className="genesis-label mt-4">{t("order.youGet")}</p>
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
                {busy
                  ? t("order.submitBusy")
                  : launch
                    ? t("order.submitLaunch", {
                        price: selected ? formatPrice(selected.price_eur, selected) : "…",
                      })
                    : t("order.submit")}
              </Button>
              {error && email.trim() && (
                <p className="mt-2 text-xs text-rose-300" role="alert">
                  {error}
                </p>
              )}
              <p className="mt-3 text-[10px] text-genesis-muted">{t("order.payAfter")}</p>
            </Card>
          </aside>
        </form>

        <p className="mt-6 text-center text-xs text-genesis-muted">
          {launch ? t("order.agreeLaunch") : t("order.agreeSubmit")}
          <Link href="/agb" className="text-genesis-accent hover:underline">
            AGB
          </Link>
          {t("order.and")}
          <Link href="/datenschutz" className="text-genesis-accent hover:underline">
            Datenschutz
          </Link>
          .
        </p>
      </main>
    </PublicPageShell>
  );
}

function OrderSteps({ current, launch = false }: { current: number; launch?: boolean }) {
  const { t } = useTranslation("site");
  const steps = launch
    ? [
        { n: 1, label: t("order.stepProject") },
        { n: 2, label: t("order.stepLaunch") },
        { n: 3, label: t("order.stepPublish") },
      ]
    : [
        { n: 1, label: t("order.stepForm") },
        { n: 2, label: t("order.stepConfirm") },
        { n: 3, label: t("order.stepPay") },
      ];
  return (
    <ol className="mb-8 flex justify-center gap-2 sm:gap-4" aria-label={t("order.stepsAria")}>
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
