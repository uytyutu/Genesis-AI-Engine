"use client";

import { useMemo, useState } from "react";
import {
  checkoutOfficeJob,
  configureSalesKitCompany,
} from "../../lib/officeApi";
import { saveOfficeJobToken } from "../../lib/officeSession";
import { useOfficeT } from "../../lib/useOfficeT";
import { OfficeShell } from "./OfficeShell";

type TierId = "sales_kit_basic" | "sales_kit_business" | "sales_kit_professional";

const TIERS: {
  id: TierId;
  price: string;
  includesKey: "basicIncludes" | "businessIncludes" | "professionalIncludes";
}[] = [
  { id: "sales_kit_basic", price: "99", includesKey: "basicIncludes" },
  { id: "sales_kit_business", price: "199", includesKey: "businessIncludes" },
  { id: "sales_kit_professional", price: "299", includesKey: "professionalIncludes" },
];

export function OfficeSalesKitPage() {
  const { t } = useOfficeT();
  const [tier, setTier] = useState<TierId>("sales_kit_business");
  const [companyName, setCompanyName] = useState("");
  const [description, setDescription] = useState("");
  const [services, setServices] = useState("");
  const [prices, setPrices] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [configured, setConfigured] = useState<{
    jobId: string;
    ownerToken: string;
    priceEur: number;
    blocked: boolean;
  } | null>(null);

  const selected = useMemo(() => TIERS.find((x) => x.id === tier)!, [tier]);

  async function onConfigure() {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const company = {
        company_name: companyName.trim(),
        description: description.trim(),
        services: services
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean),
        prices: prices
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean),
        contacts: {
          email: email.trim(),
          phone: phone.trim(),
        },
      };
      const res = await configureSalesKitCompany({
        tier,
        company,
        email: email.trim() || undefined,
      });
      const jid = String(res.job_id || "").trim();
      const tok = String(res.owner_token || "").trim();
      if (!jid || !tok) {
        throw new Error(t("salesKit.configFailed"));
      }
      saveOfficeJobToken(jid, tok, { status: "proposal_ready" });
      setConfigured({
        jobId: jid,
        ownerToken: tok,
        priceEur: Number(res.price_eur || selected.price),
        blocked: Boolean(res.purchase_blocked_until_live ?? true),
      });
      setInfo(
        res.purchase_blocked_until_live
          ? t("salesKit.configuredBlocked")
          : t("salesKit.configuredReady"),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : t("salesKit.configFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function onCheckout() {
    if (!configured) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      await checkoutOfficeJob(configured.jobId, configured.ownerToken, {
        success_url: `${origin}/office/order/${encodeURIComponent(configured.jobId)}?paid=1`,
        cancel_url: `${origin}/office/sales-kit?cancel=1`,
        email: email.trim() || undefined,
        price_eur: configured.priceEur,
      });
      setInfo(t("salesKit.checkoutUnexpected"));
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (/not.?live|nicht verfügbar|product_not_live|derzeit nicht/i.test(msg)) {
        setInfo(t("salesKit.liveBlocked"));
      } else {
        setError(msg);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <OfficeShell active="sales_kit">
      <section className="vo-enter max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--vo-accent)]">
          {t("salesKit.eyebrow")}
        </p>
        <h1 className="vo-display mt-2 text-4xl font-semibold tracking-tight text-[var(--vo-ink)]">
          {t("salesKit.title")}
        </h1>
        <p className="mt-3 text-lg text-[var(--vo-muted)]">{t("salesKit.lead")}</p>
        <p className="mt-3 text-sm text-[var(--vo-ink)]/80">{t("salesKit.honesty")}</p>
      </section>

      <section className="mt-10 grid gap-4 sm:grid-cols-3">
        {TIERS.map((item) => {
          const active = tier === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setTier(item.id);
                setConfigured(null);
                setInfo(null);
                setError(null);
              }}
              className={`rounded-2xl border p-5 text-left transition ${
                active
                  ? "border-[var(--vo-accent)] bg-[var(--vo-accent-soft)]/50"
                  : "border-[var(--vo-border)] bg-[var(--vo-surface)] hover:border-[var(--vo-accent)]/40"
              }`}
            >
              <h2 className="text-lg font-semibold text-[var(--vo-ink)]">
                {t(`salesKit.tiers.${item.id}.label`)}
              </h2>
              <p className="mt-1 text-2xl font-semibold text-[var(--vo-accent)]">
                {item.price} €
              </p>
              <p className="mt-2 text-sm text-[var(--vo-muted)]">
                {t(`salesKit.tiers.${item.id}.desc`)}
              </p>
              <p className="mt-3 text-xs text-[var(--vo-ink)]/75">
                {t(`salesKit.${item.includesKey}`)}
              </p>
            </button>
          );
        })}
      </section>

      <section className="mt-10 rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-5 sm:p-6">
        <h2 className="text-lg font-semibold text-[var(--vo-ink)]">{t("salesKit.formTitle")}</h2>
        <p className="mt-1 text-sm text-[var(--vo-muted)]">{t("salesKit.formLead")}</p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field
            label={t("salesKit.fields.companyName")}
            value={companyName}
            onChange={setCompanyName}
          />
          <Field label={t("salesKit.fields.email")} value={email} onChange={setEmail} />
          <Field label={t("salesKit.fields.phone")} value={phone} onChange={setPhone} />
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-[var(--vo-muted)]">
              {t("salesKit.fields.description")}
            </label>
            <textarea
              className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-[var(--vo-muted)]">
              {t("salesKit.fields.services")}
            </label>
            <textarea
              className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm"
              rows={4}
              value={services}
              onChange={(e) => setServices(e.target.value)}
              placeholder={t("salesKit.placeholders.services")}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-[var(--vo-muted)]">
              {t("salesKit.fields.prices")}
            </label>
            <textarea
              className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm"
              rows={4}
              value={prices}
              onChange={(e) => setPrices(e.target.value)}
              placeholder={t("salesKit.placeholders.prices")}
            />
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={busy}
            onClick={() => void onConfigure()}
            className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-[var(--vo-accent)] px-6 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-60"
          >
            {busy ? t("salesKit.working") : t("salesKit.ctaConfigure")}
          </button>
          {configured ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void onCheckout()}
              className="inline-flex min-h-[48px] items-center justify-center rounded-xl border border-[var(--vo-border)] px-6 text-sm font-semibold text-[var(--vo-ink)] hover:border-[var(--vo-accent)]/40 disabled:opacity-60"
            >
              {t("salesKit.ctaCheckout")}
            </button>
          ) : null}
        </div>

        {info ? (
          <p className="mt-4 rounded-xl border border-[var(--vo-accent)]/30 bg-[var(--vo-accent-soft)]/40 px-4 py-3 text-sm text-[var(--vo-ink)]">
            {info}
          </p>
        ) : null}
        {error ? (
          <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </p>
        ) : null}
      </section>
    </OfficeShell>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="text-xs font-semibold text-[var(--vo-muted)]">{label}</label>
      <input
        className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
