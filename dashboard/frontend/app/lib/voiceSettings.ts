/** Genesis Voice v2 — persisted user preferences. */

export const VOICE_SETTINGS_KEY = "genesis_voice_settings_v2";
export const VOICE_BUILD = "voice-v2";

export type VoiceSettings = {
  /** "auto" | "cloud" | browser voice URI/name */
  voice: string;
  speed: number;
  pitch: number;
  volume: number;
  autoListen: boolean;
  pushToTalk: boolean;
  interruptSpeaking: boolean;
};

export const DEFAULT_VOICE_SETTINGS: VoiceSettings = {
  voice: "auto",
  speed: 1.1,
  pitch: 1.0,
  volume: 1.0,
  autoListen: true,
  pushToTalk: false,
  interruptSpeaking: true,
};

export function loadVoiceSettings(): VoiceSettings {
  if (typeof window === "undefined") return { ...DEFAULT_VOICE_SETTINGS };
  try {
    const raw = localStorage.getItem(VOICE_SETTINGS_KEY);
    if (!raw) return { ...DEFAULT_VOICE_SETTINGS };
    const parsed = JSON.parse(raw) as Partial<VoiceSettings>;
    return {
      ...DEFAULT_VOICE_SETTINGS,
      ...parsed,
      speed: clamp(parsed.speed ?? DEFAULT_VOICE_SETTINGS.speed, 0.85, 1.25),
      pitch: clamp(parsed.pitch ?? DEFAULT_VOICE_SETTINGS.pitch, 0.8, 1.2),
      volume: clamp(parsed.volume ?? DEFAULT_VOICE_SETTINGS.volume, 0.2, 1),
    };
  } catch {
    return { ...DEFAULT_VOICE_SETTINGS };
  }
}

export function saveVoiceSettings(settings: VoiceSettings): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(VOICE_SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    /* private mode */
  }
}

function clamp(n: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, n));
}
