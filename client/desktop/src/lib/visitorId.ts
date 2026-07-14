const VISITOR_KEY = "genesis_visitor_id";

export function getPriorVisitorId(): string {
  if (typeof localStorage === "undefined") return "";
  try {
    return localStorage.getItem(VISITOR_KEY) || "";
  } catch {
    return "";
  }
}

export function setPlatformVisitorId(id: string): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(VISITOR_KEY, id);
  } catch {
    /* ignore */
  }
}
