"use client";

import type { GuidedCommerceState } from "../lib/guidedCommerce";
import { guidedProductPreviewUrl } from "../lib/guidedProduct";
import { SpringIn } from "./motion/SpringIn";

type Props = {
  state: GuidedCommerceState;
  loading?: boolean;
  error?: string;
};

export function GuidedFactoryProductPreview({ state, loading, error }: Props) {
  const name = state.companyName.trim();
  const previewUrl = state.productId ? guidedProductPreviewUrl(state.productId) : null;
  const stageLabel = state.productStage === "owned" ? "Ваш сайт" : "Черновик";

  if (loading) {
    return (
      <div className="mt-4 flex min-h-[14rem] items-center justify-center rounded-xl border border-dashed border-white/12 bg-white/[0.02] px-4 text-center text-sm text-genesis-muted">
        {name ? `Собираем сайт для ${name}…` : "Собираем черновик…"}
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-4 rounded-xl border border-rose-500/30 bg-rose-950/20 px-4 py-3 text-sm text-rose-100">
        {error}
      </div>
    );
  }

  if (!previewUrl) {
    return (
      <div className="mt-4 flex min-h-[10rem] items-center justify-center rounded-xl border border-dashed border-white/12 bg-white/[0.02] px-4 text-center text-sm text-genesis-muted">
        Введите название компании — здесь появится черновик сайта.
      </div>
    );
  }

  return (
    <SpringIn className="mt-4 flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-white/10 bg-[#0a0d14] shadow-inner">
      <div className="border-b border-emerald-500/20 bg-emerald-950/30 px-3 py-1.5 text-center text-[9px] font-medium text-emerald-200/90">
        {stageLabel} — тот же сайт, что вы оформляете
      </div>
      <iframe
        title={name ? `Превью: ${name}` : "Превью сайта"}
        src={previewUrl}
        className="min-h-[min(52dvh,28rem)] w-full flex-1 border-0 bg-white"
        sandbox="allow-same-origin allow-scripts"
      />
    </SpringIn>
  );
}
