/** Voice pipeline diagnostics — getUserMedia + SpeechRecognition (Chrome/Edge). */

export type MicDeviceInfo = {
  deviceId: string;
  label: string;
  kind: string;
};

export async function listAudioInputDevices(): Promise<MicDeviceInfo[]> {
  if (typeof navigator === "undefined" || !navigator.mediaDevices?.enumerateDevices) {
    return [];
  }
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices
      .filter((d) => d.kind === "audioinput")
      .map((d) => ({
        deviceId: d.deviceId,
        label: d.label || "(без названия — разрешите микрофон)",
        kind: d.kind,
      }));
  } catch (err) {
    console.warn("[Genesis] enumerateDevices failed:", err);
    return [];
  }
}

export function logVoiceDiagnostics(phase: string, extra?: Record<string, unknown>) {
  console.info(`[Genesis voice] ${phase}`, extra ?? {});
}

export function isPermissionsPolicyBlock(err: unknown): boolean {
  const name =
    err && typeof err === "object" && "name" in err
      ? String((err as { name: string }).name)
      : "";
  const msg =
    err && typeof err === "object" && "message" in err
      ? String((err as { message: string }).message)
      : String(err ?? "");
  const low = (name + " " + msg).toLowerCase();
  return (
    low.includes("permissions policy") ||
    low.includes("permission policy") ||
    low.includes("feature policy")
  );
}

export function voiceErrorMessage(err: unknown): string {
  if (isPermissionsPolicyBlock(err)) {
    return (
      "Браузер заблокировал микрофон политикой сайта (Permissions-Policy).\n\n" +
      "Обновите страницу после перезапуска frontend — микрофон должен быть разрешён для этого домена."
    );
  }
  const name =
    err && typeof err === "object" && "name" in err
      ? String((err as { name: string }).name)
      : "";
  const msg =
    err && typeof err === "object" && "message" in err
      ? String((err as { message: string }).message)
      : "";
  if (/NotAllowed|Permission|denied/i.test(name + msg)) {
    return (
      "Genesis не получил доступ к микрофону.\n\n" +
      "Нажмите «Разрешить микрофон» или откройте 🔒 возле адресной строки → Микрофон → Разрешить."
    );
  }
  if (/NotFound|DevicesNotFound/i.test(name)) {
    return "Микрофон не найден. Подключите микрофон и нажмите «Попробовать снова».";
  }
  if (/NotReadable|TrackStart|Abort/i.test(name)) {
    return "Микрофон занят или прерван. Закройте другие приложения и нажмите «Попробовать снова».";
  }
  if (/DOMException|SecurityError/i.test(name + msg)) {
    return "Голос работает только по HTTPS или на localhost. Откройте сайт безопасно и попробуйте снова.";
  }
  return "Не удалось включить микрофон. Нажмите «Попробовать снова» или напишите текстом.";
}

export function isMicContextAllowed(): boolean {
  if (typeof window === "undefined") return false;
  const { protocol, hostname } = window.location;
  if (protocol === "https:") return true;
  return hostname === "localhost" || hostname === "127.0.0.1";
}

export const MIC_CONTEXT_WARNING =
  "Голос работает по безопасному соединению (HTTPS) или на localhost. " +
  "Откройте сайт как https://… или http://localhost:3000/site";

export async function micPermissionState(): Promise<PermissionState | "unknown"> {
  if (typeof navigator === "undefined" || !navigator.permissions?.query) return "unknown";
  try {
    const s = await navigator.permissions.query({ name: "microphone" as PermissionName });
    return s.state;
  } catch {
    return "unknown";
  }
}

export function getSpeechRecognitionCtor(): (new () => SpeechRecognition) | null {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null;
}
