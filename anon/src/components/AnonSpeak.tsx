"use client";

import Link from "next/link";
import { AnonCharacter, type VeilAccent, type VeilMood } from "./AnonCharacter";
import { useI18n } from "./I18nProvider";

export function AnonSpeak({
  lineKey,
  mood = "curious",
  accent = "secret",
  ctaHref,
  ctaKey,
  size = 72,
  align = "left",
}: {
  lineKey: string;
  mood?: VeilMood;
  accent?: VeilAccent;
  ctaHref?: string;
  ctaKey?: string;
  size?: number;
  align?: "left" | "center";
}) {
  const { t } = useI18n();
  return (
    <div
      className={`flex gap-3 ${align === "center" ? "flex-col items-center text-center" : "items-start"}`}
    >
      <AnonCharacter size={size} mood={mood} accent={accent} pulse={mood === "secret"} />
      <div className={align === "center" ? "" : "flex-1 pt-1"}>
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-violet-300/80">
          Veil
        </p>
        <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-white/90">
          {t(lineKey)}
        </p>
        {ctaHref && ctaKey ? (
          <Link href={ctaHref} className="anon-btn anon-btn-primary mt-3 !px-4 !py-2 text-xs">
            {t(ctaKey)}
          </Link>
        ) : null}
      </div>
    </div>
  );
}
