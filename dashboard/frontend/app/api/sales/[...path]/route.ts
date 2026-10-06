import { NextRequest, NextResponse } from "next/server";
import { backendApiBase, backendConfigured } from "../../../lib/backendProxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

async function proxy(req: NextRequest, prefix: "sales" | "public", pathParts: string[]) {
  if (!backendConfigured()) {
    return NextResponse.json(
      { detail: "Backend offline", code: "BACKEND_OFFLINE" },
      { status: 503 },
    );
  }
  const base = backendApiBase();
  const sub = pathParts.map(encodeURIComponent).join("/");
  const url = new URL(req.url);
  const target = `${base}/api/${prefix}/${sub}${url.search}`;

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (HOP_BY_HOP.has(key.toLowerCase())) return;
    headers.set(key, value);
  });
  if (!headers.has("user-agent")) headers.set("user-agent", "virtus-core-vercel-proxy");

  const init: RequestInit = { method: req.method, headers, redirect: "manual" };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  try {
    const upstream = await fetch(target, init);
    const outHeaders = new Headers();
    upstream.headers.forEach((value, key) => {
      if (HOP_BY_HOP.has(key.toLowerCase())) return;
      if (key.toLowerCase() === "content-encoding") return;
      outHeaders.set(key, value);
    });
    return new NextResponse(upstream.body, { status: upstream.status, headers: outHeaders });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "fetch_failed";
    return NextResponse.json(
      { detail: `Backend unreachable: ${msg}`, code: "BACKEND_UNREACHABLE" },
      { status: 502 },
    );
  }
}

type Ctx = { params: Promise<{ path?: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, "sales", path);
}
export async function POST(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, "sales", path);
}
export async function PUT(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, "sales", path);
}
export async function PATCH(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, "sales", path);
}
export async function DELETE(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, "sales", path);
}
