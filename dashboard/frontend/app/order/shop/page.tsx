"use client";

/**
 * AI Store R1 — questionnaire → register → Stripe → cabinet pipeline.
 */

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { OrderFormShell } from "../../components/OrderFormShell";
import { PublicPageShell } from "../../components/PublicPageShell";
import { useLocale } from "../../context/LocaleContext";
import { BRAND_NAME } from "../../lib/publicBrand";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { startOrderCheckout } from "../../lib/orderCheckout";
import { publicApiBase } from "../../lib/publicApiBase";
import { getVisitorId } from "../../lib/visitorId";
import { uiLangForMarket } from "../../lib/marketLang";

const API = publicApiBase();

const CATEGORIES = [
  { id: "clothing", label: "Clothing" },
  { id: "electronics", label: "Electronics" },
  { id: "auto", label: "Auto" },
  { id: "beauty", label: "Beauty" },
  { id: "jewelry", label: "Jewelry" },
  { id: "furniture", label: "Furniture" },
  { id: "food", label: "Food" },
  { id: "other", label: "Other" },
] as const;

const CATALOG_SIZES = ["20", "100", "500", "1000+"] as const;
const PAYMENTS = [
  { id: "stripe", label: "Stripe" },
  { id: "paypal", label: "PayPal" },
  { id: "bank", label: "Bank transfer" },
] as const;
const SHIPPING = [
  { id: "dhl", label: "DHL" },
  { id: "hermes", label: "Hermes" },
  { id: "dpd", label: "DPD" },
  { id: "pickup", label: "Pickup" },
] as const;
const PAGES = [
  { id: "home", label: "Home" },
  { id: "catalog", label: "Catalog" },
  { id: "pdp", label: "Product page" },
  { id: "about", label: "About" },
  { id: "contact", label: "Contact" },
  { id: "faq", label: "FAQ" },
  { id: "legal", label: "Legal / Privacy" },
  { id: "returns", label: "Returns" },
  { id: "news", label: "News" },
  { id: "blog", label: "Blog" },
] as const;
const STYLES = [
  "modern",
  "minimal",
  "luxury",
  "tech",
  "bold",
  "warm",
] as const;
const INTEGRATIONS = [
  { id: "instagram_shop", label: "Instagram Shop" },
  { id: "facebook_shop", label: "Facebook Shop" },
  { id: "google_merchant", label: "Google Merchant" },
  { id: "google_analytics", label: "Google Analytics" },
  { id: "meta_pixel", label: "Meta Pixel" },
] as const;

type Step = "brief" | "catalog" | "features" | "commerce" | "design" | "pay";

type ShopBrief = {
  company_name: string;
  store_name: string;
  business_description: string;
  what_is_sold: string;
  category: string;
  product_categories: string;
  catalog_size: string;
  languages: string[];
  currency: string;
  payments: string[];
  shipping: string[];
  pages: string[];
  wishes: string;
  logo_url: string;
  logo_need: "have_logo" | "need_new_logo" | "skip";
  photo_urls: string[];
  color_scheme: string;
  style: string;
  need_variants: boolean;
  need_search: boolean;
  need_reviews: boolean;
  need_promo_codes: boolean;
  need_gift_cards: boolean;
  has_digital_products: boolean;
  integrations: string[];
};

const emptyBrief = (): ShopBrief => ({
  company_name: "",
  store_name: "",
  business_description: "",
  what_is_sold: "",
  category: "other",
  product_categories: "",
  catalog_size: "20",
  languages: ["de"],
  currency: "EUR",
  payments: ["stripe"],
  shipping: ["dhl"],
  pages: ["home", "catalog", "pdp", "contact", "legal"],
  wishes: "",
  logo_url: "",
  logo_need: "need_new_logo",
  photo_urls: [],
  color_scheme: "",
  style: "modern",
  need_variants: false,
  need_search: true,
  need_reviews: false,
  need_promo_codes: false,
  need_gift_cards: false,
  has_digital_products: false,
  integrations: [],
});

function toggleIn(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg px-3 py-1.5 text-sm transition ${
        active
          ? "border border-emerald-400/45 bg-emerald-500/15 text-white"
          : "border border-white/10 text-zinc-400 hover:border-white/20"
      }`}
    >
      {children}
    </button>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm text-zinc-300">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  );
}

const inputClass =
  "w-full rounded-xl border border-white/15 bg-black/35 px-3 py-2.5 text-white placeholder:text-zinc-600 focus:border-emerald-400/40 focus:outline-none";

function ShopOrderInner() {
  const { t } = useTranslation("site");
  const { uiLocale } = useLocale();
  const router = useRouter();
  const search = useSearchParams();
  const market = (search.get("market") || "DE").toUpperCase();
  const [step, setStep] = useState<Step>("brief");
  const [brief, setBrief] = useState<ShopBrief>(emptyBrief);
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(Boolean(getClientToken()));
  }, []);

  const registerNext = useMemo(() => {
    const q = market ? `?market=${encodeURIComponent(market)}` : "";
    return `/order/shop${q}`;
  }, [market]);

  const ensureAuth = useCallback(() => {
    if (getClientToken()) return true;
    router.replace(
      `/client/register?next=${encodeURIComponent(registerNext)}`,
    );
    return false;
  }, [registerNext, router]);

  const patch = (partial: Partial<ShopBrief>) =>
    setBrief((b) => ({ ...b, ...partial }));

  const submitPay = async () => {
    setError(null);
    if (
      !brief.company_name.trim() ||
      !brief.store_name.trim() ||
      !brief.what_is_sold.trim()
    ) {
      setError(
        t("aiStore.fillRequired", {
          defaultValue: "Please complete required fields.",
        }),
      );
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setError(
        t("aiStore.fillRequired", {
          defaultValue: "Please complete required fields.",
        }),
      );
      return;
    }
    if (!ensureAuth()) return;
    setBusy(true);
    try {
      const meRes = await fetch(`${API}/api/client/me`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      const me = await meRes.json().catch(() => ({}));
      if (!meRes.ok) {
        throw new Error(formatApiDetail(me.detail) || "Please sign in again.");
      }
      const customerId =
        String(me?.customer_id || me?.account?.customer_id || "").trim() ||
        null;
      const accountEmail =
        String(me?.account?.email || me?.email || email).trim() || email;

      const description = [
        brief.store_name,
        brief.category,
        brief.style,
        `~${brief.catalog_size} SKUs`,
        brief.what_is_sold.slice(0, 180),
      ]
        .filter(Boolean)
        .join(" · ");

      const res = await fetch(`${API}/api/sales/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...clientAuthHeaders(),
        },
        body: JSON.stringify({
          package_id: "ecommerce_shop",
          product_kind: "shop",
          business_name: brief.store_name || brief.company_name,
          description: description || brief.what_is_sold,
          email: accountEmail,
          phone: phone.trim() || undefined,
          customer_id: customerId,
          visitor_id: getVisitorId(),
          market_code: market,
          ui_lang: uiLocale || uiLangForMarket(market),
          shop_brief: {
            ...brief,
            product_categories: brief.product_categories
              .split(",")
              .map((x) => x.trim())
              .filter(Boolean),
            photo_urls: brief.logo_url
              ? [brief.logo_url, ...brief.photo_urls].filter(Boolean).slice(0, 12)
              : brief.photo_urls,
          },
          extra_wishes: brief.wishes || undefined,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          formatApiDetail(body.detail) ||
            t("aiStore.orderFailed", { defaultValue: "Could not create order" }),
        );
      }
      const orderId = String(body.order_id || "");
      if (!orderId) throw new Error("No order id");
      const checkoutUrl = await startOrderCheckout(orderId, {
        successPath: `/client/stores/${orderId}?paid=1`,
        cancelPath: `/order/shop?canceled=1&market=${encodeURIComponent(market)}`,
      });
      window.location.href = checkoutUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  };

  const steps: { id: Step; label: string }[] = [
    { id: "brief", label: t("aiStore.stepBrief", { defaultValue: "Business" }) },
    { id: "catalog", label: t("aiStore.stepCatalog", { defaultValue: "Catalog" }) },
    {
      id: "features",
      label: t("aiStore.stepFeatures", { defaultValue: "Features" }),
    },
    {
      id: "commerce",
      label: t("aiStore.stepCommerce", { defaultValue: "Commerce" }),
    },
    { id: "design", label: t("aiStore.stepDesign", { defaultValue: "Design" }) },
    { id: "pay", label: t("aiStore.stepPay", { defaultValue: "Pay" }) },
  ];

  const nav = (back?: Step, next?: Step) => (
    <div className="flex flex-wrap gap-2 pt-2">
      {back ? (
        <button
          type="button"
          className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          onClick={() => setStep(back)}
        >
          ←
        </button>
      ) : null}
      {next ? (
        <button
          type="button"
          className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110"
          onClick={() => setStep(next)}
        >
          {t("aiStore.next", { defaultValue: "Next →" })}
        </button>
      ) : null}
    </div>
  );

  return (
    <OrderFormShell
      backHref="/site#ai-store"
      backLabel={t("aiStore.back", {
        brand: BRAND_NAME,
        defaultValue: `← ${BRAND_NAME} storefront`,
      })}
      eyebrow="AI Store by Virtus Core"
      title={t("aiStore.title", {
        defaultValue: "Tell us about your business",
      })}
      priceLabel={t("aiStore.priceLine", { defaultValue: "from 799 €" })}
      subtitle={t("aiStore.positioning", {
        defaultValue:
          "Virtus Core creates a professional online shop for your business — not a generic website package. After payment your shop appears in your client cabinet.",
      })}
    >
      <nav className="mb-5 flex flex-wrap gap-2" aria-label="Steps">
        {steps.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setStep(s.id)}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              step === s.id
                ? "bg-emerald-500/20 text-emerald-100"
                : "bg-white/5 text-zinc-500"
            }`}
          >
            {s.label}
          </button>
        ))}
      </nav>

      {step === "brief" ? (
        <div className="space-y-4">
          <Field label={t("aiStore.company", { defaultValue: "Company name" })}>
            <input
              className={inputClass}
              value={brief.company_name}
              onChange={(e) => patch({ company_name: e.target.value })}
            />
          </Field>
          <Field label={t("aiStore.storeName", { defaultValue: "Store name" })}>
            <input
              className={inputClass}
              value={brief.store_name}
              onChange={(e) => patch({ store_name: e.target.value })}
            />
          </Field>
          <Field
            label={t("aiStore.description", {
              defaultValue: "Business description",
            })}
          >
            <textarea
              className={inputClass}
              rows={3}
              value={brief.business_description}
              onChange={(e) =>
                patch({ business_description: e.target.value })
              }
            />
          </Field>
          <Field
            label={t("aiStore.whatSold", { defaultValue: "What do you sell?" })}
          >
            <textarea
              className={inputClass}
              rows={3}
              value={brief.what_is_sold}
              onChange={(e) => patch({ what_is_sold: e.target.value })}
            />
          </Field>
          {nav(undefined, "catalog")}
        </div>
      ) : null}

      {step === "catalog" ? (
        <div className="space-y-4">
          <p className="text-sm font-medium text-white">
            {t("aiStore.category", { defaultValue: "Category" })}
          </p>
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((c) => (
              <Chip
                key={c.id}
                active={brief.category === c.id}
                onClick={() => patch({ category: c.id })}
              >
                {c.label}
              </Chip>
            ))}
          </div>
          <Field
            label={t("aiStore.productCategories", {
              defaultValue: "Product categories needed (comma-separated)",
            })}
          >
            <input
              className={inputClass}
              placeholder="Women, Men, Accessories…"
              value={brief.product_categories}
              onChange={(e) => patch({ product_categories: e.target.value })}
            />
          </Field>
          <p className="text-sm font-medium text-white">
            {t("aiStore.catalogSize", { defaultValue: "Approx. products" })}
          </p>
          <div className="flex flex-wrap gap-2">
            {CATALOG_SIZES.map((s) => (
              <Chip
                key={s}
                active={brief.catalog_size === s}
                onClick={() => patch({ catalog_size: s })}
              >
                {s}
              </Chip>
            ))}
          </div>
          <Field
            label={t("aiStore.languages", {
              defaultValue: "Languages (comma-separated)",
            })}
          >
            <input
              className={inputClass}
              value={brief.languages.join(", ")}
              onChange={(e) =>
                patch({
                  languages: e.target.value
                    .split(",")
                    .map((x) => x.trim())
                    .filter(Boolean),
                })
              }
            />
          </Field>
          <Field label={t("aiStore.currency", { defaultValue: "Currency" })}>
            <input
              className={inputClass}
              value={brief.currency}
              onChange={(e) =>
                patch({ currency: e.target.value.toUpperCase() })
              }
            />
          </Field>
          {nav("brief", "features")}
        </div>
      ) : null}

      {step === "features" ? (
        <div className="space-y-4">
          <p className="text-sm text-zinc-400">
            {t("aiStore.featuresHint", {
              defaultValue:
                "Optional extras for later — tell us what you need.",
            })}
          </p>
          {(
            [
              ["need_variants", "Product variants (size, color…)"],
              ["need_search", "Product search"],
              ["need_reviews", "Customer reviews"],
              ["need_promo_codes", "Promo codes"],
              ["need_gift_cards", "Gift cards"],
              ["has_digital_products", "Digital products"],
            ] as const
          ).map(([key, label]) => (
            <label
              key={key}
              className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-sm text-zinc-200"
            >
              <input
                type="checkbox"
                checked={Boolean(brief[key])}
                onChange={(e) => patch({ [key]: e.target.checked })}
                className="h-4 w-4 accent-emerald-500"
              />
              {t(`aiStore.${key}`, { defaultValue: label })}
            </label>
          ))}
          <p className="pt-2 text-sm font-medium text-white">
            {t("aiStore.integrations", { defaultValue: "Integrations" })}
          </p>
          <div className="flex flex-wrap gap-2">
            {INTEGRATIONS.map((i) => (
              <Chip
                key={i.id}
                active={brief.integrations.includes(i.id)}
                onClick={() =>
                  patch({ integrations: toggleIn(brief.integrations, i.id) })
                }
              >
                {i.label}
              </Chip>
            ))}
          </div>
          {nav("catalog", "commerce")}
        </div>
      ) : null}

      {step === "commerce" ? (
        <div className="space-y-4">
          <p className="text-sm font-medium text-white">
            {t("aiStore.payments", { defaultValue: "Payments" })}
          </p>
          <div className="flex flex-wrap gap-2">
            {PAYMENTS.map((p) => (
              <Chip
                key={p.id}
                active={brief.payments.includes(p.id)}
                onClick={() =>
                  patch({ payments: toggleIn(brief.payments, p.id) })
                }
              >
                {p.label}
              </Chip>
            ))}
          </div>
          <p className="text-sm font-medium text-white">
            {t("aiStore.shipping", { defaultValue: "Shipping" })}
          </p>
          <div className="flex flex-wrap gap-2">
            {SHIPPING.map((p) => (
              <Chip
                key={p.id}
                active={brief.shipping.includes(p.id)}
                onClick={() =>
                  patch({ shipping: toggleIn(brief.shipping, p.id) })
                }
              >
                {p.label}
              </Chip>
            ))}
          </div>
          <p className="text-sm font-medium text-white">
            {t("aiStore.pages", { defaultValue: "Pages needed" })}
          </p>
          <div className="flex flex-wrap gap-2">
            {PAGES.map((p) => (
              <Chip
                key={p.id}
                active={brief.pages.includes(p.id)}
                onClick={() => patch({ pages: toggleIn(brief.pages, p.id) })}
              >
                {p.label}
              </Chip>
            ))}
          </div>
          {nav("features", "design")}
        </div>
      ) : null}

      {step === "design" ? (
        <div className="space-y-4">
          <p className="text-sm font-medium text-white">
            {t("aiStore.style", { defaultValue: "Preferred style" })}
          </p>
          <div className="flex flex-wrap gap-2">
            {STYLES.map((s) => (
              <Chip
                key={s}
                active={brief.style === s}
                onClick={() => patch({ style: s })}
              >
                {s}
              </Chip>
            ))}
          </div>
          <Field
            label={t("aiStore.color", {
              defaultValue: "Main colors (optional)",
            })}
          >
            <input
              className={inputClass}
              placeholder="#0f172a, emerald…"
              value={brief.color_scheme}
              onChange={(e) => patch({ color_scheme: e.target.value })}
            />
          </Field>
          <p className="text-sm font-medium text-white">
            {t("aiStore.logoNeed", { defaultValue: "Logo" })}
          </p>
          <div className="flex flex-wrap gap-2">
            {(
              [
                ["have_logo", "I have a logo"],
                ["need_new_logo", "Need a new logo"],
                ["skip", "Skip for now"],
              ] as const
            ).map(([id, label]) => (
              <Chip
                key={id}
                active={brief.logo_need === id}
                onClick={() => patch({ logo_need: id })}
              >
                {t(`aiStore.logo_${id}`, { defaultValue: label })}
              </Chip>
            ))}
          </div>
          {brief.logo_need === "have_logo" ? (
            <Field
              label={t("aiStore.logoUrl", { defaultValue: "Logo URL" })}
            >
              <input
                type="url"
                className={inputClass}
                value={brief.logo_url}
                onChange={(e) => patch({ logo_url: e.target.value })}
              />
            </Field>
          ) : null}
          <Field
            label={t("aiStore.wishes", { defaultValue: "Extra wishes" })}
          >
            <textarea
              className={inputClass}
              rows={3}
              value={brief.wishes}
              onChange={(e) => patch({ wishes: e.target.value })}
            />
          </Field>
          {nav("commerce", "pay")}
        </div>
      ) : null}

      {step === "pay" ? (
        <div className="space-y-4">
          <p className="text-lg font-semibold text-white">
            {t("aiStore.readyPay", {
              defaultValue: "Ready for payment — from 799 €",
            })}
          </p>
          <p className="text-sm text-zinc-300">
            {brief.store_name || brief.company_name} · {brief.style} ·{" "}
            {brief.category} · ~{brief.catalog_size}
          </p>
          <p className="text-xs text-amber-100/85">
            {t("aiStore.honestNote", {
              defaultValue:
                "After payment you receive a professional online shop in your client cabinet. You can open it right away. Connecting your own payments and deeper catalog tools come as you grow.",
            })}
          </p>
          {!loggedIn ? (
            <p className="text-sm text-amber-200">
              {t("aiStore.needAccount", {
                defaultValue: "Create an account before payment.",
              })}{" "}
              <Link
                href={`/client/register?next=${encodeURIComponent(registerNext)}`}
                className="underline"
              >
                {t("aiStore.register", { defaultValue: "Register →" })}
              </Link>
            </p>
          ) : null}
          <Field label="Email">
            <input
              type="email"
              className={inputClass}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          <Field
            label={`Phone (${t("aiStore.optional", { defaultValue: "optional" })})`}
          >
            <input
              className={inputClass}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </Field>
          {error ? (
            <p className="text-sm text-rose-300" role="alert">
              {error}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300"
              onClick={() => setStep("design")}
            >
              ←
            </button>
            <button
              type="button"
              disabled={busy}
              className="rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-black disabled:opacity-60"
              onClick={() => void submitPay()}
            >
              {busy
                ? t("aiStore.openingPay", {
                    defaultValue: "Opening payment…",
                  })
                : t("aiStore.pay", { defaultValue: "Pay securely →" })}
            </button>
          </div>
        </div>
      ) : null}
    </OrderFormShell>
  );
}

export default function ShopOrderPage() {
  return (
    <Suspense
      fallback={
        <PublicPageShell customerDecisionFlow minimal>
          <div className="mx-auto max-w-2xl px-4 py-16 text-zinc-400">…</div>
        </PublicPageShell>
      }
    >
      <ShopOrderInner />
    </Suspense>
  );
}
