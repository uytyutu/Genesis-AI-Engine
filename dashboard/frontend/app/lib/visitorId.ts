const VISITOR_KEY = "genesis_visitor_id";
const OWNER_VISITOR_KEY = "genesis_owner_visitor_id";

export function getVisitorId(scope: "public" | "owner" = "public"): string {
  if (typeof window === "undefined") return "anonymous";
  const key = scope === "owner" ? OWNER_VISITOR_KEY : VISITOR_KEY;
  try {
    let id = localStorage.getItem(key);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(key, id);
    }
    return id;
  } catch {
    return "anonymous";
  }
}
