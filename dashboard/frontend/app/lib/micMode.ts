/** Mic mode — voice chat vs speech-to-text dictation (no LLM). */

export const MIC_MODE_KEY = "virtus_mic_mode";

export type MicMode = "chat" | "dictation";

export const DEFAULT_MIC_MODE: MicMode = "chat";

export function loadMicMode(): MicMode {
  if (typeof window === "undefined") return DEFAULT_MIC_MODE;
  try {
    const raw = localStorage.getItem(MIC_MODE_KEY);
    if (raw === "chat" || raw === "dictation") return raw;
  } catch {
    /* private mode */
  }
  return DEFAULT_MIC_MODE;
}

export function saveMicMode(mode: MicMode): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(MIC_MODE_KEY, mode);
  } catch {
    /* private mode */
  }
}

/** Append recognized speech to the composer field. */
export function appendDictationText(previous: string, segment: string): string {
  const chunk = segment.trim();
  if (!chunk) return previous;
  const base = previous.trimEnd();
  if (!base) return chunk;
  const last = base.slice(-1);
  if (last === "\n" || last === " ") return `${base}${chunk}`;
  if (/[.!?…]$/.test(last)) return `${base}\n${chunk}`;
  return `${base} ${chunk}`;
}
