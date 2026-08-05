"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  StoreAdminComingSoon,
  StoreAdminShell,
  type StoreAdminSectionId,
} from "../../../components/StoreAdminShell";
import { StoreAdminProducts } from "../../../components/StoreAdminProducts";
import { StoreAdminDesign } from "../../../components/StoreAdminDesign";
import { StoreAdminCustomers } from "../../../components/StoreAdminCustomers";
import { StoreAdminCommerce } from "../../../components/StoreAdminCommerce";
import { clientAuthHeaders, getClientToken } from "../../../lib/clientAuth";
import { formatApiDetail } from "../../../lib/formatApiError";
import { publicApiBase } from "../../../lib/publicApiBase";

const API = publicApiBase();

type StoreMeta = {
  store_name?: string;
  shop_pipeline?: string | null;
  product_id?: string | null;
  version?: number | null;
};

const ACTIVITY = [
  { t: "Store Admin opened", d: "Foundation ready — manage your shop from here." },
  { t: "Product catalog live", d: "Add, edit, media, SEO and AI assist are available." },
  { t: "Design studio", d: "Brand, colors, hero and homepage — with live preview." },
];

export default function StoreAdminPage() {
  const params = useParams();
  const orderId = String(params?.orderId || "");
  const router = useRouter();
  const [section, setSection] = useState<StoreAdminSectionId>("dashboard");
  const [meta, setMeta] = useState<StoreMeta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [themeDark, setThemeDark] = useState(true);
  const [productCount, setProductCount] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!getClientToken()) {
      router.replace(
        `/client/login?next=${encodeURIComponent(`/client/stores/${orderId}/admin`)}`,
      );
      return;
    }
    try {
      const res = await fetch(`${API}/api/client/stores/${orderId}`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Store not found");
      }
      setMeta(body as StoreMeta);
      setError(null);
      try {
        const pr = await fetch(
          `${API}/api/client/stores/${orderId}/admin/products`,
          { headers: { ...clientAuthHeaders() }, cache: "no-store" },
        );
        if (pr.ok) {
          const pb = await pr.json();
          setProductCount(Number(pb.count ?? (pb.products || []).length) || 0);
        }
      } catch {
        /* optional metric */
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [orderId, router]);

  useEffect(() => {
    void load();
  }, [load]);

  const storeName = meta?.store_name || "Your online shop";
  const dark = themeDark;

  const METRICS = [
    {
      id: "revenue",
      label: "Revenue",
      value: "—",
      hint: "Connects with Commerce",
    },
    { id: "orders", label: "Orders", value: "0", hint: "No orders yet" },
    {
      id: "customers",
      label: "Customers",
      value: "0",
      hint: "Shop buyers (separate login)",
    },
    {
      id: "products",
      label: "Products",
      value: productCount === null ? "…" : String(productCount),
      hint: "Open Products to manage catalog",
    },
  ] as const;

  return (
    <StoreAdminShell
      orderId={orderId}
      storeName={storeName}
      section={section}
      onSection={setSection}
      onThemeChange={(t) => setThemeDark(t === "dark")}
    >
      {error ? (
        <p
          className={`mb-4 rounded-2xl border px-4 py-3 text-sm ${
            dark
              ? "border-rose-500/30 bg-rose-500/10 text-rose-200"
              : "border-rose-200 bg-rose-50 text-rose-800"
          }`}
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {section === "dashboard" ? (
        <div className="space-y-6">
          <div
            className={`overflow-hidden rounded-3xl border p-6 sm:p-8 ${
              dark
                ? "border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-white/[0.03] to-transparent"
                : "border-emerald-200/80 bg-gradient-to-br from-emerald-50 via-white to-amber-50/40 shadow-sm"
            }`}
          >
            <p
              className={`text-xs font-semibold uppercase tracking-[0.22em] ${
                dark ? "text-emerald-300/80" : "text-emerald-800"
              }`}
            >
              Welcome
            </p>
            <h2 className="mt-2 max-w-xl text-2xl font-semibold tracking-tight sm:text-3xl">
              Your shop control center
            </h2>
            <p
              className={`mt-2 max-w-2xl text-sm ${
                dark ? "text-zinc-400" : "text-slate-600"
              }`}
            >
              This is Store Admin — separate from Virtus Core Client Workspace. Here you
              manage your online shop. Buyers will later use their own customer accounts.
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <span
                className={`rounded-full px-2.5 py-1 ${
                  dark ? "bg-white/5 text-zinc-400" : "bg-white text-slate-600 shadow-sm"
                }`}
              >
                Status: {meta?.shop_pipeline || "—"}
              </span>
              {meta?.version ? (
                <span
                  className={`rounded-full px-2.5 py-1 ${
                    dark ? "bg-white/5 text-zinc-400" : "bg-white text-slate-600 shadow-sm"
                  }`}
                >
                  Storefront v{meta.version}
                </span>
              ) : null}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {METRICS.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => {
                  if (m.id === "products") setSection("products");
                }}
                className={`rounded-2xl border p-5 text-left transition hover:-translate-y-0.5 hover:shadow-lg ${
                  dark
                    ? "border-white/10 bg-white/[0.03] hover:border-white/20"
                    : "border-slate-200/90 bg-white/80 shadow-sm hover:border-slate-300"
                }`}
              >
                <p
                  className={`text-[11px] font-semibold uppercase tracking-wider ${
                    dark ? "text-zinc-500" : "text-slate-500"
                  }`}
                >
                  {m.label}
                </p>
                <p className="mt-2 text-3xl font-semibold tracking-tight">{m.value}</p>
                <p
                  className={`mt-1 text-xs ${dark ? "text-zinc-500" : "text-slate-500"}`}
                >
                  {m.hint}
                </p>
                <div
                  className={`mt-4 flex h-10 items-end gap-1 opacity-60 ${
                    dark ? "text-emerald-400/40" : "text-emerald-600/30"
                  }`}
                  aria-hidden
                >
                  {[40, 55, 35, 70, 50, 85, 60, 75].map((h, i) => (
                    <span
                      key={i}
                      className={`flex-1 rounded-sm ${
                        dark ? "bg-emerald-400/30" : "bg-emerald-600/25"
                      }`}
                      style={{ height: `${h}%` }}
                    />
                  ))}
                </div>
              </button>
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-5">
            <div
              className={`rounded-3xl border p-5 lg:col-span-3 ${
                dark
                  ? "border-white/10 bg-white/[0.03]"
                  : "border-slate-200 bg-white/80 shadow-sm"
              }`}
            >
              <p
                className={`text-xs font-semibold uppercase tracking-wider ${
                  dark ? "text-zinc-500" : "text-slate-500"
                }`}
              >
                Recent activity
              </p>
              <ul className="mt-4 space-y-3">
                {ACTIVITY.map((row) => (
                  <li
                    key={row.t}
                    className={`rounded-2xl border px-4 py-3 ${
                      dark
                        ? "border-white/5 bg-black/20"
                        : "border-slate-100 bg-slate-50/80"
                    }`}
                  >
                    <p className="text-sm font-medium">{row.t}</p>
                    <p
                      className={`mt-0.5 text-xs ${
                        dark ? "text-zinc-500" : "text-slate-500"
                      }`}
                    >
                      {row.d}
                    </p>
                  </li>
                ))}
              </ul>
            </div>

            <div
              className={`rounded-3xl border p-5 lg:col-span-2 ${
                dark
                  ? "border-white/10 bg-white/[0.03]"
                  : "border-slate-200 bg-white/80 shadow-sm"
              }`}
            >
              <p
                className={`text-xs font-semibold uppercase tracking-wider ${
                  dark ? "text-zinc-500" : "text-slate-500"
                }`}
              >
                Quick links
              </p>
              <ul className="mt-4 space-y-2 text-sm">
                <li>
                  <button
                    type="button"
                    className={`w-full rounded-xl px-3 py-2.5 text-left transition ${
                      dark
                        ? "hover:bg-emerald-500/10 hover:text-emerald-200"
                        : "hover:bg-emerald-50 hover:text-emerald-900"
                    }`}
                    onClick={() => setSection("products")}
                  >
                    Products → manage catalog
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    className={`w-full rounded-xl px-3 py-2.5 text-left transition ${
                      dark
                        ? "hover:bg-emerald-500/10 hover:text-emerald-200"
                        : "hover:bg-emerald-50 hover:text-emerald-900"
                    }`}
                    onClick={() => setSection("design")}
                  >
                    Design → live preview
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    className={`w-full rounded-xl px-3 py-2.5 text-left transition ${
                      dark
                        ? "hover:bg-emerald-500/10 hover:text-emerald-200"
                        : "hover:bg-emerald-50 hover:text-emerald-900"
                    }`}
                    onClick={() => setSection("commerce")}
                  >
                    Commerce → prepare payments
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      ) : section === "products" ? (
        <StoreAdminProducts
          orderId={orderId}
          dark={dark}
          storeName={storeName}
        />
      ) : section === "design" ? (
        <StoreAdminDesign
          orderId={orderId}
          dark={dark}
          storeName={storeName}
        />
      ) : section === "customers" ? (
        <StoreAdminCustomers orderId={orderId} dark={dark} />
      ) : section === "commerce" ? (
        <StoreAdminCommerce orderId={orderId} dark={dark} focus="overview" />
      ) : section === "payments" ? (
        <StoreAdminCommerce orderId={orderId} dark={dark} focus="payments" />
      ) : section === "shipping" ? (
        <StoreAdminCommerce orderId={orderId} dark={dark} focus="shipping" />
      ) : (
        <StoreAdminComingSoon
          title={
            section.charAt(0).toUpperCase() + section.slice(1).replace(/_/g, " ")
          }
          dark={dark}
        />
      )}
    </StoreAdminShell>
  );
}
