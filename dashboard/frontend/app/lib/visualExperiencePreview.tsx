"use client";

import { publicApiBase } from "../lib/publicApiBase";

export type VxpPreview = {
  ok: boolean;
  mode: string;
  tier: string;
  niche_id?: string | null;
  product_id?: string | null;
  specialization_id?: string | null;
  label?: string | null;
  preview_url?: string | null;
  reason?: string | null;
};

export async function fetchVisualExperiencePreview(opts: {
  niche?: string;
  specialization?: string;
  tier: string;
}): Promise<VxpPreview | null> {
  const api = publicApiBase();
  const qs = new URLSearchParams();
  if (opts.niche) qs.set("niche", opts.niche);
  if (opts.specialization) qs.set("specialization", opts.specialization);
  qs.set("tier", opts.tier);
  try {
    const res = await fetch(`${api}/api/public/visual-experience?${qs}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as VxpPreview;
  } catch {
    return null;
  }
}

type Props = {
  preview: VxpPreview | null;
  loading?: boolean;
  onUpgrade?: () => void;
  upgradeLabel?: string;
};

const MODE_LABEL: Record<string, string> = {
  none: "Basic · Standard-Website",
  preview: "Business · Premium Preview",
  css_motion: "Motion",
  interactive_3d: "Premium · Visual Experience",
};

export function VisualExperienceCard({
  preview,
  loading,
  onUpgrade,
  upgradeLabel = "Upgrade to Premium",
}: Props) {
  if (loading) {
    return (
      <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs text-genesis-muted">
        Visual Experience wird geladen…
      </div>
    );
  }
  if (!preview) return null;

  const mode = preview.mode || "none";
  const src = preview.preview_url || null;

  return (
    <div className="mt-4 overflow-hidden rounded-xl border border-white/10 bg-white/[0.03]">
      {src && mode !== "none" ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt={preview.label || "Visual Experience"}
          className="aspect-[16/10] w-full object-cover"
        />
      ) : (
        <div className="flex aspect-[16/10] items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950/50 px-4 text-center">
          <div>
            <p className="text-sm font-medium text-white/90">
              {mode === "css_motion"
                ? "Stilvolle Motion — passend zur Branche"
                : "Website-Vorschau"}
            </p>
            <p className="mt-1 text-[11px] text-genesis-muted">
              Beispiele erscheinen in der Paket-Galerie
            </p>
          </div>
        </div>
      )}
      <div className="space-y-1.5 p-3">
        <p className="text-xs font-medium text-white">
          {MODE_LABEL[mode] || mode}
        </p>
        {preview.label ? (
          <p className="text-[11px] text-genesis-muted line-clamp-2">{preview.label}</p>
        ) : null}
        {preview.product_id ? (
          <p className="text-[10px] text-genesis-muted">
            {preview.niche_id}/{preview.product_id}
          </p>
        ) : null}
        {mode === "preview" && onUpgrade ? (
          <button
            type="button"
            onClick={onUpgrade}
            className="mt-1 w-full rounded-lg border border-emerald-500/40 bg-emerald-950/40 px-2 py-1.5 text-xs font-medium text-emerald-100 hover:bg-emerald-900/50"
          >
            {upgradeLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}
