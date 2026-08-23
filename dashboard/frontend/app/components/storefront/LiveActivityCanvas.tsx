"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const TOAST_KEYS = [
  "appStore.live.toasts.lead",
  "appStore.live.toasts.replied",
  "appStore.live.toasts.booking",
  "appStore.live.toasts.published",
  "appStore.live.toasts.order",
] as const;

type Toast = { id: number; key: (typeof TOAST_KEYS)[number]; x: number; y: number };

export function LiveActivityCanvas() {
  const { t } = useTranslation("site");
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    let n = 0;
    const tick = () => {
      n += 1;
      const key = TOAST_KEYS[n % TOAST_KEYS.length];
      const toast: Toast = {
        id: n,
        key,
        x: 8 + (n * 17) % 72,
        y: 12 + (n * 23) % 58,
      };
      setToasts((prev) => [...prev.slice(-4), toast]);
    };
    tick();
    const id = window.setInterval(tick, 3200);
    return () => window.clearInterval(id);
  }, []);

  return (
    <div
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-hidden
    >
      <div className="storefront-orb storefront-orb-a max-sm:opacity-40" />
      <div className="storefront-orb storefront-orb-b max-sm:opacity-35" />
      <div className="storefront-orb storefront-orb-c max-sm:opacity-25" />
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="storefront-toast absolute max-w-[13rem] rounded-2xl border border-genesis-purple/35 bg-black/55 px-3 py-2 text-left text-[11px] text-white/90 shadow-glow backdrop-blur-md max-sm:hidden sm:max-w-[14rem]"
          style={{ left: `${toast.x}%`, top: `${toast.y}%` }}
        >
          {t(toast.key, { defaultValue: "…" })}
        </div>
      ))}
    </div>
  );
}
