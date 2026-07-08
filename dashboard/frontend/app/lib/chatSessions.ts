/** Conversation UX v1 — chat threads (Level 1–2) separate from visitor profile (Level 3). */

export type StoredMessage = {
  role: "user" | "assistant";
  text: string;
  cta_href?: string | null;
  cta_label?: string | null;
};

export type ChatSessionMeta = {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  preview?: string;
  pinned?: boolean;
};

export type SessionsStore = {
  version: 1;
  activeSessionId: string | null;
  /** Cached messages for offline / fast restore */
  localMessages: Record<string, StoredMessage[]>;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function sessionsStorageKey(scope: "public" | "owner"): string {
  return scope === "owner" ? "genesis_owner_sessions_v1" : "genesis_chat_sessions_v1";
}

export function loadSessionsStore(scope: "public" | "owner"): SessionsStore {
  if (typeof window === "undefined") {
    return { version: 1, activeSessionId: null, localMessages: {} };
  }
  try {
    const raw = localStorage.getItem(sessionsStorageKey(scope));
    if (!raw) return { version: 1, activeSessionId: null, localMessages: {} };
    const parsed = JSON.parse(raw) as SessionsStore;
    if (parsed?.version === 1) return parsed;
  } catch {
    /* ignore */
  }
  return { version: 1, activeSessionId: null, localMessages: {} };
}

export function saveSessionsStore(scope: "public" | "owner", store: SessionsStore): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(sessionsStorageKey(scope), JSON.stringify(store));
  } catch {
    /* private mode */
  }
}

export async function fetchSessionList(
  visitorId: string,
): Promise<ChatSessionMeta[]> {
  const res = await fetch(
    `${API}/api/public/genesis-ai/sessions?visitor_id=${encodeURIComponent(visitorId)}`,
  );
  if (!res.ok) return [];
  const data = (await res.json()) as { sessions?: ChatSessionMeta[] };
  return data.sessions ?? [];
}

export async function createSession(
  visitorId: string,
  title = "Новый чат",
): Promise<ChatSessionMeta | null> {
  const res = await fetch(`${API}/api/public/genesis-ai/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ visitor_id: visitorId, title }),
  });
  if (!res.ok) return null;
  const row = (await res.json()) as {
    session_id: string;
    title: string;
    created_at: string;
  };
  const now = row.created_at || new Date().toISOString();
  return {
    session_id: row.session_id,
    title: row.title,
    created_at: now,
    updated_at: now,
    preview: "",
    pinned: false,
  };
}

export async function fetchSessionDetail(
  sessionId: string,
  visitorId: string,
): Promise<{ messages: StoredMessage[]; title: string; pinned: boolean } | null> {
  const res = await fetch(
    `${API}/api/public/genesis-ai/sessions/${encodeURIComponent(sessionId)}?visitor_id=${encodeURIComponent(visitorId)}`,
  );
  if (!res.ok) return null;
  const data = (await res.json()) as {
    title?: string;
    pinned?: boolean;
    messages?: Array<{ role: string; content: string }>;
  };
  const messages: StoredMessage[] = (data.messages ?? []).map((m) => ({
    role: m.role === "assistant" ? "assistant" : "user",
    text: m.content ?? "",
  }));
  return {
    messages,
    title: data.title ?? "Новый чат",
    pinned: Boolean(data.pinned),
  };
}

export async function deleteSessionApi(
  sessionId: string,
  visitorId: string,
): Promise<boolean> {
  const res = await fetch(
    `${API}/api/public/genesis-ai/sessions/${encodeURIComponent(sessionId)}?visitor_id=${encodeURIComponent(visitorId)}`,
    { method: "DELETE" },
  );
  return res.ok;
}

export async function pinSessionApi(
  sessionId: string,
  visitorId: string,
  pinned: boolean,
): Promise<boolean> {
  const res = await fetch(
    `${API}/api/public/genesis-ai/sessions/${encodeURIComponent(sessionId)}/pin`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ visitor_id: visitorId, pinned }),
    },
  );
  return res.ok;
}

export type DateGroup = "pinned" | "today" | "yesterday" | "week" | "older";

export function groupSessionsByDate(
  sessions: ChatSessionMeta[],
): Record<DateGroup, ChatSessionMeta[]> {
  const pinned = sessions.filter((s) => s.pinned);
  const rest = sessions.filter((s) => !s.pinned);
  const now = new Date();
  const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startYesterday = new Date(startToday);
  startYesterday.setDate(startYesterday.getDate() - 1);
  const startWeek = new Date(startToday);
  startWeek.setDate(startWeek.getDate() - 7);

  const buckets: Record<DateGroup, ChatSessionMeta[]> = {
    pinned: pinned,
    today: [],
    yesterday: [],
    week: [],
    older: [],
  };

  for (const s of rest) {
    const d = new Date(s.updated_at || s.created_at);
    if (Number.isNaN(d.getTime())) {
      buckets.older.push(s);
      continue;
    }
    if (d >= startToday) buckets.today.push(s);
    else if (d >= startYesterday) buckets.yesterday.push(s);
    else if (d >= startWeek) buckets.week.push(s);
    else buckets.older.push(s);
  }
  return buckets;
}
