/** Turn FastAPI `detail` (string | validation object | array) into display text. */
export function formatApiDetail(detail: unknown, fallback = "Ошибка"): string {
  if (detail == null) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map(formatValidationItem).join("; ") || fallback;
  }
  if (typeof detail === "object" && detail !== null && "msg" in detail) {
    return formatValidationItem(detail);
  }
  return fallback;
}

function formatValidationItem(item: unknown): string {
  if (typeof item === "string") return item;
  if (item && typeof item === "object" && "msg" in item) {
    const o = item as { msg?: unknown; loc?: unknown };
    const msg = typeof o.msg === "string" ? o.msg : String(o.msg ?? "");
    const loc = Array.isArray(o.loc) ? o.loc.map(String).join(".") : "";
    return loc ? `${loc}: ${msg}` : msg;
  }
  return String(item);
}
