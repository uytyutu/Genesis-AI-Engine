"use client";

import { motion, useReducedMotion } from "framer-motion";
import { springs } from "../lib/motion";

type OrbMode = "listening" | "recognizing" | "thinking" | "responding" | "speaking" | "idle";

const MODE_LABEL: Record<OrbMode, string> = {
  listening: "Слушаю…",
  recognizing: "Распознаю…",
  thinking: "Думаю…",
  responding: "Отвечаю…",
  speaking: "Говорю…",
  idle: "",
};

/** Pulsing orb while Vector listens, recognizes, thinks, or responds. */
export function VoiceOrb({
  mode,
  compact = false,
}: {
  mode: OrbMode;
  compact?: boolean;
}) {
  const active = mode !== "idle";
  const reduce = useReducedMotion();
  const size = compact ? "h-12 w-12" : "h-20 w-20";
  const inner = compact ? "h-8 w-8" : "h-14 w-14";

  const borderClass =
    mode === "thinking"
      ? "border-indigo-400/50 bg-indigo-500/10"
      : mode === "responding" || mode === "speaking"
        ? "border-emerald-400/50 bg-emerald-500/10"
        : mode === "recognizing"
          ? "border-amber-400/50 bg-amber-500/10"
          : "border-genesis-accent/40 bg-genesis-accent/10";

  const fillClass =
    mode === "thinking"
      ? "bg-gradient-to-br from-indigo-400/30 to-purple-600/40"
      : mode === "responding" || mode === "speaking"
        ? "bg-gradient-to-br from-emerald-400/35 to-teal-600/45"
        : mode === "recognizing"
          ? "bg-gradient-to-br from-amber-400/35 to-orange-600/45"
          : "bg-gradient-to-br from-genesis-accent/40 to-indigo-600/50";

  return (
    <div className={`flex flex-col items-center gap-2 ${compact ? "py-1" : "py-2"}`} aria-hidden>
      <motion.div
        className={`relative flex ${size} items-center justify-center rounded-full`}
        animate={active && !reduce ? { scale: [1, 1.06, 1] } : { scale: 1 }}
        transition={
          active && !reduce
            ? { duration: 1.6, repeat: Infinity, ease: "easeInOut" }
            : springs.soft
        }
      >
        <motion.span
          className={`absolute inset-0 rounded-full border-2 ${borderClass}`}
          animate={
            active && !reduce
              ? { opacity: [0.15, 0.45, 0.15], scale: [1, 1.12, 1] }
              : { opacity: 0.2, scale: 1 }
          }
          transition={
            active && !reduce
              ? { duration: 1.8, repeat: Infinity, ease: "easeInOut" }
              : { duration: 0.2 }
          }
        />
        <span className={`relative ${inner} rounded-full ${fillClass} shadow-glow`} />
      </motion.div>
      {!compact && (
        <p className="text-center text-xs text-genesis-muted">{MODE_LABEL[mode]}</p>
      )}
    </div>
  );
}
