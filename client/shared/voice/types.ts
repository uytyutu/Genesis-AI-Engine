/** Voice input architecture — STT integration in Stage 1b+. */

export type VoiceInputState =
  | "idle"
  | "listening"
  | "processing"
  | "error";

export type VoiceTranscript = {
  text: string;
  locale?: string;
  confidence?: number;
  durationMs?: number;
};

export type VoiceInputConfig = {
  /** Browser Web Speech API or future Tauri native STT */
  provider: "web-speech" | "native" | "cloud";
  locale: string;
  continuous: boolean;
};

export const DEFAULT_VOICE_CONFIG: VoiceInputConfig = {
  provider: "web-speech",
  locale: "ru-RU",
  continuous: false,
};
