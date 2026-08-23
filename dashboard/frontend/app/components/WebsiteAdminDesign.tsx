"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type WebsiteDesign = {
  branding: {
    site_name: string;
    tagline: string;
    logo: { id?: string; url?: string | null } | null;
    favicon: { id?: string; url?: string | null } | null;
  };
  colors: {
    primary: string;
    secondary: string;
    button: string;
    link: string;
    background: string;
    text: string;
  };
  typography: {
    font_preset: string;
    heading_scale: number;
    body_size_px: number;
  };
  motion: { simple_animations: boolean };
  font_presets?: { id: string; label: string }[];
  can_undo?: boolean;
  can_redo?: boolean;
};

type Props = {
  orderId: string;
  siteName?: string;
  onSaved?: () => void;
};

function mediaUrl(url: string | null | undefined) {
  if (!url) return "";
  const token = getClientToken();
  const abs = url.startsWith("http") ? url : `${API}${url}`;
  if (!token) return abs;
  const join = abs.includes("?") ? "&" : "?";
  return `${abs}${join}access_token=${encodeURIComponent(token)}`;
}

export function WebsiteAdminDesign({ orderId, siteName, onSaved }: Props) {
  const [design, setDesign] = useState<WebsiteDesign | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!getClientToken() || !orderId) return;
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/design`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "load_failed");
      setDesign(body.design as WebsiteDesign);
    } catch (e) {
      setError(e instanceof Error ? e.message : "load_failed");
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    if (!design) return;
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/design`,
        {
          method: "PATCH",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify(design),
        },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "save_failed");
      setDesign(body.design as WebsiteDesign);
      onSaved?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "save_failed");
    } finally {
      setSaving(false);
    }
  };

  const historyAction = async (kind: "undo" | "redo") => {
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/design/${kind}`,
        { method: "POST", headers: { ...clientAuthHeaders() } },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || `${kind}_failed`);
      setDesign(body.design as WebsiteDesign);
      onSaved?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : `${kind}_failed`);
    }
  };

  const uploadLogo = async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(
      `${API}/api/client/websites/${orderId}/admin/media?role=logo`,
      { method: "POST", headers: { ...clientAuthHeaders() }, body: fd },
    );
    const body = await res.json();
    if (!res.ok) throw new Error(formatApiDetail(body) || "upload_failed");
    const media = body.media as { id: string; url?: string };
    setDesign((d) =>
      d
        ? {
            ...d,
            branding: {
              ...d.branding,
              logo: { id: media.id, url: media.url },
            },
          }
        : d,
    );
  };

  const previewHtml = useMemo(() => {
    if (!design) return "";
    const c = design.colors;
    const name = design.branding.site_name || siteName || "Your website";
    const tag = design.branding.tagline || "Your brand";
    const logo = mediaUrl(design.branding.logo?.url);
    return `<!doctype html><html><head><meta charset="utf-8"/><style>
body{margin:0;font-family:system-ui;background:${c.background};color:${c.text}}
.hero{padding:48px 24px;background:linear-gradient(120deg,${c.primary}cc,${c.secondary});color:#fff}
h1{margin:0 0 8px;font-size:2rem}p{margin:0 0 16px;opacity:.92}
.btn{display:inline-block;background:${c.button};color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:600}
.logo{height:40px;margin-bottom:12px}
</style></head><body>
<section class="hero">
${logo ? `<img class="logo" src="${logo}" alt=""/>` : ""}
<h1>${name}</h1><p>${tag}</p>
<a class="btn" href="#">Kontakt</a>
</section>
</body></html>`;
  }, [design, siteName]);

  if (!design) {
    return <p className="text-sm text-zinc-400">{error || "Loading design…"}</p>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={!design.can_undo}
            onClick={() => void historyAction("undo")}
            className="rounded-lg border border-white/15 px-3 py-1.5 text-xs font-semibold text-zinc-200 disabled:opacity-40"
          >
            Undo
          </button>
          <button
            type="button"
            disabled={!design.can_redo}
            onClick={() => void historyAction("redo")}
            className="rounded-lg border border-white/15 px-3 py-1.5 text-xs font-semibold text-zinc-200 disabled:opacity-40"
          >
            Redo
          </button>
        </div>
        {error ? <p className="text-sm text-rose-300">{error}</p> : null}
        <label className="block text-xs text-zinc-400">
          Site name
          <input
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
            value={design.branding.site_name || ""}
            onChange={(e) =>
              setDesign({
                ...design,
                branding: { ...design.branding, site_name: e.target.value },
              })
            }
          />
        </label>
        <label className="block text-xs text-zinc-400">
          Tagline
          <input
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
            value={design.branding.tagline || ""}
            onChange={(e) =>
              setDesign({
                ...design,
                branding: { ...design.branding, tagline: e.target.value },
              })
            }
          />
        </label>
        <label className="block text-xs text-zinc-400">
          Logo
          <input
            type="file"
            accept="image/*"
            className="mt-1 block w-full text-xs text-zinc-300"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void uploadLogo(f).catch((err) => setError(String(err)));
            }}
          />
        </label>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {(
            [
              "primary",
              "secondary",
              "button",
              "link",
              "background",
              "text",
            ] as const
          ).map((key) => (
            <label key={key} className="block text-xs capitalize text-zinc-400">
              {key}
              <input
                type="color"
                className="mt-1 h-10 w-full cursor-pointer rounded border border-white/10 bg-transparent"
                value={design.colors[key] || "#000000"}
                onChange={(e) =>
                  setDesign({
                    ...design,
                    colors: { ...design.colors, [key]: e.target.value },
                  })
                }
              />
            </label>
          ))}
        </div>
        <label className="block text-xs text-zinc-400">
          Font preset
          <select
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
            value={design.typography.font_preset}
            onChange={(e) =>
              setDesign({
                ...design,
                typography: {
                  ...design.typography,
                  font_preset: e.target.value,
                },
              })
            }
          >
            {(design.font_presets || []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <input
            type="checkbox"
            checked={design.motion?.simple_animations !== false}
            onChange={(e) =>
              setDesign({
                ...design,
                motion: { simple_animations: e.target.checked },
              })
            }
          />
          Simple animations
        </label>
        <button
          type="button"
          disabled={saving}
          onClick={() => void save()}
          className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save design"}
        </button>
      </div>
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/40">
        <p className="border-b border-white/10 px-3 py-2 text-xs text-zinc-400">
          Live preview
        </p>
        <iframe
          title="Website design preview"
          className="h-[420px] w-full bg-white"
          srcDoc={previewHtml}
        />
      </div>
    </div>
  );
}
