"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

export type CatalogImage = {
  id: string;
  url?: string | null;
  is_primary?: boolean;
  sort?: number;
  optimized?: boolean;
};

export type CatalogProduct = {
  id: string;
  product_type: string;
  status: "draft" | "published" | string;
  title: string;
  short_description?: string;
  description?: string;
  price: number;
  compare_at_price?: number | null;
  currency?: string;
  sku?: string;
  stock_qty?: number;
  stock_status?: string;
  category?: string;
  subcategory?: string;
  brand?: string;
  variants?: {
    size?: string[];
    color?: string[];
    material?: string[];
    weight?: string | null;
  };
  images?: CatalogImage[];
  seo?: { title?: string; description?: string; slug?: string };
};

const PRODUCT_TYPES = [
  { id: "physical", label: "Physical Product", active: true },
  { id: "digital", label: "Digital Product", active: false },
  { id: "service", label: "Service", active: false },
  { id: "ticket", label: "Ticket", active: false },
  { id: "booking", label: "Booking", active: false },
] as const;

type Props = {
  orderId: string;
  dark?: boolean;
  storeName?: string;
};

function emptyDraft(productType = "physical"): Partial<CatalogProduct> {
  return {
    product_type: productType,
    status: "draft",
    title: "",
    short_description: "",
    description: "",
    price: 0,
    compare_at_price: null,
    currency: "EUR",
    sku: "",
    stock_qty: 0,
    stock_status: "in_stock",
    category: "",
    subcategory: "",
    brand: "",
    variants: { size: [], color: [], material: [], weight: "" },
    seo: { title: "", description: "", slug: "" },
    images: [],
  };
}

function listToCsv(arr?: string[]) {
  return (arr || []).join(", ");
}

function csvToList(s: string) {
  return s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

function mediaUrl(url: string | null | undefined) {
  if (!url) return "";
  const token = getClientToken();
  const abs = url.startsWith("http") ? url : `${API}${url}`;
  if (!token) return abs;
  const join = abs.includes("?") ? "&" : "?";
  return `${abs}${join}access_token=${encodeURIComponent(token)}`;
}

export function StoreAdminProducts({ orderId, dark = true, storeName }: Props) {
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [editorOpen, setEditorOpen] = useState(false);
  const [draft, setDraft] = useState<Partial<CatalogProduct>>(emptyDraft());
  const [saving, setSaving] = useState(false);
  const [aiHint, setAiHint] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [dragId, setDragId] = useState<string | null>(null);
  const [bulkBusy, setBulkBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (q.trim()) params.set("q", q.trim());
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/products?${params}`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Failed to load products");
      }
      setProducts((body.products || []) as CatalogProduct[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [orderId, q, statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const allSelected = useMemo(
    () => products.length > 0 && products.every((p) => selected.has(p.id)),
    [products, selected],
  );

  const openCreate = () => {
    setDraft(emptyDraft("physical"));
    setAiHint("");
    setEditorOpen(true);
  };

  const openEdit = (p: CatalogProduct) => {
    setDraft({
      ...emptyDraft(p.product_type),
      ...p,
      variants: {
        size: p.variants?.size || [],
        color: p.variants?.color || [],
        material: p.variants?.material || [],
        weight: p.variants?.weight || "",
      },
      seo: {
        title: p.seo?.title || "",
        description: p.seo?.description || "",
        slug: p.seo?.slug || "",
      },
    });
    setAiHint(p.title || "");
    setEditorOpen(true);
  };

  const saveProduct = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        product_type: draft.product_type || "physical",
        status: draft.status || "draft",
        title: draft.title || "",
        short_description: draft.short_description || "",
        description: draft.description || "",
        price: Number(draft.price || 0),
        compare_at_price:
          draft.compare_at_price === null || draft.compare_at_price === undefined
            ? null
            : Number(draft.compare_at_price),
        currency: draft.currency || "EUR",
        sku: draft.sku || "",
        stock_qty: Number(draft.stock_qty || 0),
        stock_status: draft.stock_status || "in_stock",
        category: draft.category || "",
        subcategory: draft.subcategory || "",
        brand: draft.brand || "",
        variants: draft.variants || {},
        seo: draft.seo || {},
      };
      const isEdit = Boolean(draft.id);
      const res = await fetch(
        isEdit
          ? `${API}/api/client/stores/${orderId}/admin/products/${draft.id}`
          : `${API}/api/client/stores/${orderId}/admin/products`,
        {
          method: isEdit ? "PATCH" : "POST",
          headers: {
            "Content-Type": "application/json",
            ...clientAuthHeaders(),
          },
          body: JSON.stringify(payload),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Save failed");
      }
      const saved = body.product as CatalogProduct;
      setDraft({ ...draft, ...saved });
      await load();
      if (!isEdit) {
        setDraft({ ...saved });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  const deleteOne = async (id: string) => {
    if (!window.confirm("Delete this product?")) return;
    const res = await fetch(
      `${API}/api/client/stores/${orderId}/admin/products/${id}`,
      { method: "DELETE", headers: { ...clientAuthHeaders() } },
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setError(formatApiDetail(body.detail) || "Delete failed");
      return;
    }
    setSelected((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    if (draft.id === id) setEditorOpen(false);
    await load();
  };

  const runBulk = async (action: string, extra: Record<string, unknown> = {}) => {
    const ids = Array.from(selected);
    if (!ids.length) return;
    setBulkBusy(true);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/products/bulk`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...clientAuthHeaders(),
          },
          body: JSON.stringify({ action, product_ids: ids, ...extra }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Bulk action failed");
      }
      setSelected(new Set());
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBulkBusy(false);
    }
  };

  const runAi = async () => {
    setAiBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/products/ai-generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...clientAuthHeaders(),
          },
          body: JSON.stringify({
            hint: aiHint || draft.title || "",
            language: "en",
            product_type: draft.product_type || "physical",
          }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "AI generate failed");
      }
      setDraft((prev) => ({
        ...prev,
        title: body.title || prev.title,
        short_description: body.short_description || prev.short_description,
        description: body.description || prev.description,
        category: body.category || prev.category,
        subcategory: body.subcategory || prev.subcategory,
        brand: body.brand || prev.brand || storeName,
        sku: prev.sku || body.suggested_sku || "",
        variants: body.variants || prev.variants,
        seo: body.seo || prev.seo,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setAiBusy(false);
    }
  };

  const uploadImages = async (files: FileList | null) => {
    if (!files?.length || !draft.id) {
      setError("Save the product first, then upload photos.");
      return;
    }
    const fd = new FormData();
    Array.from(files).forEach((f) => fd.append("files", f));
    const res = await fetch(
      `${API}/api/client/stores/${orderId}/admin/products/${draft.id}/media`,
      {
        method: "POST",
        headers: { ...clientAuthHeaders() },
        body: fd,
      },
    );
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(formatApiDetail(body.detail) || "Upload failed");
      return;
    }
    setDraft({ ...draft, ...(body.product as CatalogProduct) });
    await load();
  };

  const persistImageOrder = async (
    images: CatalogImage[],
    primaryId?: string,
  ) => {
    if (!draft.id) return;
    const res = await fetch(
      `${API}/api/client/stores/${orderId}/admin/products/${draft.id}/media`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...clientAuthHeaders(),
        },
        body: JSON.stringify({
          image_ids: images.map((i) => i.id),
          primary_image_id: primaryId,
        }),
      },
    );
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(formatApiDetail(body.detail) || "Reorder failed");
      return;
    }
    setDraft({ ...draft, ...(body.product as CatalogProduct) });
  };

  const onDropImage = async (targetId: string) => {
    if (!dragId || dragId === targetId) return;
    const images = [...(draft.images || [])].sort(
      (a, b) => (a.sort || 0) - (b.sort || 0),
    );
    const from = images.findIndex((i) => i.id === dragId);
    const to = images.findIndex((i) => i.id === targetId);
    if (from < 0 || to < 0) return;
    const [moved] = images.splice(from, 1);
    images.splice(to, 0, moved);
    setDraft({ ...draft, images });
    setDragId(null);
    await persistImageOrder(images);
  };

  const setPrimary = async (imageId: string) => {
    const images = (draft.images || []).map((img) => ({
      ...img,
      is_primary: img.id === imageId,
    }));
    setDraft({ ...draft, images });
    await persistImageOrder(images, imageId);
  };

  const removeImage = async (imageId: string) => {
    if (!draft.id) return;
    const res = await fetch(
      `${API}/api/client/stores/${orderId}/admin/products/${draft.id}/media/${imageId}`,
      { method: "DELETE", headers: { ...clientAuthHeaders() } },
    );
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(formatApiDetail(body.detail) || "Remove image failed");
      return;
    }
    setDraft({ ...draft, ...(body.product as CatalogProduct) });
    await load();
  };

  const card = dark
    ? "border-white/10 bg-white/[0.03]"
    : "border-slate-200 bg-white/80 shadow-sm";
  const input = dark
    ? "border-white/10 bg-black/30 text-zinc-100 placeholder:text-zinc-600"
    : "border-slate-200 bg-white text-slate-900 placeholder:text-slate-400";
  const muted = dark ? "text-zinc-500" : "text-slate-500";

  return (
    <div className="space-y-5">
      <div className={`rounded-3xl border p-5 sm:p-6 ${card}`}>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p
              className={`text-xs font-semibold uppercase tracking-[0.2em] ${
                dark ? "text-emerald-300/70" : "text-emerald-700"
              }`}
            >
              Catalog
            </p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight">
              Products
            </h2>
            <p className={`mt-1 text-sm ${muted}`}>
              Manage your shop catalog. Physical products are live — other types
              are reserved in the schema.
            </p>
          </div>
          <button
            type="button"
            onClick={openCreate}
            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-zinc-950 hover:bg-emerald-400"
          >
            + Add product
          </button>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search title, SKU, category…"
            className={`min-w-[14rem] flex-1 rounded-xl border px-3 py-2 text-sm ${input}`}
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={`rounded-xl border px-3 py-2 text-sm ${input}`}
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
          </select>
        </div>

        {selected.size > 0 ? (
          <div
            className={`mt-4 flex flex-wrap items-center gap-2 rounded-2xl border px-3 py-2 ${
              dark ? "border-emerald-500/20 bg-emerald-500/5" : "border-emerald-200 bg-emerald-50"
            }`}
          >
            <span className="text-xs font-medium">{selected.size} selected</span>
            <button
              type="button"
              disabled={bulkBusy}
              className="rounded-lg px-2 py-1 text-xs hover:underline"
              onClick={() => void runBulk("set_status", { status: "published" })}
            >
              Publish
            </button>
            <button
              type="button"
              disabled={bulkBusy}
              className="rounded-lg px-2 py-1 text-xs hover:underline"
              onClick={() => void runBulk("set_status", { status: "draft" })}
            >
              Draft
            </button>
            <button
              type="button"
              disabled={bulkBusy}
              className="rounded-lg px-2 py-1 text-xs hover:underline"
              onClick={() => {
                const category = window.prompt("New category for selected:");
                if (category) void runBulk("set_category", { category });
              }}
            >
              Set category
            </button>
            <button
              type="button"
              disabled={bulkBusy}
              className="rounded-lg px-2 py-1 text-xs hover:underline"
              onClick={() => {
                const price = window.prompt("New price (EUR):");
                if (price != null && price !== "") {
                  void runBulk("set_price", { price: Number(price) });
                }
              }}
            >
              Set price
            </button>
            <button
              type="button"
              disabled={bulkBusy}
              className="rounded-lg px-2 py-1 text-xs text-rose-400 hover:underline"
              onClick={() => {
                if (window.confirm(`Delete ${selected.size} products?`)) {
                  void runBulk("delete");
                }
              }}
            >
              Delete
            </button>
          </div>
        ) : null}

        {error ? (
          <p
            className={`mt-4 rounded-xl border px-3 py-2 text-sm ${
              dark
                ? "border-rose-500/30 bg-rose-500/10 text-rose-200"
                : "border-rose-200 bg-rose-50 text-rose-800"
            }`}
            role="alert"
          >
            {error}
          </p>
        ) : null}
      </div>

      <div className={`overflow-hidden rounded-3xl border ${card}`}>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead
              className={`border-b text-xs uppercase tracking-wider ${
                dark
                  ? "border-white/10 text-zinc-500"
                  : "border-slate-200 text-slate-500"
              }`}
            >
              <tr>
                <th className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelected(new Set(products.map((p) => p.id)));
                      } else {
                        setSelected(new Set());
                      }
                    }}
                  />
                </th>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Price</th>
                <th className="px-4 py-3">Stock</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className={`px-4 py-8 ${muted}`}>
                    Loading…
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={7} className={`px-4 py-10 text-center ${muted}`}>
                    No products yet. Add your first item or generate copy with AI.
                  </td>
                </tr>
              ) : (
                products.map((p) => {
                  const primary =
                    (p.images || []).find((i) => i.is_primary) ||
                    (p.images || [])[0];
                  return (
                    <tr
                      key={p.id}
                      className={`border-t ${
                        dark ? "border-white/5 hover:bg-white/[0.02]" : "border-slate-100 hover:bg-slate-50/80"
                      }`}
                    >
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selected.has(p.id)}
                          onChange={(e) => {
                            setSelected((prev) => {
                              const next = new Set(prev);
                              if (e.target.checked) next.add(p.id);
                              else next.delete(p.id);
                              return next;
                            });
                          }}
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div
                            className={`h-11 w-11 overflow-hidden rounded-xl ${
                              dark ? "bg-white/5" : "bg-slate-100"
                            }`}
                          >
                            {primary?.url ? (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img
                                src={mediaUrl(primary.url)}
                                alt=""
                                className="h-full w-full object-cover"
                              />
                            ) : null}
                          </div>
                          <div>
                            <p className="font-medium">{p.title}</p>
                            <p className={`text-xs ${muted}`}>
                              {p.sku || "No SKU"} · {p.category || "Uncategorized"}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 capitalize">{p.product_type}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase ${
                            p.status === "published"
                              ? dark
                                ? "bg-emerald-500/20 text-emerald-200"
                                : "bg-emerald-100 text-emerald-800"
                              : dark
                                ? "bg-white/5 text-zinc-400"
                                : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {Number(p.price || 0).toFixed(2)} {p.currency || "EUR"}
                      </td>
                      <td className="px-4 py-3">
                        {p.stock_qty ?? 0} · {p.stock_status || "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          className="mr-2 text-xs font-medium text-emerald-400 hover:underline"
                          onClick={() => openEdit(p)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="text-xs text-rose-400 hover:underline"
                          onClick={() => void deleteOne(p.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {editorOpen ? (
        <div className="fixed inset-0 z-50 flex items-stretch justify-end bg-black/50 p-0 sm:p-4">
          <div
            className={`flex h-full w-full max-w-2xl flex-col overflow-hidden border shadow-2xl sm:rounded-3xl ${
              dark
                ? "border-white/10 bg-[#0c0c12] text-zinc-100"
                : "border-slate-200 bg-[#faf9f6] text-slate-900"
            }`}
          >
            <div
              className={`flex items-center gap-3 border-b px-5 py-4 ${
                dark ? "border-white/10" : "border-slate-200"
              }`}
            >
              <div className="min-w-0 flex-1">
                <p className={`text-xs uppercase tracking-wider ${muted}`}>
                  {draft.id ? "Edit product" : "New product"}
                </p>
                <h3 className="truncate text-lg font-semibold">
                  {draft.title || "Untitled"}
                </h3>
              </div>
              <button
                type="button"
                className={`rounded-xl px-3 py-2 text-sm ${
                  dark ? "bg-white/5" : "bg-white shadow-sm"
                }`}
                onClick={() => setEditorOpen(false)}
              >
                Close
              </button>
            </div>

            <div className="flex-1 space-y-5 overflow-y-auto p-5">
              <div
                className={`rounded-2xl border p-4 ${
                  dark
                    ? "border-emerald-500/20 bg-emerald-500/5"
                    : "border-emerald-200 bg-emerald-50/80"
                }`}
              >
                <p className="text-sm font-semibold">✨ Generate with AI</p>
                <p className={`mt-1 text-xs ${muted}`}>
                  Vector fills title, descriptions, SEO, category and variants
                  from a short hint.
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <input
                    value={aiHint}
                    onChange={(e) => setAiHint(e.target.value)}
                    placeholder="e.g. hiking leather boots, waterproof"
                    className={`min-w-[12rem] flex-1 rounded-xl border px-3 py-2 text-sm ${input}`}
                  />
                  <button
                    type="button"
                    disabled={aiBusy}
                    onClick={() => void runAi()}
                    className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-zinc-950 disabled:opacity-50"
                  >
                    {aiBusy ? "…" : "✨ Generate with AI"}
                  </button>
                </div>
              </div>

              <label className="block text-xs font-semibold uppercase tracking-wider">
                Product type
                <select
                  className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                  value={draft.product_type || "physical"}
                  onChange={(e) =>
                    setDraft({ ...draft, product_type: e.target.value })
                  }
                >
                  {PRODUCT_TYPES.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.label}
                      {!t.active ? " · schema ready" : ""}
                    </option>
                  ))}
                </select>
                {(draft.product_type || "physical") !== "physical" ? (
                  <p className={`mt-1 text-[11px] ${muted}`}>
                    Type saved for future modules. R3.1.2 editing UI is optimized
                    for Physical Product.
                  </p>
                ) : null}
              </label>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="block text-xs font-semibold uppercase tracking-wider sm:col-span-2">
                  Title
                  <input
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.title || ""}
                    onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider sm:col-span-2">
                  Short description
                  <input
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.short_description || ""}
                    onChange={(e) =>
                      setDraft({ ...draft, short_description: e.target.value })
                    }
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider sm:col-span-2">
                  Full description
                  <textarea
                    rows={4}
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.description || ""}
                    onChange={(e) =>
                      setDraft({ ...draft, description: e.target.value })
                    }
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider">
                  Price
                  <input
                    type="number"
                    step="0.01"
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.price ?? 0}
                    onChange={(e) =>
                      setDraft({ ...draft, price: Number(e.target.value) })
                    }
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider">
                  Compare-at price
                  <input
                    type="number"
                    step="0.01"
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.compare_at_price ?? ""}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        compare_at_price:
                          e.target.value === "" ? null : Number(e.target.value),
                      })
                    }
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider">
                  SKU
                  <input
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.sku || ""}
                    onChange={(e) => setDraft({ ...draft, sku: e.target.value })}
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider">
                  Stock qty
                  <input
                    type="number"
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.stock_qty ?? 0}
                    onChange={(e) =>
                      setDraft({ ...draft, stock_qty: Number(e.target.value) })
                    }
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider">
                  Stock status
                  <select
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.stock_status || "in_stock"}
                    onChange={(e) =>
                      setDraft({ ...draft, stock_status: e.target.value })
                    }
                  >
                    <option value="in_stock">In stock</option>
                    <option value="low_stock">Low stock</option>
                    <option value="out_of_stock">Out of stock</option>
                    <option value="preorder">Preorder</option>
                    <option value="made_to_order">Made to order</option>
                  </select>
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider">
                  Status
                  <select
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.status || "draft"}
                    onChange={(e) =>
                      setDraft({ ...draft, status: e.target.value })
                    }
                  >
                    <option value="draft">Draft</option>
                    <option value="published">Published</option>
                  </select>
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider">
                  Category
                  <input
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.category || ""}
                    onChange={(e) =>
                      setDraft({ ...draft, category: e.target.value })
                    }
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider">
                  Subcategory
                  <input
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.subcategory || ""}
                    onChange={(e) =>
                      setDraft({ ...draft, subcategory: e.target.value })
                    }
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider sm:col-span-2">
                  Brand
                  <input
                    className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm font-normal normal-case tracking-normal ${input}`}
                    value={draft.brand || ""}
                    onChange={(e) => setDraft({ ...draft, brand: e.target.value })}
                  />
                </label>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider">
                  Variants
                </p>
                <div className="mt-2 grid gap-3 sm:grid-cols-2">
                  {(
                    [
                      ["size", "Size (comma-separated)"],
                      ["color", "Color"],
                      ["material", "Material"],
                    ] as const
                  ).map(([key, label]) => (
                    <label key={key} className={`block text-xs ${muted}`}>
                      {label}
                      <input
                        className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm text-inherit ${input}`}
                        value={listToCsv(draft.variants?.[key] as string[])}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            variants: {
                              ...draft.variants,
                              [key]: csvToList(e.target.value),
                            },
                          })
                        }
                      />
                    </label>
                  ))}
                  <label className={`block text-xs ${muted}`}>
                    Weight
                    <input
                      className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm text-inherit ${input}`}
                      value={String(draft.variants?.weight || "")}
                      onChange={(e) =>
                        setDraft({
                          ...draft,
                          variants: {
                            ...draft.variants,
                            weight: e.target.value,
                          },
                        })
                      }
                    />
                  </label>
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider">
                  SEO
                </p>
                <div className="mt-2 space-y-3">
                  <input
                    placeholder="SEO title"
                    className={`w-full rounded-xl border px-3 py-2 text-sm ${input}`}
                    value={draft.seo?.title || ""}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        seo: { ...draft.seo, title: e.target.value },
                      })
                    }
                  />
                  <textarea
                    placeholder="SEO description"
                    rows={2}
                    className={`w-full rounded-xl border px-3 py-2 text-sm ${input}`}
                    value={draft.seo?.description || ""}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        seo: { ...draft.seo, description: e.target.value },
                      })
                    }
                  />
                  <input
                    placeholder="URL slug"
                    className={`w-full rounded-xl border px-3 py-2 text-sm ${input}`}
                    value={draft.seo?.slug || ""}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        seo: { ...draft.seo, slug: e.target.value },
                      })
                    }
                  />
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider">
                  Media
                </p>
                <p className={`mt-1 text-xs ${muted}`}>
                  Multi-upload · drag to reorder · set primary · auto-optimize
                  (WebP when Pillow is available). Save product before first
                  upload.
                </p>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  className="mt-3 block w-full text-sm"
                  onChange={(e) => void uploadImages(e.target.files)}
                />
                <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-4">
                  {[...(draft.images || [])]
                    .sort((a, b) => (a.sort || 0) - (b.sort || 0))
                    .map((img) => (
                      <div
                        key={img.id}
                        draggable
                        onDragStart={() => setDragId(img.id)}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={() => void onDropImage(img.id)}
                        className={`relative overflow-hidden rounded-xl border ${
                          img.is_primary
                            ? "border-emerald-400 ring-2 ring-emerald-400/40"
                            : dark
                              ? "border-white/10"
                              : "border-slate-200"
                        }`}
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={mediaUrl(img.url)}
                          alt=""
                          className="aspect-square w-full object-cover"
                        />
                        <div className="absolute inset-x-0 bottom-0 flex gap-1 bg-black/55 p-1 text-[10px] text-white">
                          <button
                            type="button"
                            className="flex-1 rounded bg-white/10 px-1 py-0.5"
                            onClick={() => void setPrimary(img.id)}
                          >
                            {img.is_primary ? "Primary" : "Make primary"}
                          </button>
                          <button
                            type="button"
                            className="rounded bg-rose-500/80 px-1 py-0.5"
                            onClick={() => void removeImage(img.id)}
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>

            <div
              className={`flex flex-wrap gap-2 border-t px-5 py-4 ${
                dark ? "border-white/10" : "border-slate-200"
              }`}
            >
              <button
                type="button"
                disabled={saving}
                onClick={() => void saveProduct()}
                className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-zinc-950 disabled:opacity-50"
              >
                {saving ? "Saving…" : draft.id ? "Save changes" : "Create product"}
              </button>
              {draft.id ? (
                <button
                  type="button"
                  className="rounded-xl px-4 py-2.5 text-sm text-rose-400"
                  onClick={() => void deleteOne(draft.id!)}
                >
                  Delete
                </button>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
