import { NextRequest, NextResponse } from "next/server";

/**
 * POST /api/treasury/alert
 * Forwards to TREASURY_WEBHOOK_URL and/or Telegram (server env only).
 */
export async function POST(req: NextRequest) {
  let body: {
    title?: string;
    body?: string;
    severity?: string;
    address?: string;
    network?: string;
    at?: string;
  };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, detail: "invalid json" }, { status: 400 });
  }

  const text = [
    `[Virtus Treasury] ${body.severity || "info"}`,
    body.title || "Alert",
    body.body || "",
    body.network ? `network=${body.network}` : "",
    body.address ? `address=${body.address}` : "",
    body.at || new Date().toISOString(),
  ]
    .filter(Boolean)
    .join("\n");

  const results: string[] = [];

  const webhook = process.env.TREASURY_WEBHOOK_URL;
  if (webhook) {
    try {
      const r = await fetch(webhook, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, ...body, source: "virtus-treasury" }),
      });
      results.push(`webhook:${r.status}`);
    } catch (e) {
      results.push(`webhook:fail:${e instanceof Error ? e.message : "err"}`);
    }
  }

  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chat = process.env.TELEGRAM_CHAT_ID;
  if (token && chat) {
    try {
      const r = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chat, text }),
      });
      results.push(`telegram:${r.status}`);
    } catch (e) {
      results.push(`telegram:fail:${e instanceof Error ? e.message : "err"}`);
    }
  }

  if (!webhook && !(token && chat)) {
    return NextResponse.json({
      ok: false,
      detail: "No TREASURY_WEBHOOK_URL or TELEGRAM_BOT_TOKEN+TELEGRAM_CHAT_ID configured",
    });
  }

  const ok = results.some((x) => /:(200|201|204)$/.test(x) || x.includes(":200"));
  return NextResponse.json({ ok, detail: results.join(" · ") });
}
