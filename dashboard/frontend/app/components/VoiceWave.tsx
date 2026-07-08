"use client";

export function VoiceWave({ active }: { active: boolean }) {
  return (
    <div className="flex h-16 items-center justify-center gap-1.5" aria-hidden>
      {[0, 1, 2, 3, 4, 5, 6].map((i) => (
        <span
          key={i}
          className={`w-1.5 rounded-full bg-genesis-accent ${
            active ? "animate-genesis-voice-bar" : "h-2 opacity-40"
          }`}
          style={
            active
              ? {
                  animationDelay: `${i * 0.08}s`,
                  height: `${12 + (i % 3) * 8}px`,
                }
              : undefined
          }
        />
      ))}
    </div>
  );
}
