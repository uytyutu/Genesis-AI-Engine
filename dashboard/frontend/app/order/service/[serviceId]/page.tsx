"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { PublicPageShell } from "../../../components/PublicPageShell";
import { BRAND_NAME } from "../../../lib/publicBrand";
import { formatApiDetail } from "../../../lib/formatApiError";
import { startOrderCheckout } from "../../../lib/orderCheckout";
import { publicApiBase } from "../../../lib/publicApiBase";
import { getServiceSpec, type ServiceFieldId } from "../../../lib/serviceOrderSpecs";
import { getVisitorId } from "../../../lib/visitorId";

const API = publicApiBase();

type FormState = Partial<Record<ServiceFieldId, string>>;
type Step = "form" | "confirm";

export default function ServiceOrderPage() {
  const params = useParams();
  const router = useRouter();
  const serviceId = String(params?.serviceId || "");
  const spec = useMemo(() => getServiceSpec(serviceId), [serviceId]);

  const [values, setValues] = useState<FormState>({});
  const [step, setStep] = useState<Step>("form");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [waitlisted, setWaitlisted] = useState(false);
  const [orderId, setOrderId] = useState("");

  if (!spec) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-lg px-4 py-16 text-center">
          <h1 className="text-xl font-semibold text-white">Service not found</h1>
          <Link href="/site" className="mt-4 inline-block text-emerald-300 hover:underline">
            ← Back to storefront
          </Link>
        </main>
      </PublicPageShell>
    );
  }

  if (spec.id === "landing_website") {
    router.replace("/order");
    return null;
  }
  if (spec.id === "ai_business_bot") {
    router.replace("/order/bot");
    return null;
  }
  if (spec.id === "website_check") {
    router.replace("/site?service=analysis");
    return null;
  }

  function setField(id: ServiceFieldId, v: string) {
    setValues((prev) => ({ ...prev, [id]: v }));
  }

  function validateForm(): string | null {
    for (const f of spec!.fields) {
      if (f.required && !(values[f.id] || "").trim()) {
        return `Please fill: ${f.label}`;
      }
    }
    const email = (values.email || "").trim();
    if (spec!.fields.some((f) => f.id === "email") && !email.includes("@")) {
      return "Valid email required";
    }
    return null;
  }

  function buildWishes(): string {
    return [
      values.goal?.trim(),
      values.notes?.trim(),
      values.access_notes?.trim(),
      values.gbp_name ? `GBP name: ${values.gbp_name}` : "",
      values.gbp_category ? `GBP category: ${values.gbp_category}` : "",
      values.hosting_from ? `From: ${values.hosting_from}` : "",
      values.hosting_to ? `To: ${values.hosting_to}` : "",
    ]
      .filter(Boolean)
      .join("\n");
  }

  async function onSubmitForm(e: FormEvent) {
    e.preventDefault();
    setError("");
    const invalid = validateForm();
    if (invalid) {
      setError(invalid);
      return;
    }
    if (spec!.availability === "coming_soon") {
      setBusy(true);
      try {
        const wishes = buildWishes();
        const email = (values.email || "").trim();
        const res = await fetch(`${API}/api/sales/orders`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            package_id: spec!.id,
            business_name: (values.business_name || "").trim() || "Interest request",
            description: `[interest] ${wishes || spec!.blurb}`,
            email,
            phone: (values.phone || "").trim() || null,
            whatsapp: (values.whatsapp || "").trim() || null,
            city: (values.city || "").trim() || null,
            company_website: (values.website_url || "").trim() || null,
            extra_wishes: wishes || null,
            visitor_id: getVisitorId(),
          }),
        });
        const body = await res.json();
        if (!res.ok) {
          throw new Error(formatApiDetail(body.detail) || "Could not save interest");
        }
        setOrderId(String(body.order_id || body.id || ""));
        setWaitlisted(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Interest failed");
      } finally {
        setBusy(false);
      }
      return;
    }
    setStep("confirm");
  }

  async function onConfirmPay() {
    setError("");
    setBusy(true);
    try {
      const wishes = buildWishes();
      const email = (values.email || "").trim();
      const res = await fetch(`${API}/api/sales/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          package_id: spec!.id,
          business_name: (values.business_name || "").trim() || "Service order",
          description: wishes || spec!.blurb,
          email,
          phone: (values.phone || "").trim() || null,
          whatsapp: (values.whatsapp || "").trim() || null,
          city: (values.city || "").trim() || null,
          company_website: (values.website_url || "").trim() || null,
          extra_wishes: wishes || null,
          visitor_id: getVisitorId(),
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Could not create order");
      }
      const id = String(body.order_id || body.id || "");
      if (!id) throw new Error("No order id");
      setOrderId(id);
      const url = await startOrderCheckout(id, {
        successPath: `/order/status/${id}?paid=1`,
        cancelPath: `/order/service/${spec!.id}?canceled=1`,
      });
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Order failed");
      setBusy(false);
    }
  }

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-xl px-4 py-10">
        <Link href="/site" className="text-sm text-emerald-300 hover:underline">
          ← {BRAND_NAME} storefront
        </Link>
        <p className="mt-6 text-xs font-semibold uppercase tracking-[0.25em] text-zinc-500">
          {step === "form" ? "Order form" : "Ready for payment"}
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-white">{spec.name}</h1>
        <p className="mt-1 text-lg text-emerald-200/90">{spec.price_label}</p>
        <p className="mt-3 text-sm text-zinc-400">{spec.blurb}</p>

        {step === "confirm" ? (
          <div className="mt-8 space-y-5 rounded-2xl border border-emerald-500/25 bg-emerald-500/[0.07] p-5">
            <p className="text-lg font-semibold text-white">
              Thanks — your request is prepared.
            </p>
            <p className="text-sm text-zinc-300">
              Next you pay securely. After payment this is what you get:
            </p>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Included
              </p>
              <ul className="mt-2 space-y-1 text-sm text-zinc-200">
                {spec.includes.map((line) => (
                  <li key={line}>✓ {line}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Timeline
              </p>
              <p className="mt-1 text-sm text-zinc-200">{spec.timeline}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                After payment
              </p>
              <ul className="mt-2 space-y-1 text-sm text-zinc-200">
                {spec.afterPay.map((line) => (
                  <li key={line}>→ {line}</li>
                ))}
              </ul>
            </div>
            <p className="text-xs text-zinc-500">Support: {spec.support}</p>
            {error ? (
              <p className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-100">
                {error}
              </p>
            ) : null}
            <div className="flex flex-col gap-2 sm:flex-row">
              <button
                type="button"
                onClick={() => setStep("form")}
                disabled={busy}
                className="rounded-xl border border-white/20 px-4 py-3 text-sm font-medium text-white hover:bg-white/5 disabled:opacity-60"
              >
                ← Edit form
              </button>
              <button
                type="button"
                onClick={() => void onConfirmPay()}
                disabled={busy}
                className="flex-1 rounded-xl bg-emerald-500 py-3 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-60"
              >
                {busy ? "Opening payment…" : "Pay securely →"}
              </button>
            </div>
            {orderId ? (
              <p className="text-[11px] text-zinc-500">Order draft: {orderId}</p>
            ) : null}
          </div>
        ) : (
          <form onSubmit={onSubmitForm} className="mt-8 space-y-4">
            {spec.availability === "coming_soon" ? (
              <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
                Checkout is not open yet — submit interest and we will contact you.
              </p>
            ) : (
              <p className="text-xs text-zinc-500">
                Step 1 of 2: tell us what you need → then confirm value → payment.
              </p>
            )}

            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs text-zinc-400">
              <p className="font-semibold text-zinc-300">What&apos;s included</p>
              <ul className="mt-2 space-y-1">
                {spec.includes.map((line) => (
                  <li key={line}>✓ {line}</li>
                ))}
              </ul>
              <p className="mt-2 text-zinc-500">
                {spec.stages.join(" → ")} · {spec.timeline}
              </p>
            </div>

            {spec.fields.map((f) => (
              <label key={f.id} className="block text-sm text-zinc-300">
                <span className="mb-1.5 block font-medium text-zinc-200">
                  {f.label}
                  {f.required ? " *" : ""}
                </span>
                {f.multiline ? (
                  <textarea
                    rows={4}
                    value={values[f.id] || ""}
                    onChange={(e) => setField(f.id, e.target.value)}
                    placeholder={f.placeholder}
                    className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2.5 text-white outline-none focus:border-emerald-400/50"
                  />
                ) : (
                  <input
                    type={f.type || "text"}
                    value={values[f.id] || ""}
                    onChange={(e) => setField(f.id, e.target.value)}
                    placeholder={f.placeholder}
                    className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2.5 text-white outline-none focus:border-emerald-400/50"
                  />
                )}
              </label>
            ))}

            {error ? (
              <p className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-100">
                {error}
              </p>
            ) : null}
            {waitlisted ? (
              <div className="space-y-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-3 text-sm text-emerald-100">
                <p className="font-semibold text-white">Thanks — interest recorded.</p>
                <p>
                  Checkout for this service is not open yet. We will contact you when it
                  goes live. No payment was taken.
                </p>
                {orderId ? (
                  <p className="text-[11px] text-emerald-200/70">Reference: {orderId}</p>
                ) : null}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={busy || waitlisted}
              className="w-full rounded-xl bg-emerald-500 py-3 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-60"
            >
              {busy
                ? "Saving…"
                : waitlisted
                  ? "Interest sent"
                  : spec.availability === "coming_soon"
                    ? "Send interest"
                    : "Prepare request →"}
            </button>
          </form>
        )}
      </main>
    </PublicPageShell>
  );
}
