import { NextRequest, NextResponse } from "next/server";
import { STON_NATIVE_TON } from "../../../../lib/treasury/vcoreConversion";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * POST /api/treasury/vcore/simulate
 * Body: { amount: string, vcoreAddress?: string | null }
 * Honest: without deployed VCORE + pool → SIMULATION FAIL / SKIPPED, not fake TON out.
 */
export async function POST(req: NextRequest) {
  let body: { amount?: string; vcoreAddress?: string | null };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "invalid json" }, { status: 400 });
  }

  const amount = String(body.amount || "0").trim();
  const vcore = body.vcoreAddress?.trim() || null;

  if (!vcore) {
    return NextResponse.json({
      ok: true,
      simulation: "FAIL",
      blocker: "VCORE_NOT_DEPLOYED",
      from: "VCORE",
      to: "TON",
      amountIn: amount,
      amountOut: null,
      minReceive: null,
      feeHint: null,
      priceImpact: null,
      message:
        "Нет адреса Jetton master VCORE. Создать 1e12 VCORE в UI ≠ on-chain identity. Сначала deploy Jetton (testnet), затем пул.",
      executeAllowed: false,
    });
  }

  // Attempt real STON simulate — will fail without pool; we surface the error honestly
  const units = (() => {
    try {
      // assume 9 decimals draft
      const n = Number(amount);
      if (!Number.isFinite(n) || n <= 0) return null;
      return String(BigInt(Math.floor(n * 1e9)));
    } catch {
      return null;
    }
  })();

  if (!units) {
    return NextResponse.json({ ok: false, error: "invalid amount" }, { status: 400 });
  }

  try {
    const res = await fetch("https://api.ston.fi/v1/swap/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        offer_address: vcore,
        ask_address: STON_NATIVE_TON,
        units,
        slippage_tolerance: "0.01",
      }),
      cache: "no-store",
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json({
        ok: true,
        simulation: "FAIL",
        blocker: "ROUTE_MISSING",
        from: "VCORE",
        to: "TON",
        amountIn: amount,
        amountOut: null,
        minReceive: null,
        feeHint: null,
        priceImpact: null,
        message: `STON.fi simulate HTTP ${res.status}: ${JSON.stringify(json).slice(0, 400)}`,
        executeAllowed: false,
        raw: json,
      });
    }

    return NextResponse.json({
      ok: true,
      simulation: "PASS",
      blocker: "NONE",
      from: "VCORE",
      to: "TON",
      amountIn: amount,
      amountOut: json.ask_units ?? json.out_units ?? null,
      minReceive: json.min_ask_units ?? json.recommended_min_ask_units ?? null,
      feeHint: json.fee_units ? String(json.fee_units) : null,
      priceImpact: json.price_impact != null ? String(json.price_impact) : null,
      message: "Simulation PASS — можно готовить TON Connect tx (ещё не REAL).",
      executeAllowed: true,
      raw: json,
    });
  } catch (e) {
    return NextResponse.json({
      ok: true,
      simulation: "FAIL",
      blocker: "SIMULATION_FAIL",
      from: "VCORE",
      to: "TON",
      amountIn: amount,
      amountOut: null,
      minReceive: null,
      feeHint: null,
      priceImpact: null,
      message: e instanceof Error ? e.message : String(e),
      executeAllowed: false,
    });
  }
}
