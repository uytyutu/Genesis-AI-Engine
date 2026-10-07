"use client";

import { useState } from "react";
import { useI18n } from "@/components/I18nProvider";
import type { RoleId } from "@/lib/games/definitions";

export function RoleCard({ role }: { role: RoleId | null | undefined }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);

  if (!role) return null;

  return (
    <button
      type="button"
      onClick={() => setOpen((v) => !v)}
      className="relative mx-auto block w-full max-w-xs perspective-[800px]"
      aria-expanded={open}
    >
      <div
        className={`relative h-48 w-full transition-transform duration-500 [transform-style:preserve-3d] ${
          open ? "[transform:rotateY(180deg)]" : ""
        }`}
      >
        <div className="anon-card absolute inset-0 flex flex-col items-center justify-center gap-2 [backface-visibility:hidden]">
          <p className="text-xs uppercase tracking-[0.3em] text-violet-300">
            {t("role.your")}
          </p>
          <p className="text-4xl font-bold">???</p>
          <p className="text-sm anon-muted">{t("role.tap")}</p>
        </div>
        <div className="anon-card absolute inset-0 flex flex-col items-center justify-center gap-2 border-violet-400/40 bg-violet-950/50 px-4 [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <p className="text-xs uppercase tracking-[0.3em] text-violet-200">
            {t("role.youAre")}
          </p>
          <p className="text-2xl font-bold">{t(`role.${role}`)}</p>
          <p className="text-center text-sm text-white/70">{t(`role.${role}.desc`)}</p>
          <p className="text-xs anon-muted">{t("role.hide")}</p>
        </div>
      </div>
    </button>
  );
}
