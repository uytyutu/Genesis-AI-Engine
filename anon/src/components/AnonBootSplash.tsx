"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AnonCharacter } from "./AnonCharacter";
import { useI18n } from "./I18nProvider";
// Veil boot: brand character = face of curiosity

const KEY = "anon_boot_seen_v1";

export function AnonBootSplash() {
  const { t } = useI18n();
  const pathname = usePathname() || "/";
  const skip =
    pathname.startsWith("/admin") ||
    pathname.startsWith("/auth") ||
    pathname.startsWith("/open/") ||
    pathname.startsWith("/engage/");
  const [phase, setPhase] = useState<"show" | "out" | "done">(skip ? "done" : "show");

  useEffect(() => {
    if (skip) {
      setPhase("done");
      return;
    }
    try {
      if (sessionStorage.getItem(KEY) === "1") {
        setPhase("done");
        return;
      }
    } catch {
      /* private mode */
    }

    const out = window.setTimeout(() => setPhase("out"), 1600);
    const done = window.setTimeout(() => {
      try {
        sessionStorage.setItem(KEY, "1");
      } catch {
        /* ignore */
      }
      setPhase("done");
    }, 2100);

    return () => {
      window.clearTimeout(out);
      window.clearTimeout(done);
    };
  }, [skip]);

  if (phase === "done") return null;

  return (
    <div
      className={`anon-boot fixed inset-0 z-[80] flex flex-col items-center justify-center ${
        phase === "out" ? "anon-boot-out" : ""
      }`}
      aria-hidden={phase !== "show"}
    >
      <div className="anon-boot-orbit" />
      <AnonCharacter size={148} mood="secret" accent="secret" pulse />
      <p className="anon-boot-wordmark mt-5 text-3xl font-bold tracking-[0.35em]">ANON</p>
      <p className="anon-boot-tag mt-3 max-w-xs px-6 text-center text-sm text-white/70">
        {t("boot.tag")}
      </p>
      <p className="anon-boot-char mt-2 text-xs tracking-[0.25em] text-violet-300/80">
        {t("boot.line")}
      </p>
    </div>
  );
}
