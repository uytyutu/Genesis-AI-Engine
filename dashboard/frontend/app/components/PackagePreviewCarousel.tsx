"use client";

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  normalizeOrderNicheKey,
  normalizePreviewTier,
  resolveExactOrderPreview,
  resolvePremiumServices,
  type PackagePreviewSlide,
} from "../lib/packagePreviewGallery";

/** Bust phone/CDN cache of previous 404 responses for gallery.jpg */
const GALLERY_CACHE = "g8";

type Props = {
  packageId: string;
  niche?: string | null;
  /** website | store — drives which package-previews folder is shown */
  kind?: "website" | "store";
  /** Client-entered service lines (Premium block) */
  services?: string[] | null;
  className?: string;
};

function slideUrl(slide: PackagePreviewSlide): string {
  const raw = (slide.src || "").trim();
  if (
    raw.startsWith("/vitrine/") ||
    raw.startsWith("/package-previews/") ||
    raw.startsWith("http://") ||
    raw.startsWith("https://")
  ) {
    return raw;
  }
  const path = raw.replace(/^\/+/, "");
  if (path.startsWith("package-previews/")) return `/${path}?v=${GALLERY_CACHE}`;
  return `/package-previews/${path}?v=${GALLERY_CACHE}`;
}

function siteDemoUrl(slide: PackagePreviewSlide): string | null {
  if (!slide.siteSrc) return null;
  const raw = slide.siteSrc.trim();
  if (
    raw.startsWith("/package-previews/") ||
    raw.startsWith("http://") ||
    raw.startsWith("https://")
  ) {
    return raw;
  }
  const path = raw.replace(/^\/+/, "");
  return `/package-previews/${path}`;
}

function humanNicheLabel(niche?: string | null): string {
  const key = normalizeOrderNicheKey(niche) || (niche || "").trim();
  const map: Record<string, string> = {
    beauty: "Salon",
    dental: "Zahnarzt",
    restaurant: "Restaurant",
    fashion: "Fashion",
    electronics: "Electronics",
    handwerk: "Handwerk",
    auto: "Autowerkstatt",
    law: "Rechtsanwalt",
    barbershop: "Barbershop",
    gartenpflege: "Gartenpflege",
    dachreinigung: "Dachreinigung",
    zaunbau: "Zaunbau",
    food: "Food",
    furniture: "Möbel",
    accessories: "Accessoires",
  };
  if (!key) return "Branche";
  return map[key] || key.charAt(0).toUpperCase() + key.slice(1);
}

export function PackagePreviewCarousel({
  packageId,
  niche,
  kind = "website",
  services,
  className = "",
}: Props) {
  const { t } = useTranslation("site");
  const pkg = (packageId || "").toLowerCase();
  const tier = normalizePreviewTier(packageId);
  const isPremium = tier === "premium";
  const slide = useMemo(
    () => resolveExactOrderPreview(packageId, niche, kind),
    [packageId, niche, kind],
  );
  const [iframeFailed, setIframeFailed] = useState(false);
  const premiumServices = useMemo(
    () =>
      isPremium
        ? resolvePremiumServices(niche || slide?.niche, services)
        : [],
    [isPremium, niche, services, slide?.niche],
  );
  const clientFilled = Boolean(services && services.length > 0);

  const tierLabel =
    tier === "premium" ? "Premium" : tier === "business" ? "Business" : "Basic";
  const productLabel = kind === "store" ? "Online-Shop" : "Website";
  const nicheTitle = humanNicheLabel(niche || slide?.niche);
  const title = `${tierLabel} ${nicheTitle} ${productLabel}`;
  const subtitle =
    tier === "premium"
      ? "Gleiche visuelle Qualität wie Business — mehr Steuerung und Tiefe"
      : tier === "business"
        ? "Business-Beispiel mit Workspace — Präsentationsniveau"
        : "Basic-Beispiel — klare Standard-Website für Ihre Branche";

  if (!slide) {
    return (
      <div className={`mt-4 ${className}`}>
        <div className="mb-2 px-0.5">
          <p className="text-sm font-semibold text-white/95">{title}</p>
          <p className="mt-0.5 text-[11px] text-genesis-muted">{subtitle}</p>
        </div>
        <div className="overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950/40">
          <div className="flex h-[220px] flex-col items-center justify-center gap-2 px-4 text-center sm:h-[240px]">
            <p className="text-sm font-medium text-white/90">
              {tier === "premium" ? "Premium noch nicht bereit" : "Demo folgt bald"}
            </p>
            <p className="max-w-xs text-[11px] text-genesis-muted">
              {tier === "premium"
                ? "Öffentliche Premium-Beispiele erscheinen nach Quality Gate. Basic und Business sind bereits sichtbar."
                : `Für ${tierLabel} · ${nicheTitle} · ${productLabel} ist noch kein freigegebenes Beispiel hinterlegt.`}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const demoHref = siteDemoUrl(slide);

  return (
    <div className={`mt-4 ${className}`}>
      <div className="mb-2 px-0.5">
        <p className="text-sm font-semibold text-white/95">{title}</p>
        <p className="mt-0.5 text-[11px] leading-snug text-genesis-muted">{subtitle}</p>
      </div>
      <div className="overflow-hidden rounded-xl border border-white/10 bg-slate-950">
        {demoHref && !iframeFailed ? (
          <div className="relative w-full bg-white">
            {isPremium ? (
              <div className="pointer-events-none absolute left-2 top-2 z-10 max-w-[85%] rounded-md border border-white/20 bg-black/55 px-2 py-1 backdrop-blur-sm">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-200">
                  {t("order.previewPremiumBadge")}
                </p>
                {premiumServices.length > 0 ? (
                  <ul className="mt-1 space-y-0.5">
                    {premiumServices.slice(0, 4).map((s) => (
                      <li key={s} className="text-[10px] leading-snug text-white/90">
                        · {s}
                      </li>
                    ))}
                  </ul>
                ) : null}
                {clientFilled ? null : (
                  <p className="mt-1 text-[9px] text-amber-100/80">
                    {t("order.premiumServicesHint")}
                  </p>
                )}
              </div>
            ) : null}
            <iframe
              title={slide.alt}
              src={demoHref}
              className="h-[min(70vh,520px)] w-full border-0 bg-white"
              loading="lazy"
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
              onError={() => setIframeFailed(true)}
            />
          </div>
        ) : (
          <div className="relative h-[220px] w-full overflow-hidden bg-slate-900 sm:h-[280px]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={slideUrl(slide)}
              alt={slide.alt}
              className="h-full w-full object-cover object-top"
              loading="eager"
              decoding="async"
              onError={() => setIframeFailed(true)}
            />
          </div>
        )}
        <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2">
          <span className="text-[10px] text-genesis-muted">
            {tierLabel} · {nicheTitle} · {productLabel}
            {isPremium ? " · Mehr Tiefe" : tier === "business" ? " · Workspace" : " · Standard"}
          </span>
          {demoHref ? (
            <a
              href={demoHref}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-semibold text-emerald-300/95 underline-offset-2 hover:underline"
            >
              Vollständiges Demo öffnen →
            </a>
          ) : (
            <span className="text-[11px] text-genesis-muted">Demo folgt bald</span>
          )}
        </div>
      </div>
    </div>
  );
}
