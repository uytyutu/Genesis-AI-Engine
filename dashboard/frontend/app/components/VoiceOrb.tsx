"use client";

import { motion, useReducedMotion } from "framer-motion";
import { springs } from "../lib/motion";

/** ChatGPT-style pulsing orb while Genesis listens, thinks, or speaks. */
export function VoiceOrb({
  mode,
}: {
  mode: "listening" | "thinking" | "speaking" | "idle";
}) {
  const active = mode !== "idle";
  const reduce = useReducedMotion();

  return (
    <div className="flex flex-col items-center gap-3 py-2" aria-hidden>
      <motion.div
        className="relative flex h-20 w-20 items-center justify-center rounded-full"
        animate={
          active && !reduce
            ? { scale: [1, 1.06, 1] }
            : { scale: 1 }
        }
        transition={
          active && !reduce
            ? { duration: 1.6, repeat: Infinity, ease: "easeInOut" }
            : springs.soft
        }
      >
        <motion.span
          className={`absolute inset-0 rounded-full border-2 ${
            mode === "thinking"
              ? "border-indigo-400/50 bg-indigo-500/10"
              : mode === "speaking"
                ? "border-emerald-400/50 bg-emerald-500/10"
                : "border-genesis-accent/40 bg-genesis-accent/10"
          }`}
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
        <span
          className={`relative h-14 w-14 rounded-full ${
            mode === "thinking"
              ? "bg-gradient-to-br from-indigo-400/30 to-purple-600/40"
              : mode === "speaking"
                ? "bg-gradient-to-br from-emerald-400/35 to-teal-600/45"
                : "bg-gradient-to-br from-genesis-accent/40 to-indigo-600/50"
          } shadow-glow`}
        />
      </motion.div>
      <p className="text-center text-xs text-genesis-muted">
        {mode === "listening" && "Слушаю…"}
        {mode === "thinking" && "Думаю…"}
        {mode === "speaking" && "Говорю…"}
        {mode === "idle" && ""}
      </p>
    </div>
  );
}
