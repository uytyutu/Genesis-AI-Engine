"use client";

import { useTranslation } from "react-i18next";
import { PackagePreviewCarousel } from "./PackagePreviewCarousel";
import { parseClientServices } from "../lib/packagePreviewGallery";

export type OrderProjectType = "website" | "shop" | "ai" | "other";

type Props = {
  projectType: OrderProjectType;
  packageId: string;
  niche?: string | null;
  serviceList?: string;
  className?: string;
};

function AiEmployeePreview({ className = "" }: { className?: string }) {
  const { t } = useTranslation("site");
  return (
    <div className={`mt-4 ${className}`} data-order-preview="ai">
      <p className="mb-2 text-sm font-semibold text-white/95">
        {t("order.previewAiTitle")}
      </p>
      <p className="mb-3 text-[11px] text-genesis-muted">{t("order.previewAiHint")}</p>
      <div className="overflow-hidden rounded-2xl border border-emerald-400/30 bg-[#0a0f18] shadow-[0_0_40px_-16px_rgba(16,185,129,0.5)]">
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
          <div>
            <p className="text-sm font-semibold text-white">Virtus AI</p>
            <p className="text-[11px] text-emerald-300/90">● {t("order.previewAiOnline")}</p>
          </div>
          <span className="rounded-full border border-white/15 px-2 py-0.5 text-[10px] text-zinc-400">
            {t("order.previewAiDemo")}
          </span>
        </div>
        <div className="space-y-3 px-4 py-4 text-sm">
          <div className="max-w-[90%] rounded-2xl rounded-tl-md border border-white/10 bg-white/[0.06] px-3 py-2 text-zinc-100">
            {t("order.previewAiHello")}
          </div>
          <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-md bg-emerald-500/20 px-3 py-2 text-emerald-50">
            {t("order.previewAiUser")}
          </div>
          <div className="max-w-[92%] rounded-2xl rounded-tl-md border border-white/10 bg-white/[0.06] px-3 py-2 text-zinc-100">
            {t("order.previewAiReply")}
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {[t("order.previewAiChipWebsite"), t("order.previewAiChipStore"), t("order.previewAiChipPrice")].map(
              (chip) => (
                <span
                  key={chip}
                  className="rounded-full border border-white/15 bg-black/40 px-2.5 py-1 text-[11px] text-zinc-300"
                >
                  {chip}
                </span>
              ),
            )}
          </div>
        </div>
        <div className="border-t border-white/10 px-3 py-3">
          <div className="flex items-center gap-2 rounded-xl border border-white/15 bg-black/40 px-3 py-2 text-xs text-zinc-500">
            <span className="flex-1">{t("order.previewAiInput")}</span>
            <span className="rounded-lg bg-emerald-500 px-2 py-1 font-semibold text-black">➤</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function StorePreviewShell({
  packageId,
  niche,
  serviceList,
  className = "",
}: {
  packageId: string;
  niche?: string | null;
  serviceList?: string;
  className?: string;
}) {
  const { t } = useTranslation("site");
  return (
    <div className={className} data-order-preview="store">
      <p className="mb-1 text-sm font-semibold text-white/95">{t("order.previewStoreTitle")}</p>
      <p className="mb-3 text-[11px] text-genesis-muted">{t("order.previewStoreHint")}</p>
      <div className="mb-3 overflow-hidden rounded-2xl border border-sky-400/25 bg-[#080c14]">
        <div className="flex items-center justify-between border-b border-white/10 px-3 py-2 text-[11px] text-zinc-300">
          <span className="font-semibold text-white">AI Store</span>
          <span>{t("order.previewStoreCart")} · 🛒 3</span>
        </div>
        <div className="grid grid-cols-3 gap-2 p-3">
          {[
            { n: "€39", l: t("order.previewStoreProduct1") },
            { n: "€59", l: t("order.previewStoreProduct2") },
            { n: "€89", l: t("order.previewStoreProduct3") },
          ].map((p) => (
            <div
              key={p.n}
              className="rounded-xl border border-white/10 bg-white/[0.04] px-2 py-3 text-center"
            >
              <div className="mx-auto mb-2 h-10 w-full rounded-lg bg-gradient-to-br from-sky-500/30 to-violet-500/20" />
              <p className="truncate text-[10px] text-zinc-300">{p.l}</p>
              <p className="mt-0.5 text-xs font-semibold text-white">{p.n}</p>
            </div>
          ))}
        </div>
        <div className="border-t border-white/10 px-3 py-2 text-center text-[11px] font-medium text-sky-100">
          {t("order.previewStoreCta")}
        </div>
      </div>
      <PackagePreviewCarousel
        packageId={packageId}
        niche={niche}
        kind="store"
        services={parseClientServices(serviceList)}
      />
    </div>
  );
}

function OtherPreview({ className = "" }: { className?: string }) {
  const { t } = useTranslation("site");
  return (
    <div
      className={`mt-4 rounded-2xl border border-violet-400/30 bg-gradient-to-br from-violet-950/40 to-[#0a0a12] p-4 ${className}`}
      data-order-preview="other"
    >
      <p className="text-sm font-semibold text-white">{t("order.previewOtherTitle")}</p>
      <p className="mt-2 text-xs leading-relaxed text-zinc-300">{t("order.previewOtherHint")}</p>
      <ul className="mt-3 space-y-1.5 text-xs text-zinc-400">
        <li>• {t("order.previewOtherBullet1")}</li>
        <li>• {t("order.previewOtherBullet2")}</li>
        <li>• {t("order.previewOtherBullet3")}</li>
      </ul>
    </div>
  );
}

/** Dynamic order preview — switches immediately with projectType. */
export function OrderProjectPreview({
  projectType,
  packageId,
  niche,
  serviceList,
  className = "",
}: Props) {
  const { t } = useTranslation("site");

  if (projectType === "ai") {
    return <AiEmployeePreview className={className} />;
  }
  if (projectType === "other") {
    return <OtherPreview className={className} />;
  }
  if (projectType === "shop") {
    return (
      <StorePreviewShell
        packageId={packageId}
        niche={niche}
        serviceList={serviceList}
        className={className}
      />
    );
  }
  return (
    <div className={className} data-order-preview="website">
      <p className="mb-1 text-sm font-semibold text-white/95">{t("order.previewWebsiteTitle")}</p>
      <p className="mb-3 text-[11px] text-genesis-muted">{t("order.previewWebsiteHint")}</p>
      <PackagePreviewCarousel
        packageId={packageId}
        niche={niche}
        kind="website"
        services={parseClientServices(serviceList)}
      />
    </div>
  );
}
