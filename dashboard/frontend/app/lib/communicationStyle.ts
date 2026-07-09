/** Vector communication style — persisted user preference. */

export const COMMUNICATION_STYLE_KEY = "virtus_communication_style";

export type CommunicationStyle =
  | "auto"
  | "professional"
  | "friendly"
  | "casual"
  | "concise"
  | "mentor";

export const COMMUNICATION_STYLE_OPTIONS: {
  id: CommunicationStyle;
  label: string;
  emoji: string;
}[] = [
  { id: "auto", label: "Auto", emoji: "✨" },
  { id: "professional", label: "Professional", emoji: "💼" },
  { id: "friendly", label: "Friendly", emoji: "🙂" },
  { id: "casual", label: "Casual", emoji: "😎" },
  { id: "concise", label: "Concise", emoji: "⚡" },
  { id: "mentor", label: "Mentor", emoji: "🎓" },
];

export const DEFAULT_COMMUNICATION_STYLE: CommunicationStyle = "auto";

export function loadCommunicationStyle(): CommunicationStyle {
  if (typeof window === "undefined") return DEFAULT_COMMUNICATION_STYLE;
  try {
    const raw = localStorage.getItem(COMMUNICATION_STYLE_KEY);
    if (raw && COMMUNICATION_STYLE_OPTIONS.some((o) => o.id === raw)) {
      return raw as CommunicationStyle;
    }
  } catch {
    /* private mode */
  }
  return DEFAULT_COMMUNICATION_STYLE;
}

export function saveCommunicationStyle(style: CommunicationStyle): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(COMMUNICATION_STYLE_KEY, style);
  } catch {
    /* private mode */
  }
}
