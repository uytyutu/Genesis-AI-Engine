import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { LOCALE_COOKIE, parseLocale, DEFAULT_LOCALE } from "@/lib/i18n/core";

/** Support /@username share links → /u/username (rewrite, keep URL). */
export function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;
  // Next.js treats @folders as parallel routes — match the share URL explicitly.
  if (path.startsWith("/@")) {
    const raw = path.slice(2).replace(/\/$/, "");
    if (/^[a-zA-Z0-9_]{3,24}$/.test(raw)) {
      const url = req.nextUrl.clone();
      url.pathname = `/u/${raw.toLowerCase()}`;
      return NextResponse.rewrite(url);
    }
  }

  const res = NextResponse.next();
  // Ensure locale cookie exists so SSR layout can bake the right language.
  if (!req.cookies.get(LOCALE_COOKIE)?.value) {
    const accept = req.headers.get("accept-language") || "";
    const fromHeader = parseLocale(accept.split(",")[0]);
    res.cookies.set(LOCALE_COOKIE, fromHeader || DEFAULT_LOCALE, {
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
      sameSite: "lax",
    });
  }
  return res;
}

export const config = {
  // Avoid /@:param matchers — @ breaks path-to-regexp in Next middleware.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api|.*\\..*).*)"],
};
