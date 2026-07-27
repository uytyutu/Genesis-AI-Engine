/**
 * P0 — Auth + indexing gate for Virtus Core Next.js surfaces.
 *
 * Fail-closed for ALL hosts (including localhost / Genesis.exe).
 * Anonymous / Incognito never receive Owner Panel HTML.
 * LAN (192.168.*) is never trusted. Bind Mission Control to 127.0.0.1 as well.
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/** Public marketing / legal — crawlable, no owner auth. */
const PUBLIC_EXACT = new Set([
  "/site",
  "/services",
  "/products",
  "/order",
  "/pricing",
  "/faq",
  "/kontakt",
  "/trust",
  "/impressum",
  "/datenschutz",
  "/agb",
  "/widerruf",
  "/cookies",
  "/ai-disclaimer",
  "/intellectual-property",
  "/owner-gate",
  "/client/login",
  "/client/register",
  "/robots.txt",
  "/sitemap.xml",
  "/manifest.webmanifest",
]);

const PUBLIC_ASSET_PREFIXES = [
  "/order/",
  "/products/",
  "/site/",
  "/brand/",
  "/_next/",
  "/package-previews/",
  "/icon",
  "/favicon",
];

/** APIs safe without owner cookie (still validated by backend). */
const PUBLIC_API_PREFIXES = [
  "/api/public/",
  "/api/sales/",
  "/api/client/",
  "/api/webhooks/",
  "/api/v1/",
  "/api/factory/",
  "/webhooks/",
];

/** Client office — needs client session cookie (or portal virtus_session). */
const CLIENT_PREFIXES = ["/client", "/projects"];

const SECURITY_HEADERS: Record<string, string> = {
  "X-Frame-Options": "DENY",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(self), geolocation=()",
  "X-DNS-Prefetch-Control": "off",
  "Content-Security-Policy": [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data:",
    "connect-src 'self' http://127.0.0.1:* http://localhost:* https:",
    "media-src 'self' blob:",
    "frame-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; "),
};

const NOINDEX =
  "noindex, nofollow, noarchive, nosnippet, noimageindex";

function isLoopbackHost(host: string): boolean {
  const h = (host || "").split(":")[0]?.toLowerCase() ?? "";
  return (
    h === "localhost" ||
    h === "127.0.0.1" ||
    h === "[::1]" ||
    h === "::1"
  );
}

function isPublicMarketingPath(path: string): boolean {
  if (PUBLIC_EXACT.has(path)) return true;
  return PUBLIC_ASSET_PREFIXES.some((p) => path.startsWith(p));
}

function isPublicApiPath(path: string): boolean {
  return PUBLIC_API_PREFIXES.some((p) => path.startsWith(p));
}

function isClientPath(path: string): boolean {
  if (
    path === "/client/login" ||
    path === "/client/register" ||
    path.startsWith("/client/login") ||
    path.startsWith("/client/register")
  ) {
    return false;
  }
  return CLIENT_PREFIXES.some(
    (p) => path === p || path.startsWith(`${p}/`),
  );
}

function applySecurityHeaders(
  response: NextResponse,
  opts: { noindex: boolean },
): NextResponse {
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) {
    response.headers.set(k, v);
  }
  if (opts.noindex) {
    response.headers.set("X-Robots-Tag", NOINDEX);
  }
  return response;
}

function ownerSecret(): string {
  return (
    process.env.GENESIS_OWNER_GATE_SECRET ||
    process.env.NEXT_PUBLIC_OWNER_GATE_SECRET ||
    ""
  ).trim();
}

function hasOwnerCookie(request: NextRequest): boolean {
  const secret = ownerSecret();
  if (!secret) return false;
  const cookie = request.cookies.get("genesis_owner")?.value;
  const tokenParam = request.nextUrl.searchParams.get("owner");
  return cookie === secret || tokenParam === secret;
}

function hasClientSession(request: NextRequest): boolean {
  const token = request.cookies.get("virtus_client_token")?.value;
  if (token && token.length > 8) return true;
  const portal = request.cookies.get("virtus_session")?.value;
  return Boolean(portal && portal.length > 8);
}

function redirectTo(
  request: NextRequest,
  pathname: string,
  nextPath?: string,
): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = pathname;
  url.search = "";
  if (nextPath) {
    url.searchParams.set("next", nextPath);
  }
  return applySecurityHeaders(NextResponse.redirect(url), { noindex: true });
}

function unauthorizedJson(): NextResponse {
  return applySecurityHeaders(
    NextResponse.json({ detail: "Unauthorized" }, { status: 401 }),
    { noindex: true },
  );
}

function requireOwnerPage(request: NextRequest, path: string): NextResponse {
  const secret = ownerSecret();
  // Fail-closed: no secret → never CEO HTML (gate page only).
  if (!secret) {
    if (path === "/owner-gate") {
      return applySecurityHeaders(NextResponse.next(), { noindex: true });
    }
    return redirectTo(request, "/owner-gate", path);
  }

  if (hasOwnerCookie(request)) {
    const response = applySecurityHeaders(NextResponse.next(), {
      noindex: true,
    });
    const tokenParam = request.nextUrl.searchParams.get("owner");
    if (tokenParam === secret) {
      response.cookies.set("genesis_owner", secret, {
        httpOnly: true,
        sameSite: "lax",
        secure: request.nextUrl.protocol === "https:",
        maxAge: 60 * 60 * 24 * 30,
        path: "/",
      });
    }
    return response;
  }

  if (path !== "/owner-gate") {
    return redirectTo(request, "/owner-gate", path);
  }
  return applySecurityHeaders(NextResponse.next(), { noindex: true });
}

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const host = request.headers.get("host") || "";
  const loopback = isLoopbackHost(host);

  // Portal commerce — cookie session enforced by backend; allow through.
  if (path.startsWith("/portal/")) {
    return applySecurityHeaders(NextResponse.next(), { noindex: true });
  }

  // Public marketing / assets
  if (isPublicMarketingPath(path)) {
    return applySecurityHeaders(NextResponse.next(), { noindex: false });
  }

  // Public commerce / client-auth APIs
  if (isPublicApiPath(path)) {
    return applySecurityHeaders(NextResponse.next(), { noindex: true });
  }

  // Internal APIs: loopback (Genesis.exe) or owner cookie; else 401.
  if (path.startsWith("/api/") || path.startsWith("/webhooks/")) {
    if (loopback || hasOwnerCookie(request)) {
      return applySecurityHeaders(NextResponse.next(), { noindex: true });
    }
    return unauthorizedJson();
  }

  // Client workspace — auth always (incognito without cookie → login).
  if (isClientPath(path)) {
    if (hasClientSession(request)) {
      return applySecurityHeaders(NextResponse.next(), { noindex: true });
    }
    return redirectTo(request, "/client/login", path);
  }

  // CEO / Owner / Mission Control — auth always (no localhost guest bypass).
  return requireOwnerPage(request, path);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|package-previews/|brand/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|js|css|ico|woff2?)$).*)",
  ],
};
