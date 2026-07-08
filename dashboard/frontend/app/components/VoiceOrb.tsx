"use client";

/** ChatGPT-style pulsing orb while Genesis listens, thinks, or speaks. */
export function VoiceOrb({
  mode,
}: {
  mode: "listening" | "thinking" | "speaking" | "idle";
}) {
  const active = mode !== "idle";
  return (
    <div className="flex flex-col items-center gap-3 py-2" aria-hidden>
      <div
        className={`relative flex h-20 w-20 items-center justify-center rounded-full ${
          active ? "animate-genesis-voice-orb" : ""
        }`}
      >
        <span
          className={`absolute inset-0 rounded-full border-2 ${
            mode === "thinking"
              ? "border-indigo-400/50 bg-indigo-500/10"
              : mode === "speaking"
                ? "border-emerald-400/50 bg-emerald-500/10"
                : "border-genesis-accent/40 bg-genesis-accent/10"
          } ${active ? "animate-ping opacity-30" : "opacity-20"}`}
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
      </div>
      <p className="text-center text-xs text-genesis-muted">
        {mode === "listening" && "Слушаю…"}
        {mode === "thinking" && "Думаю…"}
        {mode === "speaking" && "Говорю…"}
        {mode === "idle" && ""}
      </p>
    </div>
  );
}
