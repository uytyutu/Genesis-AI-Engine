"use client";

import { useEffect, useState } from "react";

/** Client countdown derived from server phaseEndsAt + serverNow skew. */
export function PhaseTimer({
  phaseEndsAt,
  serverNow,
}: {
  phaseEndsAt: string | null;
  serverNow: string;
}) {
  const [left, setLeft] = useState(0);

  useEffect(() => {
    if (!phaseEndsAt) {
      setLeft(0);
      return;
    }
    const skew = Date.now() - Date.parse(serverNow);
    const tick = () => {
      const ms = Date.parse(phaseEndsAt) - (Date.now() - skew);
      setLeft(Math.max(0, Math.ceil(ms / 1000)));
    };
    tick();
    const id = setInterval(tick, 250);
    return () => clearInterval(id);
  }, [phaseEndsAt, serverNow]);

  if (!phaseEndsAt) return null;

  const urgent = left <= 5;
  return (
    <div
      className={`inline-flex min-w-[4.5rem] items-center justify-center rounded-2xl px-3 py-2 font-mono text-lg font-bold tabular-nums ${
        urgent
          ? "bg-rose-500/20 text-rose-200 ring-1 ring-rose-400/40"
          : "bg-white/10 text-white"
      }`}
      aria-live="polite"
    >
      {String(Math.floor(left / 60)).padStart(2, "0")}:
      {String(left % 60).padStart(2, "0")}
    </div>
  );
}
