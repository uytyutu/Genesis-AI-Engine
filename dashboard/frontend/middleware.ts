import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PREFIXES = ["/owner-gate", "/api/", "/_next/", "/icon", "/favicon", "/manifest"];

function isLocalHost(host: string): boolean {
  return host.includes("localhost") || host.includes("127.0.0.1");
}

function isPublicPath(path: string): boolean {
  return PUBLIC_PREFIXES.some((prefix) => path.startsWith(prefix));
}

export function middleware(request: NextRequest) {
  const gateEnabled = process.env.NEXT_PUBLIC_OWNER_GATE === "1";
  if (!gateEnabled) {
    return NextResponse.next();
  }

  const host = request.headers.get("host") || "";
  if (isLocalHost(host)) {
    return NextResponse.next();
  }

  const path = request.nextUrl.pathname;
  if (isPublicPath(path)) {
    return NextResponse.next();
  }

  const secret = (process.env.GENESIS_OWNER_GATE_SECRET || "").trim();
  if (!secret) {
    return NextResponse.next();
  }

  const cookie = request.cookies.get("genesis_owner")?.value;
  const tokenParam = request.nextUrl.searchParams.get("owner");

  if (cookie === secret || tokenParam === secret) {
    const response = NextResponse.next();
    if (tokenParam === secret && cookie !== secret) {
      response.cookies.set("genesis_owner", secret, {
        httpOnly: true,
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 30,
        path: "/",
      });
    }
    return response;
  }

  if (path !== "/owner-gate") {
    const url = request.nextUrl.clone();
    url.pathname = "/owner-gate";
    url.searchParams.set("next", path);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
