/**
 * Genesis TTS v2 — cloud providers first, browser SpeechSynthesis as fallback.
 */

import {
  DEFAULT_VOICE_SETTINGS,
  type VoiceSettings,
  VOICE_BUILD,
} from "./voiceSettings";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Best installed voices — Neural / Microsoft female RU preferred. */
const VOICE_PRIORITY: RegExp[] = [
  /Microsoft Aria Online/i,
  /Microsoft Aria/i,
  /Microsoft Katja Online/i,
  /Microsoft Katja/i,
  /Microsoft Hedda/i,
  /Microsoft Natasha/i,
  /Google.*Russian/i,
  /Google русский/i,
  /Neural/i,
  /ru-RU.*Female/i,
  /ru-RU/i,
];

let activeAudio: HTMLAudioElement | null = null;
let interruptRecognition: SpeechRecognition | null = null;
let speaking = false;
let voicesReady: Promise<SpeechSynthesisVoice[]> | null = null;

export function isSpeaking(): boolean {
  return speaking;
}

export function cleanTextForSpeech(text: string): string {
  return text
    .replace(/\*\*/g, "")
    .replace(/#{1,6}\s/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 1200);
}

function waitForVoices(): Promise<SpeechSynthesisVoice[]> {
  if (typeof window === "undefined" || !window.speechSynthesis) {
    return Promise.resolve([]);
  }
  if (voicesReady) return voicesReady;
  voicesReady = new Promise((resolve) => {
    const pick = () => {
      const list = window.speechSynthesis.getVoices();
      if (list.length) {
        resolve(list);
        return true;
      }
      return false;
    };
    if (pick()) return;
    window.speechSynthesis.onvoiceschanged = () => {
      if (pick()) window.speechSynthesis.onvoiceschanged = null;
    };
    setTimeout(() => resolve(window.speechSynthesis.getVoices()), 400);
  });
  return voicesReady;
}

export async function listBrowserVoices(): Promise<
  { name: string; lang: string; localService: boolean; voiceURI: string }[]
> {
  const voices = await waitForVoices();
  return voices
    .filter((v) => /ru|russian|katja|hedda|natasha|aria|neural/i.test(`${v.name} ${v.lang}`))
    .map((v) => ({
      name: v.name,
      lang: v.lang,
      localService: v.localService,
      voiceURI: v.voiceURI,
    }));
}

export function pickBestBrowserVoice(
  voices: SpeechSynthesisVoice[],
  preferredId?: string,
): SpeechSynthesisVoice | null {
  if (!voices.length) return null;
  if (preferredId && preferredId !== "auto" && preferredId !== "cloud") {
    const exact =
      voices.find((v) => v.voiceURI === preferredId) ??
      voices.find((v) => v.name === preferredId);
    if (exact) return exact;
  }
  for (const pattern of VOICE_PRIORITY) {
    const hit = voices.find((v) => pattern.test(v.name) || pattern.test(`${v.name} ${v.lang}`));
    if (hit) return hit;
  }
  return (
    voices.find((v) => v.lang.startsWith("ru")) ??
    voices.find((v) => /female|жен/i.test(v.name)) ??
    voices[0] ??
    null
  );
}

import {
  getSpeechRecognitionCtor,
} from "./voiceRuntime";

const INTERRUPT_RE =
  /^(стоп|подожди|подождите|не надо|хватит|стой|stop|wait|нет|тише|замолчи)[.!?,]*$/i;

export function isInterruptPhrase(text: string): boolean {
  const t = text.trim();
  if (!t) return false;
  if (INTERRUPT_RE.test(t)) return true;
  return /^(стоп|подожди|не надо|хватит|стой)\b/i.test(t) && t.length < 48;
}

/** Stop TTS immediately — cloud audio + browser speech. */
export function stopSpeaking(): void {
  if (interruptRecognition) {
    try {
      interruptRecognition.stop();
    } catch {
      /* ignore */
    }
    interruptRecognition = null;
  }
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  if (activeAudio) {
    try {
      activeAudio.pause();
      activeAudio.currentTime = 0;
    } catch {
      /* ignore */
    }
    activeAudio.src = "";
    activeAudio = null;
  }
  speaking = false;
}

/**
 * Listen for «Стоп» / «Подожди» while Genesis speaks — GPT-style interrupt.
 * Returns cleanup function.
 */
export function startInterruptListener(onInterrupt?: (phrase: string) => void): () => void {
  const SR = getSpeechRecognitionCtor();
  if (!SR || typeof window === "undefined") return () => undefined;

  stopInterruptListener();
  const rec = new SR();
  rec.lang = "ru-RU";
  rec.interimResults = true;
  rec.continuous = true;
  rec.onresult = (event: SpeechRecognitionEvent) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i]?.[0]?.transcript?.trim();
      if (!transcript || !isInterruptPhrase(transcript)) continue;
      stopSpeaking();
      onInterrupt?.(transcript);
      return;
    }
  };
  rec.onerror = () => {
    /* mic busy or denied — non-fatal */
  };
  interruptRecognition = rec;
  try {
    rec.start();
  } catch {
    interruptRecognition = null;
  }
  return stopInterruptListener;
}

export function stopInterruptListener(): void {
  if (!interruptRecognition) return;
  try {
    interruptRecognition.stop();
  } catch {
    /* ignore */
  }
  interruptRecognition = null;
}

async function fetchCloudTts(
  text: string,
  settings: VoiceSettings,
): Promise<{ blob: Blob; provider: string } | null> {
  try {
    const res = await fetch(`${API}/api/public/genesis-ai/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: cleanTextForSpeech(text),
        speed: settings.speed,
        locale: "ru-RU",
      }),
    });
    if (!res.ok) return null;
    const provider = res.headers.get("X-Genesis-TTS-Provider") ?? "cloud";
    const blob = await res.blob();
    if (!blob.size) return null;
    return { blob, provider };
  } catch {
    return null;
  }
}

function speakBrowser(
  text: string,
  settings: VoiceSettings,
  onEnd?: () => void,
  onStart?: () => void,
): void {
  if (typeof window === "undefined" || !window.speechSynthesis) {
    onEnd?.();
    return;
  }
  window.speechSynthesis.cancel();
  const clean = cleanTextForSpeech(text);
  const utter = new SpeechSynthesisUtterance(clean);
  utter.lang = "ru-RU";
  utter.rate = settings.speed;
  utter.pitch = settings.pitch;
  utter.volume = settings.volume;

  void waitForVoices().then((voices) => {
    const voice = pickBestBrowserVoice(voices, settings.voice);
    if (voice) utter.voice = voice;
    utter.onstart = () => {
      speaking = true;
      onStart?.();
    };
    utter.onend = () => {
      speaking = false;
      onEnd?.();
    };
    utter.onerror = () => {
      speaking = false;
      onEnd?.();
    };
    window.speechSynthesis.speak(utter);
  });
}

function playAudioBlob(
  blob: Blob,
  settings: VoiceSettings,
  onEnd?: () => void,
  onStart?: () => void,
): void {
  stopSpeaking();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.volume = settings.volume;
  audio.playbackRate = Math.min(1.25, Math.max(0.85, settings.speed / 1.1));
  activeAudio = audio;
  audio.onplay = () => {
    speaking = true;
    onStart?.();
  };
  audio.onended = () => {
    speaking = false;
    URL.revokeObjectURL(url);
    activeAudio = null;
    onEnd?.();
  };
  audio.onerror = () => {
    speaking = false;
    URL.revokeObjectURL(url);
    activeAudio = null;
    onEnd?.();
  };
  void audio.play().catch(() => {
    speaking = false;
    URL.revokeObjectURL(url);
    activeAudio = null;
    onEnd?.();
  });
}

export type SpeakCallbacks = {
  onStart?: () => void;
  onEnd?: () => void;
  onProvider?: (provider: string) => void;
};

/** Primary entry — cloud TTS when available, else best browser voice. */
export async function speakGenesis(
  text: string,
  settings: VoiceSettings = DEFAULT_VOICE_SETTINGS,
  callbacks?: SpeakCallbacks,
): Promise<void> {
  const clean = cleanTextForSpeech(text);
  if (!clean) {
    callbacks?.onEnd?.();
    return;
  }

  stopSpeaking();

  const useCloud = settings.voice === "auto" || settings.voice === "cloud";
  if (useCloud) {
    const cloud = await fetchCloudTts(clean, settings);
    if (cloud) {
      callbacks?.onProvider?.(cloud.provider);
      playAudioBlob(cloud.blob, settings, callbacks?.onEnd, callbacks?.onStart);
      return;
    }
  }

  callbacks?.onProvider?.("browser");
  speakBrowser(clean, settings, callbacks?.onEnd, callbacks?.onStart);
}

export async function fetchTtsStatus(): Promise<{
  cloud_available?: boolean;
  preferred_provider?: string;
  voice_build?: string;
} | null> {
  try {
    const res = await fetch(`${API}/api/public/genesis-ai/tts/status`);
    if (!res.ok) return null;
    return (await res.json()) as {
      cloud_available?: boolean;
      preferred_provider?: string;
      voice_build?: string;
    };
  } catch {
    return null;
  }
}

export { VOICE_BUILD };
