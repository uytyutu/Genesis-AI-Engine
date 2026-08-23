/** Farm Accounts & Permissions — whitelist; no auto-login without user consent. */

export type FarmAccountId =
  | "github"
  | "opire"
  | "toloka"
  | "stackoverflow"
  | "gitlab"
  | "fiverr"
  | "upwork"
  | "meta"
  | "google";

export type FarmAccountMode = "auto" | "ask" | "off";

export type FarmAccountState = {
  id: FarmAccountId;
  label: string;
  connected: boolean;
  mode: FarmAccountMode;
};

const STORAGE_KEY = "virtus.farm.accounts.v1";

const DEFAULTS: FarmAccountState[] = [
  { id: "github", label: "GitHub", connected: false, mode: "ask" },
  { id: "opire", label: "Opire", connected: false, mode: "ask" },
  { id: "toloka", label: "Toloka", connected: false, mode: "off" },
  { id: "stackoverflow", label: "Stack Overflow", connected: false, mode: "off" },
  { id: "gitlab", label: "GitLab", connected: false, mode: "off" },
  { id: "fiverr", label: "Fiverr", connected: false, mode: "off" },
  { id: "upwork", label: "Upwork", connected: false, mode: "off" },
  { id: "meta", label: "Meta", connected: false, mode: "off" },
  { id: "google", label: "Google", connected: false, mode: "off" },
];

export function loadFarmAccounts(): FarmAccountState[] {
  if (typeof window === "undefined") return DEFAULTS.map((d) => ({ ...d }));
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULTS.map((d) => ({ ...d }));
    const parsed = JSON.parse(raw) as Partial<FarmAccountState>[];
    return DEFAULTS.map((d) => {
      const hit = parsed.find((p) => p?.id === d.id);
      if (!hit) return { ...d };
      return {
        ...d,
        connected: Boolean(hit.connected),
        mode: (hit.mode === "auto" || hit.mode === "ask" || hit.mode === "off"
          ? hit.mode
          : d.mode) as FarmAccountMode,
      };
    });
  } catch {
    return DEFAULTS.map((d) => ({ ...d }));
  }
}

export function saveFarmAccounts(list: FarmAccountState[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function setFarmAccountMode(
  id: FarmAccountId,
  mode: FarmAccountMode,
): FarmAccountState[] {
  const next = loadFarmAccounts().map((a) => (a.id === id ? { ...a, mode } : a));
  saveFarmAccounts(next);
  return next;
}

export function setFarmAccountConnected(
  id: FarmAccountId,
  connected: boolean,
): FarmAccountState[] {
  const next = loadFarmAccounts().map((a) =>
    a.id === id ? { ...a, connected, mode: connected ? a.mode || "ask" : "off" } : a,
  );
  saveFarmAccounts(next);
  return next;
}

/** True only if whitelist allows auto use (never opens login itself). */
export function mayAutoUseAccount(id: FarmAccountId): boolean {
  const a = loadFarmAccounts().find((x) => x.id === id);
  return Boolean(a?.connected && a.mode === "auto");
}
