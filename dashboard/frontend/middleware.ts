/**
 * Public vs Owner surfaces.
 *
 * - Genesis.exe / localhost / 127.0.0.1 → Mission Control ALWAYS open (no key).
 * - Public DNS (beta / Google) → CEO remote control NEVER shown to anonymous;
 *   send them to the marketing storefront `/site` (buy sites / bots).
 * - Optional: GENESIS_OWNER_GATE_SECRET cookie still unlocks remote CEO if needed.
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/** Public marketing / legal — crawlable. */
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

const PUBLIC_API_PREFIXES = [
  "/api/public/",
  "/api/sales/",
  "/api/client/",
  "/api/webhooks/",
  "/api/v1/",
  "/api/factory/",
  "/webhooks/",
];

const CLIENT_PREFIXES = ["/client", "/projects"];

const SECURITY_HEADERS: Record<string, string> = {
  "X-Frame-Options": "DENY",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(self), geolocation=()",
  "X-DNS-Prefetch-Control": "off",
};

/** Only Privacy + Terms — TikTok Developer Portal embeds these in an iframe. */
const FRAMEABLE_LEGAL = new Set(["/agb", "/datenschutz"]);

const LEGAL_EMBED_CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "connect-src 'self' http://127.0.0.1:* http://localhost:* https:",
  "media-src 'self' blob:",
  "frame-src 'self'",
  "frame-ancestors *",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

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
  opts: { noindex: boolean; pathname?: string },
): NextResponse {
  const allowFrame = Boolean(
    opts.pathname && FRAMEABLE_LEGAL.has(opts.pathname),
  );
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) {
    if (allowFrame && k === "X-Frame-Options") continue;
    response.headers.set(k, v);
  }
  if (allowFrame) {
    // Strip DENY from next.config global headers; allow portal iframes.
    response.headers.delete("X-Frame-Options");
    response.headers.set("Content-Security-Policy", LEGAL_EMBED_CSP);
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
): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = pathname;
  url.search = "";
  return applySecurityHeaders(NextResponse.redirect(url), {
    noindex: true,
    pathname: request.nextUrl.pathname,
  });
}

function unauthorizedJson(): NextResponse {
  return applySecurityHeaders(
    NextResponse.json({ detail: "Unauthorized" }, { status: 401 }),
    { noindex: true },
  );
}

/**
 * Public internet: never render CEO remote control for anonymous visitors.
 * Send them to the storefront. Optional owner cookie unlocks remote CEO.
 */
function publicCeoGate(request: NextRequest): NextResponse {
  if (hasOwnerCookie(request)) {
    const secret = ownerSecret();
    const response = applySecurityHeaders(NextResponse.next(), {
      noindex: true,
      pathname: request.nextUrl.pathname,
    });
    const tokenParam = request.nextUrl.searchParams.get("owner");
    if (secret && tokenParam === secret) {
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
  // Google / strangers → marketing site (buy), not Mission Control.
  return redirectTo(request, "/site");
}

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const host = request.headers.get("host") || "";
  const loopback = isLoopbackHost(host);

  // Owner daily path (Genesis.exe): Mission Control always open.
  if (loopback) {
    return applySecurityHeaders(NextResponse.next(), {
      noindex: !isPublicMarketingPath(path),
      pathname: path,
    });
  }

  if (path.startsWith("/portal/")) {
    return applySecurityHeaders(NextResponse.next(), {
      noindex: true,
      pathname: path,
    });
  }

  if (isPublicMarketingPath(path)) {
    return applySecurityHeaders(NextResponse.next(), {
      noindex: false,
      pathname: path,
    });
  }

  if (isPublicApiPath(path)) {
    return applySecurityHeaders(NextResponse.next(), {
      noindex: true,
      pathname: path,
    });
  }

  if (path.startsWith("/api/") || path.startsWith("/webhooks/")) {
    if (hasOwnerCookie(request)) {
      return applySecurityHeaders(NextResponse.next(), {
        noindex: true,
        pathname: path,
      });
    }
    return unauthorizedJson();
  }

  if (isClientPath(path)) {
    if (hasClientSession(request)) {
      return applySecurityHeaders(NextResponse.next(), {
        noindex: true,
        pathname: path,
      });
    }
    // Logged-out strangers → storefront (not CEO chrome).
    return redirectTo(request, "/site");
  }

  return publicCeoGate(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|package-previews/|brand/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|js|css|ico|woff2?)$).*)",
  ],
};
