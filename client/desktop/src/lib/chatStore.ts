export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  at: string;
  pinned?: boolean;
};

const CHAT_KEY = "genesis.client.chat.v2";
const PINNED_KEY = "genesis.client.chat.pinned.v1";
const LEGACY_KEY = "genesis.client.chat.v1";

export const QUICK_COMMANDS: Record<string, string> = {
  "/focus": "What should I focus on today?",
  "/status": "Give me a short system and business status.",
  "/projects": "Summarize my active factory projects.",
  "/revenue": "What is today's and this month's revenue?",
};

export function loadChat(): ChatMessage[] {
  try {
    const raw =
      localStorage.getItem(CHAT_KEY) ?? localStorage.getItem(LEGACY_KEY);
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

export function saveChat(messages: ChatMessage[]) {
  localStorage.setItem(CHAT_KEY, JSON.stringify(messages.slice(-80)));
}

export function loadPinnedPrompts(): string[] {
  try {
    const raw = localStorage.getItem(PINNED_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

export function savePinnedPrompts(prompts: string[]) {
  localStorage.setItem(PINNED_KEY, JSON.stringify(prompts.slice(0, 12)));
}

export function searchChat(messages: ChatMessage[], query: string): ChatMessage[] {
  const q = query.trim().toLowerCase();
  if (!q) return messages;
  return messages.filter((m) => m.text.toLowerCase().includes(q));
}

export function recentChatSnippet(limit = 3): { text: string; at: string }[] {
  return loadChat()
    .filter((m) => m.role === "user")
    .slice(-limit)
    .reverse()
    .map((m) => ({ text: m.text, at: m.at }));
}

export function resolveQuickCommand(input: string): string | null {
  const key = input.trim().toLowerCase().split(/\s/)[0];
  return QUICK_COMMANDS[key] ?? null;
}
