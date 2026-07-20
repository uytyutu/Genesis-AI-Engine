"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  resolvePackagePreviewSlides,
  resolvePremiumServices,
  type PackagePreviewSlide,
} from "../lib/packagePreviewGallery";

const AUTO_MS = 4500;
/** Bust phone/CDN cache of previous 404 responses for gallery.jpg */
const GALLERY_CACHE = "g5";

type Props = {
  packageId: string;
  niche?: string | null;
  /** Client-entered service lines (Premium block) */
  services?: string[] | null;
  className?: string;
};

function slideUrl(slide: PackagePreviewSlide): string {
  const path = slide.src.replace(/^\/+/, "");
  // Always a site-root public URL — never a filesystem path.
  return `/package-previews/${path}?v=${GALLERY_CACHE}`;
}

function siteDemoUrl(slide: PackagePreviewSlide): string | null {
  if (!slide.siteSrc) return null;
  const path = slide.siteSrc.replace(/^\/+/, "");
  return `/package-previews/${path}`;
}

export function PackagePreviewCarousel({
  packageId,
  niche,
  services,
  className = "",
}: Props) {
  const { t } = useTranslation("site");
  const isPremium = (packageId || "").toLowerCase() === "premium";
  const slides = useMemo(
    () => resolvePackagePreviewSlides(packageId, niche, 5),
    [packageId, niche],
  );
  const [index, setIndex] = useState(0);
  const premiumServices = useMemo(
    () =>
      isPremium
        ? resolvePremiumServices(niche || slides[0]?.niche, services)
        : [],
    [isPremium, niche, services, slides],
  );
  const clientFilled = Boolean(services && services.length > 0);
  const touchX = useRef<number | null>(null);
  const paused = useRef(false);

  useEffect(() => {
    setIndex(0);
  }, [packageId, niche, slides.length]);

  useEffect(() => {
    if (slides.length <= 1) return;
    const id = window.setInterval(() => {
      if (paused.current) return;
      setIndex((i) => (i + 1) % slides.length);
    }, AUTO_MS);
    return () => window.clearInterval(id);
  }, [slides.length, packageId]);

  const go = (next: number) => {
    if (slides.length === 0) return;
    setIndex((next + slides.length) % slides.length);
  };

  const caption = (
    <div className="mb-2 px-0.5">
      <p className="text-xs font-medium text-white/90">{t("order.previewExamplesTitle")}</p>
      <p className="mt-0.5 text-[11px] leading-snug text-genesis-muted">
        {t("order.previewExamplesHint")}
      </p>
    </div>
  );

  if (slides.length === 0) {
    return (
      <div className={`mt-4 ${className}`}>
        {caption}
        <div className="overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950/40">
          <div className="flex h-[240px] items-center justify-center px-4 text-center sm:h-[260px]">
            <div>
              <p className="text-sm font-medium text-white/90">
                {t("order.previewPlaceholderTitle")}
              </p>
              <p className="mt-1 text-[11px] text-genesis-muted">
                {t("order.previewPlaceholderHint")}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const current = slides[index]!;
  const demoHref = siteDemoUrl(current);

  return (
    <div className={`mt-4 ${className}`}>
      {caption}
      <div
        className="overflow-hidden rounded-xl border border-white/10 bg-slate-950"
        onMouseEnter={() => {
          paused.current = true;
        }}
        onMouseLeave={() => {
          paused.current = false;
        }}
        onTouchStart={(e) => {
          touchX.current = e.touches[0]?.clientX ?? null;
          paused.current = true;
        }}
        onTouchEnd={(e) => {
          const start = touchX.current;
          touchX.current = null;
          paused.current = false;
          if (start == null) return;
          const end = e.changedTouches[0]?.clientX ?? start;
          const dx = end - start;
          if (Math.abs(dx) < 40) return;
          go(dx < 0 ? index + 1 : index - 1);
        }}
      >
        <div className="relative h-[220px] w-full overflow-hidden bg-slate-900 sm:h-[280px] lg:h-[260px]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            key={current.src}
            src={slideUrl(current)}
            alt={current.alt}
            className="h-full w-full object-cover object-top"
            loading="eager"
            decoding="async"
          />
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
          <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/80 to-transparent px-3 pb-3 pt-8">
            <p className="text-[11px] font-medium text-white/95">{current.alt}</p>
          </div>
          {slides.length > 1 && (
            <>
              <button
                type="button"
                aria-label="Previous"
                className="absolute left-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-black/45 px-2 py-1 text-sm text-white hover:bg-black/65"
                onClick={() => go(index - 1)}
              >
                ‹
              </button>
              <button
                type="button"
                aria-label="Next"
                className="absolute right-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-black/45 px-2 py-1 text-sm text-white hover:bg-black/65"
                onClick={() => go(index + 1)}
              >
                ›
              </button>
            </>
          )}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2">
          {slides.length > 1 ? (
            <div className="flex items-center justify-center gap-1.5">
              {slides.map((s, i) => (
                <button
                  key={s.src}
                  type="button"
                  aria-label={`Slide ${i + 1}`}
                  className={`h-1.5 rounded-full transition ${
                    i === index ? "w-4 bg-emerald-400" : "w-1.5 bg-white/30 hover:bg-white/50"
                  }`}
                  onClick={() => go(i)}
                />
              ))}
            </div>
          ) : (
            <span />
          )}
          {demoHref ? (
            <a
              href={demoHref}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-medium text-emerald-300/90 underline-offset-2 hover:underline"
            >
              {t("order.previewOpenDemo", { defaultValue: "Open full demo" })}
            </a>
          ) : null}
        </div>
      </div>
    </div>
  );
}
