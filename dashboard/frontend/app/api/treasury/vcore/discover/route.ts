import { NextResponse } from "next/server";
import { STON_NATIVE_TON } from "../../../../lib/treasury/vcoreConversion";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const STON = "https://api.ston.fi";

async function stonGet(path: string, ms = 20_000): Promise<{ ok: boolean; status: number; json: unknown }> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(`${STON}${path}`, {
      signal: ctrl.signal,
      headers: { Accept: "application/json", "User-Agent": "VirtusCore-VCORE/0.1" },
      cache: "no-store",
    });
    const json = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return { ok: false, status: 0, json: { error: e instanceof Error ? e.message : String(e) } };
  } finally {
    clearTimeout(t);
  }
}

async function stonPost(path: string, body: unknown, ms = 20_000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(`${STON}${path}`, {
      method: "POST",
      signal: ctrl.signal,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "User-Agent": "VirtusCore-VCORE/0.1",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const json = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return { ok: false, status: 0, json: { error: e instanceof Error ? e.message : String(e) } };
  } finally {
    clearTimeout(t);
  }
}

/**
 * GET /api/treasury/vcore/discover
 * Honest DEX discovery: STON.fi routers + search VCORE + TON asset ping.
 */
export async function GET() {
  const routers = await stonGet("/v1/routers");
  const tonAsset = await stonGet(`/v1/assets/${STON_NATIVE_TON}`);
  const search = await stonPost("/v1/assets/query", {
    search_terms: ["VCORE", "Virtus", "VirtusCore"],
    limit: 10,
  });

  const routerList =
    (routers.json as { router_list?: unknown[] } | null)?.router_list ??
    (Array.isArray(routers.json) ? routers.json : []);
  const assetList =
    (search.json as { asset_list?: Array<{ symbol?: string; contract_address?: string }> } | null)
      ?.asset_list ?? [];

  const vcoreHits = assetList.filter((a) => {
    const s = (a.symbol || "").toUpperCase();
    return s === "VCORE" || s.includes("VIRTUS");
  });

  const tonOk = tonAsset.ok && !!(tonAsset.json as { asset?: unknown } | null)?.asset;
  const apiOk = routers.ok || tonOk;

  const vcoreFound = vcoreHits.length > 0;
  const poolFound = false; // no VCORE pool until jetton exists + LP funded

  let detail: string;
  if (!apiOk) {
    detail = "STON.fi API недоступен — discovery отложен.";
  } else if (!vcoreFound) {
    detail =
      "VCORE не найден в каталоге STON.fi. Jetton master не задеплоен / не листится. Пул VCORE/TON отсутствует → quote = 0, EXCHANGE заблокирован.";
  } else {
    detail = "VCORE найден в каталоге, но пул/ликвидность ещё не подтверждены — следующий шаг: pool query.";
  }

  return NextResponse.json({
    ok: true,
    at: new Date().toISOString(),
    venue: "STON.fi",
    apiOk,
    routers: Array.isArray(routerList) ? routerList.length : 0,
    tonAssetAddress: tonOk ? STON_NATIVE_TON : null,
    tonAssetMeta: tonOk ? (tonAsset.json as { asset: unknown }).asset : null,
    vcoreFound,
    vcoreAssetAddress: vcoreHits[0]?.contract_address ?? null,
    vcoreHits,
    poolFound,
    detail,
    identityRequired: {
      jettonMaster: null,
      status: "GENESIS_DRAFT",
      next: [
        "Deploy VCORE Jetton master on TON testnet",
        "Fund VCORE/TON pool (testnet liquidity)",
        "Simulate swap via POST /v1/swap/simulate",
        "TON Connect sign → confirm → REAL SETTLEMENT",
      ],
    },
    law: "No liquidity / no route ⇒ no TON. UI must not paint REAL without chain confirmation.",
    farmSpendNote:
      "Toloka/API ~20 € на счету — операционный Farm spend, не резерв AMM и не эмиссия TON.",
  });
}
