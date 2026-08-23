"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  IntegrationConnectionCard,
  type IntegrationConnection,
} from "./IntegrationConnectionCard";
import { StoreAdminSmtpPanel } from "./StoreAdminSmtpPanel";
import { StoreAdminShippingPanel } from "./StoreAdminShippingPanel";
import { StoreAdminBusinessProfile } from "./StoreAdminBusinessProfile";
import { clientAuthHeaders } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type EmailTransport = {
  provider_id?: string | null;
  host?: string | null;
  port?: number;
  username?: string | null;
  encryption?: string;
  from_email?: string | null;
  from_name?: string | null;
  reply_to?: string | null;
  support_email?: string | null;
  sales_email?: string | null;
  password_set?: boolean;
  last_test?: {
    ok?: boolean;
    to?: string;
    sent_at?: string;
    status?: string;
    title?: string;
    reason?: string;
  } | null;
};

type Props = {
  orderId: string;
  dark?: boolean;
  focus?:
    | "overview"
    | "payments"
    | "shipping"
    | "integrations"
    | "taxes"
    | "email"
    | "invoices"
    | "notifications"
    | "contact";
};

type ShippingMethod = {
  id: string;
  carrier: string;
  label: string;
  days_min: number;
  days_max: number;
  price_eur: number;
  enabled: boolean;
};

type ShippingConfig = {
  country?: string;
  regions?: string[];
  free_shipping_from_eur?: number | null;
  min_order_eur?: number | null;
  processing_days?: number;
  rate_mode?: string;
  methods?: ShippingMethod[];
};

type TaxConfig = {
  profile?: string;
  standard_rate_pct?: number;
  reduced_rate_pct?: number;
  vat_exempt?: boolean;
  eu_sales_enabled?: boolean;
  export_outside_eu_zero?: boolean;
  company_vat_id?: string | null;
};

type InvoiceConfig = {
  prefix?: string;
  next_number?: number;
  credit_note_prefix?: string;
  next_credit_number?: number;
  include_order_number?: boolean;
  auto_pdf?: boolean;
  company_name?: string | null;
  language?: string;
  currency?: string;
  date_format?: string;
  signature_text?: string | null;
  stamp_enabled?: boolean;
  show_payment_qr?: boolean;
};

type HubSection = {
  id: string;
  label: string;
  phase?: string;
  items: IntegrationConnection[];
  config?: ShippingConfig | TaxConfig | InvoiceConfig | EmailTransport;
};

export function StoreAdminCommerce({
  orderId,
  dark = true,
  focus = "overview",
}: Props) {
  const [sections, setSections] = useState<HubSection[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [smtpProvider, setSmtpProvider] = useState<string | null>(null);
  const [shippingProvider, setShippingProvider] = useState<string | null>(null);
  const [shipHint, setShipHint] = useState<string | null>(null);
  const [templates, setTemplates] = useState<{ id: string; label: string }[]>([]);
  const muted = dark ? "text-zinc-500" : "text-slate-500";

  const load = useCallback(async () => {
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/integrations`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Failed to load integrations");
      }
      setSections((body.sections || []) as HubSection[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [orderId]);

  const loadTemplates = useCallback(async () => {
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/email-templates`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      if (!res.ok) return;
      const body = await res.json();
      setTemplates(
        ((body.templates || []) as { id: string; label: string }[]).map((t) => ({
          id: t.id,
          label: t.label,
        })),
      );
    } catch {
      /* optional */
    }
  }, [orderId]);

  useEffect(() => {
    void load();
    void loadTemplates();
  }, [load, loadTemplates]);

  function startStripeOAuth() {
    setBusyId("stripe");
    // Full-page breakout — Stripe OAuth cannot run inside iframes.
    const url = `${API}/api/client/stores/${orderId}/admin/integrations/stripe/oauth/start`;
    try {
      window.top!.location.href = url;
    } catch {
      window.location.href = url;
    }
  }

  async function sendTestEmail() {
    setBusyId("email-test");
    try {
      const res = await fetch(`${API}/api/client/stores/${orderId}/admin/email/test`, {
        method: "POST",
        headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok && !body.test) {
        throw new Error(formatApiDetail(body.detail) || "test_failed");
      }
      if (!body.ok) {
        setError(
          [body.test?.title || body.message, body.test?.reason].filter(Boolean).join(" — "),
        );
      } else {
        setError(null);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  }

  async function call(
    providerId: string,
    action: "connect" | "disconnect" | "reconnect" | "sync",
    account?: string,
  ) {
    setBusyId(providerId);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/integrations/${providerId}/${action}`,
        {
          method: "POST",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify(account ? { account } : {}),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || `${action}_failed`);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  }

  async function patchConfig(
    path: "shipping-config" | "tax-config" | "invoice-config",
    payload: Record<string, unknown>,
  ) {
    setSaving(true);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/${path}`,
        {
          method: "PATCH",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "save_failed");
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  const visible = sections.filter((s) => {
    if (focus === "payments") return s.id === "payments";
    if (focus === "shipping") return s.id === "shipping";
    if (focus === "taxes") return s.id === "taxes";
    if (focus === "email") return s.id === "email";
    if (focus === "invoices") return s.id === "invoices";
    if (focus === "notifications") return s.id === "notifications";
    if (focus === "integrations") return true;
    return ["payments", "shipping", "taxes", "email", "invoices", "notifications"].includes(
      s.id,
    );
  });

  const shippingSection = sections.find((s) => s.id === "shipping");
  const taxSection = sections.find((s) => s.id === "taxes");
  const invoiceSection = sections.find((s) => s.id === "invoices");
  const emailSection = sections.find((s) => s.id === "email");
  const shippingCfg = (shippingSection?.config || {}) as ShippingConfig;
  const taxCfg = (taxSection?.config || {}) as TaxConfig;
  const invoiceCfg = (invoiceSection?.config || {}) as InvoiceConfig;
  const emailTransport = (emailSection?.config || {}) as EmailTransport;

  const title = useMemo(() => {
    if (focus === "payments") return "Payments";
    if (focus === "shipping") return "Shipping";
    if (focus === "taxes") return "Taxes / MwSt";
    if (focus === "email") return "Email";
    if (focus === "contact") return "Contact & Communication";
    if (focus === "invoices") return "Invoices";
    if (focus === "notifications") return "Notifications";
    if (focus === "integrations") return "All connections";
    return "Commerce · R3.3";
  }, [focus]);

  return (
    <div className="space-y-5">
      <div
        className={`rounded-3xl border p-5 sm:p-6 ${
          dark
            ? "border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-white/[0.03] to-transparent"
            : "border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-amber-50/40 shadow-sm"
        }`}
      >
        <p
          className={`text-xs font-semibold uppercase tracking-[0.2em] ${
            dark ? "text-emerald-300/70" : "text-emerald-700"
          }`}
        >
          {focus === "integrations" ? "Integrations" : "Commerce · R3.3"}
        </p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">{title}</h2>
        <p className={`mt-1 max-w-2xl text-sm ${muted}`}>
          Owner accounts only — Virtus Core never takes buyer funds. Same Connect card for
          Stripe, DHL, Gmail and every other provider.
        </p>
      </div>

      {error ? (
        <p className="text-sm text-rose-400" role="alert">
          {error}
        </p>
      ) : null}

      {(focus === "shipping" || focus === "overview" || focus === "integrations") &&
      shippingSection ? (
        <ShippingSettingsPanel
          dark={dark}
          muted={muted}
          cfg={shippingCfg}
          saving={saving}
          onSave={(payload) => void patchConfig("shipping-config", payload)}
        />
      ) : null}

      {(focus === "taxes" || focus === "overview" || focus === "integrations") &&
      taxSection ? (
        <TaxSettingsPanel
          dark={dark}
          muted={muted}
          cfg={taxCfg}
          saving={saving}
          onSave={(payload) => void patchConfig("tax-config", payload)}
        />
      ) : null}

      {(focus === "invoices" || focus === "integrations") && invoiceSection ? (
        <InvoiceSettingsPanel
          dark={dark}
          muted={muted}
          cfg={invoiceCfg}
          saving={saving}
          orderId={orderId}
          onSave={(payload) => void patchConfig("invoice-config", payload)}
        />
      ) : null}

      {(focus === "contact" ||
        focus === "email" ||
        focus === "overview" ||
        focus === "integrations") && (
        <StoreAdminBusinessProfile orderId={orderId} dark={dark} />
      )}

      {(focus === "email" || focus === "integrations" || focus === "overview") &&
      templates.length > 0 ? (
        <section
          className={`rounded-2xl border p-4 ${
            dark ? "border-white/10 bg-black/20" : "border-slate-200 bg-white"
          }`}
        >
          <h3 className="text-sm font-semibold">Email Templates</h3>
          <p className={`mt-1 text-xs ${muted}`}>
            Gen1 basic texts — Order Confirmation, Invoice, Shipping, Welcome, …
          </p>
          <ul className="mt-3 grid gap-1 sm:grid-cols-2">
            {templates.map((t) => (
              <li
                key={t.id}
                className={`rounded-lg border px-3 py-2 text-xs ${
                  dark ? "border-white/10" : "border-slate-100"
                }`}
              >
                {t.label}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {smtpProvider ? (
        <StoreAdminSmtpPanel
          orderId={orderId}
          providerId={smtpProvider}
          dark={dark}
          initial={emailTransport}
          onDone={() => {
            setSmtpProvider(null);
            void load();
          }}
          onCancel={() => setSmtpProvider(null)}
        />
      ) : null}

      {shippingProvider ? (
        <StoreAdminShippingPanel
          orderId={orderId}
          providerId={shippingProvider}
          dark={dark}
          onDone={() => {
            setShippingProvider(null);
            void load();
          }}
          onCancel={() => setShippingProvider(null)}
        />
      ) : null}

      {shipHint ? (
        <p className={`text-sm ${dark ? "text-emerald-300" : "text-emerald-700"}`}>{shipHint}</p>
      ) : null}

      {focus !== "contact"
        ? visible.map((section) => (
        <section key={section.id} className="space-y-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="text-lg font-semibold tracking-tight">{section.label}</h3>
            {section.phase ? (
              <p className={`text-xs ${muted}`}>{section.phase}</p>
            ) : null}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {(section.items || []).map((item) => (
              <IntegrationConnectionCard
                key={item.id}
                connection={item}
                dark={dark}
                busy={busyId === item.id || busyId === "email-test"}
                onConnect={(id, account) => void call(id, "connect", account)}
                onDisconnect={(id) => void call(id, "disconnect")}
                onReconnect={(id, account) => void call(id, "reconnect", account)}
                onSync={(id) => void call(id, "sync")}
                onOAuthConnect={(id) => {
                  if (id === "stripe") startStripeOAuth();
                }}
                onSmtpConnect={(id) => setSmtpProvider(id)}
                onTestEmail={() => void sendTestEmail()}
                onShippingConnect={(id) => setShippingProvider(id)}
                onCreateShipment={() => {
                  setShipHint("Open Orders → Create Shipment on a shop order.");
                }}
                onTrack={async (id) => {
                  setBusyId(id);
                  try {
                    const res = await fetch(
                      `${API}/api/client/stores/${orderId}/admin/shipping/shipments`,
                      { headers: { ...clientAuthHeaders() }, cache: "no-store" },
                    );
                    const body = await res.json().catch(() => ({}));
                    if (!res.ok) {
                      throw new Error(formatApiDetail(body.detail) || "track_failed");
                    }
                    const first = (body.shipments || [])[0] as
                      | { tracking_number?: string; status?: string; carrier?: string }
                      | undefined;
                    if (!first) {
                      setShipHint("No shipments yet — create one from Orders.");
                    } else {
                      setShipHint(
                        `${(first.carrier || id).toUpperCase()} · ${first.tracking_number} · ${first.status}`,
                      );
                      if (first.tracking_number) {
                        await fetch(
                          `${API}/api/client/stores/${orderId}/admin/shipping/track`,
                          {
                            method: "POST",
                            headers: {
                              ...clientAuthHeaders(),
                              "Content-Type": "application/json",
                            },
                            body: JSON.stringify({
                              tracking_number: first.tracking_number,
                              advance: true,
                            }),
                          },
                        );
                      }
                    }
                  } catch (err) {
                    setError(err instanceof Error ? err.message : String(err));
                  } finally {
                    setBusyId(null);
                  }
                }}
              />
            ))}
          </div>
        </section>
      ))
        : null}
    </div>
  );
}

function panelClass(dark: boolean) {
  return `rounded-2xl border p-4 sm:p-5 space-y-3 ${
    dark ? "border-white/10 bg-black/20" : "border-slate-200 bg-white"
  }`;
}

function inputClass(dark: boolean) {
  return `w-full rounded-xl border px-3 py-2 text-sm outline-none ${
    dark
      ? "border-white/10 bg-black/40 text-white"
      : "border-slate-200 bg-white text-slate-900"
  }`;
}

function ShippingSettingsPanel({
  dark,
  muted,
  cfg,
  saving,
  onSave,
}: {
  dark: boolean;
  muted: string;
  cfg: ShippingConfig;
  saving: boolean;
  onSave: (p: Record<string, unknown>) => void;
}) {
  const [country, setCountry] = useState(cfg.country || "DE");
  const [regions, setRegions] = useState((cfg.regions || []).join(", "));
  const [freeFrom, setFreeFrom] = useState(
    cfg.free_shipping_from_eur != null ? String(cfg.free_shipping_from_eur) : "",
  );
  const [minOrder, setMinOrder] = useState(
    cfg.min_order_eur != null ? String(cfg.min_order_eur) : "",
  );
  const [processing, setProcessing] = useState(String(cfg.processing_days ?? 1));
  const [rateMode, setRateMode] = useState(cfg.rate_mode || "fixed");
  const [methods, setMethods] = useState<ShippingMethod[]>(cfg.methods || []);

  useEffect(() => {
    setCountry(cfg.country || "DE");
    setRegions((cfg.regions || []).join(", "));
    setFreeFrom(
      cfg.free_shipping_from_eur != null ? String(cfg.free_shipping_from_eur) : "",
    );
    setMinOrder(cfg.min_order_eur != null ? String(cfg.min_order_eur) : "");
    setProcessing(String(cfg.processing_days ?? 1));
    setRateMode(cfg.rate_mode || "fixed");
    setMethods(cfg.methods || []);
  }, [cfg]);

  return (
    <section className={panelClass(dark)}>
      <h3 className="text-lg font-semibold tracking-tight">Shipping settings</h3>
      <p className={`text-xs ${muted}`}>
        Country, regions, free shipping threshold, rate mode and checkout methods.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className={`text-xs ${muted}`}>
          Country
          <input
            className={`mt-1 ${inputClass(dark)}`}
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          />
        </label>
        <label className={`text-xs ${muted}`}>
          Regions (comma)
          <input
            className={`mt-1 ${inputClass(dark)}`}
            value={regions}
            onChange={(e) => setRegions(e.target.value)}
          />
        </label>
        <label className={`text-xs ${muted}`}>
          Free shipping from (€)
          <input
            className={`mt-1 ${inputClass(dark)}`}
            value={freeFrom}
            placeholder="100"
            onChange={(e) => setFreeFrom(e.target.value)}
          />
        </label>
        <label className={`text-xs ${muted}`}>
          Min order (€)
          <input
            className={`mt-1 ${inputClass(dark)}`}
            value={minOrder}
            onChange={(e) => setMinOrder(e.target.value)}
          />
        </label>
        <label className={`text-xs ${muted}`}>
          Processing days
          <input
            className={`mt-1 ${inputClass(dark)}`}
            value={processing}
            onChange={(e) => setProcessing(e.target.value)}
          />
        </label>
        <label className={`text-xs ${muted}`}>
          Rate mode
          <select
            className={`mt-1 ${inputClass(dark)}`}
            value={rateMode}
            onChange={(e) => setRateMode(e.target.value)}
          >
            <option value="fixed">Fixed</option>
            <option value="weight">By weight</option>
            <option value="order_value">By order value</option>
            <option value="item_count">By item count</option>
            <option value="free">Always free</option>
          </select>
        </label>
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium">Methods</p>
        {methods.map((m, idx) => (
          <div
            key={m.id}
            className={`flex flex-wrap items-center gap-2 rounded-xl border px-3 py-2 text-sm ${
              dark ? "border-white/10" : "border-slate-200"
            }`}
          >
            <input
              className={`min-w-[8rem] flex-1 ${inputClass(dark)}`}
              value={m.label}
              onChange={(e) => {
                const next = [...methods];
                next[idx] = { ...m, label: e.target.value };
                setMethods(next);
              }}
            />
            <span className={muted}>
              {m.days_min}–{m.days_max} d
            </span>
            <input
              className={`w-24 ${inputClass(dark)}`}
              value={String(m.price_eur)}
              onChange={(e) => {
                const next = [...methods];
                next[idx] = { ...m, price_eur: Number(e.target.value) || 0 };
                setMethods(next);
              }}
            />
            <label className={`flex items-center gap-1 text-xs ${muted}`}>
              <input
                type="checkbox"
                checked={m.enabled}
                onChange={(e) => {
                  const next = [...methods];
                  next[idx] = { ...m, enabled: e.target.checked };
                  setMethods(next);
                }}
              />
              On
            </label>
          </div>
        ))}
      </div>

      <button
        type="button"
        disabled={saving}
        className={`rounded-xl px-4 py-2 text-xs font-semibold disabled:opacity-50 ${
          dark ? "bg-emerald-500/90 text-black" : "bg-emerald-700 text-white"
        }`}
        onClick={() =>
          onSave({
            country,
            regions: regions
              .split(",")
              .map((r) => r.trim())
              .filter(Boolean),
            free_shipping_from_eur: freeFrom === "" ? null : Number(freeFrom),
            min_order_eur: minOrder === "" ? null : Number(minOrder),
            processing_days: Number(processing) || 0,
            rate_mode: rateMode,
            methods,
          })
        }
      >
        {saving ? "Saving…" : "Save shipping"}
      </button>
    </section>
  );
}

function TaxSettingsPanel({
  dark,
  muted,
  cfg,
  saving,
  onSave,
}: {
  dark: boolean;
  muted: string;
  cfg: TaxConfig;
  saving: boolean;
  onSave: (p: Record<string, unknown>) => void;
}) {
  const [profile, setProfile] = useState(cfg.profile || "de_standard");
  const [vatId, setVatId] = useState(cfg.company_vat_id || "");
  const [eu, setEu] = useState(cfg.eu_sales_enabled !== false);
  const [exportZero, setExportZero] = useState(cfg.export_outside_eu_zero !== false);

  useEffect(() => {
    setProfile(cfg.profile || "de_standard");
    setVatId(cfg.company_vat_id || "");
    setEu(cfg.eu_sales_enabled !== false);
    setExportZero(cfg.export_outside_eu_zero !== false);
  }, [cfg]);

  return (
    <section className={panelClass(dark)}>
      <h3 className="text-lg font-semibold tracking-tight">Taxes (Germany / EU)</h3>
      <p className={`text-xs ${muted}`}>MwSt 19% · MwSt 7% · VAT exempt · EU sales · Export</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className={`text-xs ${muted}`}>
          Profile
          <select
            className={`mt-1 ${inputClass(dark)}`}
            value={profile}
            onChange={(e) => setProfile(e.target.value)}
          >
            <option value="de_standard">MwSt 19%</option>
            <option value="de_reduced">MwSt 7%</option>
            <option value="vat_exempt">VAT exempt</option>
            <option value="eu_sales">EU sales</option>
            <option value="export">Export outside EU</option>
          </select>
        </label>
        <label className={`text-xs ${muted}`}>
          VAT ID
          <input
            className={`mt-1 ${inputClass(dark)}`}
            value={vatId}
            placeholder="DE123456789"
            onChange={(e) => setVatId(e.target.value)}
          />
        </label>
      </div>
      <label className={`flex items-center gap-2 text-xs ${muted}`}>
        <input type="checkbox" checked={eu} onChange={(e) => setEu(e.target.checked)} />
        EU sales rules enabled
      </label>
      <label className={`flex items-center gap-2 text-xs ${muted}`}>
        <input
          type="checkbox"
          checked={exportZero}
          onChange={(e) => setExportZero(e.target.checked)}
        />
        Export outside EU → 0% VAT
      </label>
      <button
        type="button"
        disabled={saving}
        className={`rounded-xl px-4 py-2 text-xs font-semibold disabled:opacity-50 ${
          dark ? "bg-emerald-500/90 text-black" : "bg-emerald-700 text-white"
        }`}
        onClick={() =>
          onSave({
            profile,
            company_vat_id: vatId,
            eu_sales_enabled: eu,
            export_outside_eu_zero: exportZero,
          })
        }
      >
        {saving ? "Saving…" : "Save taxes"}
      </button>
    </section>
  );
}

function InvoiceSettingsPanel({
  dark,
  muted,
  cfg,
  saving,
  onSave,
  orderId,
}: {
  dark: boolean;
  muted: string;
  cfg: InvoiceConfig;
  saving: boolean;
  onSave: (p: Record<string, unknown>) => void;
  orderId: string;
}) {
  const [prefix, setPrefix] = useState(cfg.prefix || "INV");
  const [next, setNext] = useState(String(cfg.next_number ?? 1001));
  const [cnPrefix, setCnPrefix] = useState(cfg.credit_note_prefix || "CN");
  const [cnNext, setCnNext] = useState(String(cfg.next_credit_number ?? 1));
  const [autoPdf, setAutoPdf] = useState(cfg.auto_pdf !== false);
  const [company, setCompany] = useState(cfg.company_name || "");
  const [language, setLanguage] = useState(cfg.language || "de");
  const [currency, setCurrency] = useState(cfg.currency || "EUR");
  const [dateFormat, setDateFormat] = useState(cfg.date_format || "DD.MM.YYYY");
  const [signature, setSignature] = useState(cfg.signature_text || "");
  const [stamp, setStamp] = useState(Boolean(cfg.stamp_enabled));
  const [showQr, setShowQr] = useState(cfg.show_payment_qr !== false);
  const [docs, setDocs] = useState<
    { id: string; type: string; number: string; shop_order_id?: string }[]
  >([]);
  const [shopOrderId, setShopOrderId] = useState("");
  const [vectorHint, setVectorHint] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setPrefix(cfg.prefix || "INV");
    setNext(String(cfg.next_number ?? 1001));
    setCnPrefix(cfg.credit_note_prefix || "CN");
    setCnNext(String(cfg.next_credit_number ?? 1));
    setAutoPdf(cfg.auto_pdf !== false);
    setCompany(cfg.company_name || "");
    setLanguage(cfg.language || "de");
    setCurrency(cfg.currency || "EUR");
    setDateFormat(cfg.date_format || "DD.MM.YYYY");
    setSignature(cfg.signature_text || "");
    setStamp(Boolean(cfg.stamp_enabled));
    setShowQr(cfg.show_payment_qr !== false);
  }, [cfg]);

  const loadDocs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/client/stores/${orderId}/admin/documents`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      if (!res.ok) return;
      const body = await res.json();
      setDocs((body.documents || []) as typeof docs);
    } catch {
      /* optional */
    }
  }, [orderId]);

  useEffect(() => {
    void loadDocs();
  }, [loadDocs]);

  async function createInvoice() {
    if (!shopOrderId.trim()) {
      setErr("Shop order ID required");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/documents/invoice`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ shop_order_id: shopOrderId.trim(), language }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || "create_failed");
      setVectorHint(body.vector_hint?.message || "✅ Первый Invoice успешно создан.");
      if (body.vector_hint?.logo_message) {
        setVectorHint(
          `${body.vector_hint.message}\n${body.vector_hint.logo_message}`,
        );
      }
      await loadDocs();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function emailDoc(docId: string, resend = false) {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/documents/${docId}/email`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ resend }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || "email_failed");
      await loadDocs();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function downloadDoc(docId: string, number: string) {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/documents/${docId}/pdf`,
        { headers: { ...clientAuthHeaders() } },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(formatApiDetail(body.detail) || "download_failed");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${number || docId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function createCredit(invoiceDocId: string) {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/documents/credit-note`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({
            invoice_doc_id: invoiceDocId,
            reason: "Customer refund",
            refund_type: "full",
            language,
          }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || "credit_failed");
      await loadDocs();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={panelClass(dark)}>
      <h3 className="text-lg font-semibold tracking-tight">Invoices</h3>
      <p className={`text-xs ${muted}`}>
        PDF Invoice · Credit Note · Business Profile data · DE / EN / RU / UK
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className={`text-xs ${muted}`}>
          Invoice prefix
          <input className={`mt-1 ${inputClass(dark)}`} value={prefix} onChange={(e) => setPrefix(e.target.value)} placeholder="INV-2026-" />
        </label>
        <label className={`text-xs ${muted}`}>
          Next invoice #
          <input className={`mt-1 ${inputClass(dark)}`} value={next} onChange={(e) => setNext(e.target.value)} />
        </label>
        <label className={`text-xs ${muted}`}>
          Credit note prefix
          <input className={`mt-1 ${inputClass(dark)}`} value={cnPrefix} onChange={(e) => setCnPrefix(e.target.value)} />
        </label>
        <label className={`text-xs ${muted}`}>
          Next credit #
          <input className={`mt-1 ${inputClass(dark)}`} value={cnNext} onChange={(e) => setCnNext(e.target.value)} />
        </label>
        <label className={`text-xs ${muted}`}>
          Language
          <select className={`mt-1 ${inputClass(dark)}`} value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="de">Deutsch</option>
            <option value="en">English</option>
            <option value="ru">Русский</option>
            <option value="uk">Українська</option>
          </select>
        </label>
        <label className={`text-xs ${muted}`}>
          Currency
          <input className={`mt-1 ${inputClass(dark)}`} value={currency} onChange={(e) => setCurrency(e.target.value)} />
        </label>
        <label className={`text-xs ${muted}`}>
          Date format
          <select className={`mt-1 ${inputClass(dark)}`} value={dateFormat} onChange={(e) => setDateFormat(e.target.value)}>
            <option value="DD.MM.YYYY">DD.MM.YYYY</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            <option value="MM/DD/YYYY">MM/DD/YYYY</option>
          </select>
        </label>
        <label className={`text-xs ${muted}`}>
          Signature
          <input className={`mt-1 ${inputClass(dark)}`} value={signature} onChange={(e) => setSignature(e.target.value)} />
        </label>
        <label className={`text-xs ${muted} sm:col-span-2`}>
          Company name override (optional — Business Profile is preferred)
          <input className={`mt-1 ${inputClass(dark)}`} value={company} onChange={(e) => setCompany(e.target.value)} />
        </label>
      </div>
      <label className={`flex items-center gap-2 text-xs ${muted}`}>
        <input type="checkbox" checked={autoPdf} onChange={(e) => setAutoPdf(e.target.checked)} />
        Auto-generate PDF invoice
      </label>
      <label className={`flex items-center gap-2 text-xs ${muted}`}>
        <input type="checkbox" checked={showQr} onChange={(e) => setShowQr(e.target.checked)} />
        Payment QR on invoice
      </label>
      <label className={`flex items-center gap-2 text-xs ${muted}`}>
        <input type="checkbox" checked={stamp} onChange={(e) => setStamp(e.target.checked)} />
        Stamp (optional)
      </label>
      <button
        type="button"
        disabled={saving}
        className={`rounded-xl px-4 py-2 text-xs font-semibold disabled:opacity-50 ${
          dark ? "bg-emerald-500/90 text-black" : "bg-emerald-700 text-white"
        }`}
        onClick={() =>
          onSave({
            prefix,
            next_number: Number(next) || 1001,
            credit_note_prefix: cnPrefix,
            next_credit_number: Number(cnNext) || 1,
            auto_pdf: autoPdf,
            company_name: company,
            include_order_number: true,
            language,
            currency,
            date_format: dateFormat,
            signature_text: signature,
            stamp_enabled: stamp,
            show_payment_qr: showQr,
          })
        }
      >
        {saving ? "Saving…" : "Save invoices"}
      </button>

      <div className={`mt-4 border-t pt-4 ${dark ? "border-white/10" : "border-slate-200"}`}>
        <h4 className="text-sm font-semibold">Create Invoice PDF</h4>
        <div className="mt-2 flex flex-wrap gap-2">
          <input
            className={inputClass(dark)}
            placeholder="Shop order ID"
            value={shopOrderId}
            onChange={(e) => setShopOrderId(e.target.value)}
          />
          <button
            type="button"
            disabled={busy}
            className={`rounded-xl px-3 py-2 text-xs font-semibold ${
              dark ? "bg-sky-500/90 text-black" : "bg-sky-700 text-white"
            }`}
            onClick={() => void createInvoice()}
          >
            Generate PDF
          </button>
        </div>
        {vectorHint ? (
          <p className={`mt-2 whitespace-pre-line text-xs ${dark ? "text-emerald-300" : "text-emerald-800"}`}>
            {vectorHint}
          </p>
        ) : null}
        {err ? <p className="mt-2 text-xs text-rose-400">{err}</p> : null}
        <ul className="mt-3 space-y-2">
          {docs.map((d) => (
            <li
              key={d.id}
              className={`flex flex-wrap items-center justify-between gap-2 rounded-xl border px-3 py-2 text-xs ${
                dark ? "border-white/10" : "border-slate-200"
              }`}
            >
              <span>
                {d.type === "credit_note" ? "Credit Note" : "Invoice"} {d.number}
                {d.shop_order_id ? ` · ${d.shop_order_id}` : ""}
              </span>
              <span className="flex flex-wrap gap-2">
                <button type="button" className="underline" onClick={() => void downloadDoc(d.id, d.number)}>
                  Download PDF
                </button>
                <button type="button" className="underline" onClick={() => void emailDoc(d.id)}>
                  Send Email
                </button>
                <button type="button" className="underline" onClick={() => void emailDoc(d.id, true)}>
                  Resend
                </button>
                {d.type === "invoice" ? (
                  <button type="button" className="underline" onClick={() => void createCredit(d.id)}>
                    Credit Note
                  </button>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
