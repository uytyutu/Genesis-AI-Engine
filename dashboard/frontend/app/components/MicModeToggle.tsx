"use client";

import { motion, useReducedMotion } from "framer-motion";
import { saveMicMode, type MicMode } from "../lib/micMode";
import { springs } from "../lib/motion";

type Props = {
  value: MicMode;
  onChange: (mode: MicMode) => void;
};

export function MicModeToggle({ value, onChange }: Props) {
  const reduce = useReducedMotion();

  return (
    <div
      className="mb-1 flex shrink-0 flex-col gap-0.5"
      role="group"
      aria-label="Microphone mode"
    >
      {(
        [
          { id: "chat" as const, label: "Chat", emoji: "🎤" },
          { id: "dictation" as const, label: "Dict", emoji: "📝" },
        ] as const
      ).map((opt) => {
        const active = value === opt.id;
        return (
          <motion.button
            key={opt.id}
            type="button"
            title={opt.id === "chat" ? "Voice chat" : "Dictation"}
            layout={!reduce}
            onClick={() => {
              saveMicMode(opt.id);
              onChange(opt.id);
            }}
            whileHover={reduce ? undefined : { scale: 1.05 }}
            whileTap={reduce ? undefined : { scale: 0.94 }}
            transition={springs.snappy}
            className={`rounded-lg border px-1.5 py-1 text-[10px] font-semibold leading-none ${
              active
                ? "border-genesis-accent/50 bg-genesis-accent/15 text-white shadow-[0_0_16px_-4px_rgba(91,141,239,0.4)]"
                : "border-white/10 text-genesis-muted hover:border-genesis-accent/30 hover:text-white"
            }`}
          >
            <span aria-hidden>{opt.emoji}</span>
          </motion.button>
        );
      })}
    </div>
  );
}
