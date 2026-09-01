/**
 * Smart alerts for OWN treasury balance / mempool events.
 * Browser posts to /api/treasury/alert — secrets stay server-side.
 */
export type TreasuryAlertPayload = {
  title: string;
  body: string;
  severity: "info" | "warning" | "critical";
  address?: string;
  network?: "ETH" | "BTC";
  at?: string;
};

export async function sendTreasuryAlert(payload: TreasuryAlertPayload): Promise<{ ok: boolean; detail: string }> {
  try {
    const res = await fetch("/api/treasury/alert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...payload, at: payload.at ?? new Date().toISOString() }),
    });
    if (!res.ok) {
      const t = await res.text();
      return { ok: false, detail: t || `HTTP ${res.status}` };
    }
    const data = (await res.json()) as { ok?: boolean; detail?: string };
    return { ok: !!data.ok, detail: data.detail || "sent" };
  } catch (e) {
    return { ok: false, detail: e instanceof Error ? e.message : String(e) };
  }
}
