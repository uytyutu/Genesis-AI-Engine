"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { VoiceUiStatus } from "../GenesisChatComposer";

const STATUS_EMOJI: Record<VoiceUiStatus, string> = {
  ready: "⚪",
  listening: "🎤",
  recognizing: "📝",
  thinking: "🤖",
  responding: "💬",
  speaking: "🗣️",
  stopped: "⏹️",
};

type Props = {
  status: VoiceUiStatus;
  label: string;
  className?: string;
};

/** Pulsing status emoji — subtle when active, static when idle. */
export function VoiceStatusPulse({ status, label, className }: Props) {
  const reduce = useReducedMotion();
  const leading = label.match(/^\S+/)?.[0];
  const emoji = leading && /\p{Extended_Pictographic}/u.test(leading) ? leading : STATUS_EMOJI[status] ?? "⚪";
  const text = leading && emoji === leading ? label.slice(leading.length).trim() : label;
  const pulse =
    !reduce &&
    (status === "listening" ||
      status === "recognizing" ||
      status === "thinking" ||
      status === "responding" ||
      status === "speaking");

  return (
    <p className={className} aria-live="polite">
      <motion.span
        className="mr-1 inline-block"
        aria-hidden
        animate={
          pulse
            ? { scale: [1, 1.14, 1], opacity: [0.85, 1, 0.85] }
            : { scale: 1, opacity: 1 }
        }
        transition={
          pulse
            ? { duration: 1.8, repeat: Infinity, ease: "easeInOut" }
            : { duration: 0.2 }
        }
      >
        {emoji}
      </motion.span>
      {text}
    </p>
  );
}
