/** Guest order cabinet history (browser localStorage). */

const KEY = "virtus_order_history_v1";
const MAX = 40;

export type StoredOrderRef = {
  order_id: string;
  business_name?: string;
  package_name?: string;
  price_label?: string;
  market_code?: string;
  status?: string;
  saved_at: string;
};

export function listStoredOrders(): StoredOrderRef[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as StoredOrderRef[]) : [];
  } catch {
    return [];
  }
}

export function rememberOrder(ref: Omit<StoredOrderRef, "saved_at"> & { saved_at?: string }): void {
  if (typeof window === "undefined" || !ref.order_id) return;
  try {
    const next: StoredOrderRef = {
      ...ref,
      saved_at: ref.saved_at || new Date().toISOString(),
    };
    const list = listStoredOrders().filter((o) => o.order_id !== next.order_id);
    list.unshift(next);
    window.localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)));
  } catch {
    /* private mode / quota */
  }
}
