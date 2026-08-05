"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type DesignAsset = {
  id?: string;
  url?: string | null;
  kind?: string;
  role?: string;
};

type StoreDesign = {
  branding: {
    store_name: string;
    tagline: string;
    logo: DesignAsset | null;
    favicon: DesignAsset | null;
  };
  hero: { enabled: boolean; banners: DesignAsset[] };
  colors: {
    primary: string;
    secondary: string;
    button: string;
    link: string;
    background: string;
  };
  typography: {
    font_preset: string;
    heading_scale: number;
    body_size_px: number;
  };
  homepage: Record<string, boolean>;
  can_undo?: boolean;
  can_redo?: boolean;
  font_presets?: { id: string; label: string }[];
};

type Props = {
  orderId: string;
  dark?: boolean;
  storeName?: string;
};

const SECTION_LABELS: { id: string; label: string }[] = [
  { id: "hero", label: "Hero" },
  { id: "categories", label: "Categories" },
  { id: "featured", label: "Featured" },
  { id: "new_arrivals", label: "New Arrivals" },
  { id: "bestsellers", label: "Best Sellers" },
  { id: "reviews", label: "Reviews" },
  { id: "newsletter", label: "Newsletter" },
  { id: "footer", label: "Footer" },
];

function mediaUrl(url: string | null | undefined) {
  if (!url) return "";
  const token = getClientToken();
  const abs = url.startsWith("http") ? url : `${API}${url}`;
  if (!token) return abs;
  const join = abs.includes("?") ? "&" : "?";
  return `${abs}${join}access_token=${encodeURIComponent(token)}`;
}

function buildPreviewHtml(d: StoreDesign): string {
  const c = d.colors;
  const name = d.branding.store_name || "Your shop";
  const tag = d.branding.tagline || "Your brand, your storefront.";
  const logo = mediaUrl(d.branding.logo?.url);
  const banner = mediaUrl(d.hero.banners?.[0]?.url);
  const show = d.homepage || {};
  const scale = d.typography.heading_scale || 1;
  const body = d.typography.body_size_px || 16;
  const sections = SECTION_LABELS.filter((s) => show[s.id] !== false)
    .map(
      (s) =>
        `<section class="sec"><h3>${s.label}</h3><p>Section preview</p></section>`,
    )
    .join("");

  return `<!doctype html><html><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
  :root {
    --p:${c.primary}; --s:${c.secondary}; --btn:${c.button};
    --link:${c.link}; --bg:${c.background};
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:system-ui,sans-serif;font-size:${body}px;
    background:linear-gradient(180deg,var(--bg),color-mix(in srgb,var(--s) 50%, var(--bg)));
    color:#1c1917;line-height:1.5}
  header{display:flex;align-items:center;gap:.75rem;padding:1rem 1.25rem;
    background:rgba(255,255,255,.72);backdrop-filter:blur(8px);border-bottom:1px solid rgba(0,0,0,.06)}
  header img{height:36px;width:auto}
  .brand{font-weight:700;letter-spacing:-.02em}
  .hero{min-height:220px;display:flex;align-items:flex-end;padding:2rem 1.25rem;
    background:${
      banner
        ? `linear-gradient(120deg,rgba(15,23,42,.55),rgba(15,23,42,.2)),url('${banner}') center/cover`
        : `linear-gradient(120deg,color-mix(in srgb,var(--p) 80%,#000),var(--p))`
    };color:#fff}
  .hero h1{margin:0;font-size:calc(1.9rem * ${scale});letter-spacing:-.03em}
  .hero p{margin:.4rem 0 1rem;opacity:.92;max-width:28rem}
  .btn{display:inline-block;background:var(--btn);color:#fff;padding:.65rem 1.1rem;
    border-radius:.75rem;text-decoration:none;font-weight:600;font-size:.9rem}
  main{padding:1rem 1.25rem 2rem;display:grid;gap:.85rem}
  .sec{background:rgba(255,255,255,.7);border:1px solid rgba(0,0,0,.06);
    border-radius:1rem;padding:1rem}
  .sec h3{margin:0 0 .35rem;font-size:calc(1.05rem * ${scale})}
  .sec p{margin:0;color:#57534e;font-size:.85rem}
  a{color:var(--link)}
</style></head><body>
<header>
  ${logo ? `<img src="${logo}" alt=""/>` : ""}
  <span class="brand">${escapeHtml(name)}</span>
</header>
${
  show.hero === false
    ? ""
    : `<section class="hero"><div><h1>${escapeHtml(name)}</h1>
<p>${escapeHtml(tag)}</p><a class="btn" href="#">Shop now</a></div></section>`
}
<main>${sections}</main>
</body></html>`;
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function StoreAdminDesign({ orderId, dark = true, storeName }: Props) {
  const [design, setDesign] = useState<StoreDesign | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const skipNextHistory = useRef(false);

  const card = dark
    ? "border-white/10 bg-white/[0.03]"
    : "border-slate-200 bg-white/80 shadow-sm";
  const input = dark
    ? "border-white/10 bg-black/30 text-zinc-100"
    : "border-slate-200 bg-white text-slate-900";
  const muted = dark ? "text-zinc-500" : "text-slate-500";

  const load = useCallback(async () => {
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/design`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Failed to load design");
      }
      const d = body.design as StoreDesign;
      if (!d.branding.store_name && storeName) {
        d.branding.store_name = storeName;
      }
      setDesign(d);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [orderId, storeName]);

  useEffect(() => {
    void load();
  }, [load]);

  const persist = useCallback(
    async (next: StoreDesign) => {
      setSaving(true);
      try {
        const res = await fetch(
          `${API}/api/client/stores/${orderId}/admin/design`,
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              ...clientAuthHeaders(),
            },
            body: JSON.stringify({
              branding: {
                store_name: next.branding.store_name,
                tagline: next.branding.tagline,
                logo: next.branding.logo,
                favicon: next.branding.favicon,
              },
              hero: next.hero,
              colors: next.colors,
              typography: next.typography,
              homepage: next.homepage,
            }),
          },
        );
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(formatApiDetail(body.detail) || "Save failed");
        }
        setDesign(body.design as StoreDesign);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setSaving(false);
      }
    },
    [orderId],
  );

  const patchLocal = (updater: (d: StoreDesign) => StoreDesign) => {
    setDesign((prev) => {
      if (!prev) return prev;
      const next = updater(prev);
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => {
        if (!skipNextHistory.current) void persist(next);
        skipNextHistory.current = false;
      }, 450);
      return next;
    });
  };

  const upload = async (kind: string, file: File | null) => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(
      `${API}/api/client/stores/${orderId}/admin/design/assets?kind=${encodeURIComponent(kind)}`,
      { method: "POST", headers: { ...clientAuthHeaders() }, body: fd },
    );
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(formatApiDetail(body.detail) || "Upload failed");
      return;
    }
    setDesign(body.design as StoreDesign);
  };

  const runAction = async (action: "undo" | "redo" | "restore-defaults") => {
    const res = await fetch(
      `${API}/api/client/stores/${orderId}/admin/design/${action}`,
      { method: "POST", headers: { ...clientAuthHeaders() } },
    );
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(formatApiDetail(body.detail) || "Action failed");
      return;
    }
    setDesign(body.design as StoreDesign);
  };

  const previewHtml = useMemo(
    () => (design ? buildPreviewHtml(design) : ""),
    [design],
  );

  if (!design) {
    return (
      <p className={muted}>{error || "Loading design…"}</p>
    );
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
      <div className="space-y-4">
        <div className={`rounded-3xl border p-5 ${card}`}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p
                className={`text-xs font-semibold uppercase tracking-[0.2em] ${
                  dark ? "text-emerald-300/70" : "text-emerald-700"
                }`}
              >
                Design
              </p>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight">
                Make the shop yours
              </h2>
              <p className={`mt-1 text-sm ${muted}`}>
                Branding, hero, colors, type and homepage sections — live preview
                on the right. Survives Factory regenerate.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={!design.can_undo}
                onClick={() => void runAction("undo")}
                className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-40 ${
                  dark ? "bg-white/5" : "bg-white shadow-sm"
                }`}
              >
                Undo
              </button>
              <button
                type="button"
                disabled={!design.can_redo}
                onClick={() => void runAction("redo")}
                className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-40 ${
                  dark ? "bg-white/5" : "bg-white shadow-sm"
                }`}
              >
                Redo
              </button>
              <button
                type="button"
                onClick={() => {
                  if (window.confirm("Restore default theme?")) {
                    void runAction("restore-defaults");
                  }
                }}
                className={`rounded-xl px-3 py-2 text-xs font-semibold ${
                  dark ? "bg-white/5" : "bg-white shadow-sm"
                }`}
              >
                Restore Default
              </button>
            </div>
          </div>
          <p className={`mt-3 text-xs ${muted}`}>
            {saving ? "Saving…" : "Auto-saved · User Data Protection active"}
          </p>
          {error ? (
            <p className="mt-2 text-sm text-rose-400" role="alert">
              {error}
            </p>
          ) : null}
        </div>

        <div className={`rounded-3xl border p-5 space-y-3 ${card}`}>
          <p className="text-xs font-semibold uppercase tracking-wider">Branding</p>
          <label className={`block text-xs ${muted}`}>
            Store name
            <input
              className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm text-inherit ${input}`}
              value={design.branding.store_name}
              onChange={(e) =>
                patchLocal((d) => ({
                  ...d,
                  branding: { ...d.branding, store_name: e.target.value },
                }))
              }
            />
          </label>
          <label className={`block text-xs ${muted}`}>
            Tagline / slogan
            <input
              className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm text-inherit ${input}`}
              value={design.branding.tagline}
              onChange={(e) =>
                patchLocal((d) => ({
                  ...d,
                  branding: { ...d.branding, tagline: e.target.value },
                }))
              }
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className={`block text-xs ${muted}`}>
              Logo
              <input
                type="file"
                accept="image/*"
                className="mt-1 block w-full text-xs"
                onChange={(e) => void upload("logo", e.target.files?.[0] || null)}
              />
            </label>
            <label className={`block text-xs ${muted}`}>
              Favicon
              <input
                type="file"
                accept="image/*"
                className="mt-1 block w-full text-xs"
                onChange={(e) =>
                  void upload("favicon", e.target.files?.[0] || null)
                }
              />
            </label>
          </div>
        </div>

        <div className={`rounded-3xl border p-5 space-y-3 ${card}`}>
          <p className="text-xs font-semibold uppercase tracking-wider">Hero banners</p>
          <p className={`text-xs ${muted}`}>
            Multi-banner slider · auto WebP/crop · desktop + mobile adaptation
          </p>
          <input
            type="file"
            accept="image/*"
            multiple
            className="block w-full text-xs"
            onChange={(e) => {
              const files = e.target.files;
              if (!files) return;
              void (async () => {
                for (const f of Array.from(files)) {
                  await upload("banner", f);
                }
              })();
            }}
          />
          <div className="flex flex-wrap gap-2">
            {(design.hero.banners || []).map((b) => (
              <div
                key={b.id}
                className="relative h-16 w-24 overflow-hidden rounded-xl border border-white/10"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={mediaUrl(b.url)}
                  alt=""
                  className="h-full w-full object-cover"
                />
              </div>
            ))}
          </div>
        </div>

        <div className={`rounded-3xl border p-5 space-y-3 ${card}`}>
          <p className="text-xs font-semibold uppercase tracking-wider">Colors</p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {(
              [
                ["primary", "Primary"],
                ["secondary", "Secondary"],
                ["button", "Buttons"],
                ["link", "Links"],
                ["background", "Background"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className={`block text-xs ${muted}`}>
                {label}
                <input
                  type="color"
                  className="mt-1 h-10 w-full cursor-pointer rounded-lg border-0 bg-transparent"
                  value={design.colors[key]}
                  onChange={(e) =>
                    patchLocal((d) => ({
                      ...d,
                      colors: { ...d.colors, [key]: e.target.value },
                    }))
                  }
                />
              </label>
            ))}
          </div>
        </div>

        <div className={`rounded-3xl border p-5 space-y-3 ${card}`}>
          <p className="text-xs font-semibold uppercase tracking-wider">
            Typography
          </p>
          <label className={`block text-xs ${muted}`}>
            Font pair
            <select
              className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm text-inherit ${input}`}
              value={design.typography.font_preset}
              onChange={(e) =>
                patchLocal((d) => ({
                  ...d,
                  typography: { ...d.typography, font_preset: e.target.value },
                }))
              }
            >
              {(design.font_presets || []).map((f) => (
                <option key={f.id} value={f.id}>
                  {f.label}
                </option>
              ))}
            </select>
          </label>
          <label className={`block text-xs ${muted}`}>
            Heading scale ({design.typography.heading_scale.toFixed(2)})
            <input
              type="range"
              min={0.85}
              max={1.35}
              step={0.05}
              className="mt-1 w-full"
              value={design.typography.heading_scale}
              onChange={(e) =>
                patchLocal((d) => ({
                  ...d,
                  typography: {
                    ...d.typography,
                    heading_scale: Number(e.target.value),
                  },
                }))
              }
            />
          </label>
          <label className={`block text-xs ${muted}`}>
            Body size ({design.typography.body_size_px}px)
            <input
              type="range"
              min={14}
              max={20}
              step={1}
              className="mt-1 w-full"
              value={design.typography.body_size_px}
              onChange={(e) =>
                patchLocal((d) => ({
                  ...d,
                  typography: {
                    ...d.typography,
                    body_size_px: Number(e.target.value),
                  },
                }))
              }
            />
          </label>
        </div>

        <div className={`rounded-3xl border p-5 space-y-3 ${card}`}>
          <p className="text-xs font-semibold uppercase tracking-wider">
            Homepage sections
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {SECTION_LABELS.map((s) => (
              <label
                key={s.id}
                className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm ${
                  dark ? "border-white/10" : "border-slate-200"
                }`}
              >
                <input
                  type="checkbox"
                  checked={design.homepage[s.id] !== false}
                  onChange={(e) =>
                    patchLocal((d) => ({
                      ...d,
                      homepage: { ...d.homepage, [s.id]: e.target.checked },
                    }))
                  }
                />
                {s.label}
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="xl:sticky xl:top-20 xl:self-start">
        <div className={`overflow-hidden rounded-3xl border ${card}`}>
          <div
            className={`flex items-center justify-between border-b px-4 py-2 text-xs ${
              dark ? "border-white/10" : "border-slate-200"
            } ${muted}`}
          >
            <span>Live preview</span>
            <span>No refresh needed</span>
          </div>
          <iframe
            title="Store design preview"
            className="h-[70vh] w-full bg-white"
            sandbox="allow-same-origin"
            srcDoc={previewHtml}
          />
        </div>
      </div>
    </div>
  );
}
