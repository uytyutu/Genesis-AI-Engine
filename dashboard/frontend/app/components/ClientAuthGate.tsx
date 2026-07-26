"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getClientToken } from "../lib/clientAuth";
import { BRAND_NAME } from "../lib/publicBrand";

type AuthState = "loading" | "authed" | "guest";

async function probePortalSession(): Promise<boolean> {
  try {
    const res = await fetch("/portal/my-products", {
      credentials: "include",
      cache: "no-store",
    });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * G2.X — Client Workspace is auth-only.
 * Unauthenticated visitors see Login/Register only (no Dashboard/Projects/Inbox chrome).
 */
export function ClientAuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";
  const router = useRouter();
  const [state, setState] = useState<AuthState>("loading");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      if (getClientToken()) {
        if (!cancelled) setState("authed");
        return;
      }
      const portalOk = await probePortalSession();
      if (!cancelled) setState(portalOk ? "authed" : "guest");
    })();
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  useEffect(() => {
    if (state !== "guest") return;
    const next = pathname && pathname !== "/client/login" ? pathname : "/client";
    router.replace(`/client/login?next=${encodeURIComponent(next)}`);
  }, [state, pathname, router]);

  if (state === "loading") {
    return (
      <div className="flex min-h-[40vh] items-center justify-center px-4 text-sm text-zinc-400">
        Checking account…
      </div>
    );
  }

  if (state === "guest") {
    return (
      <div className="mx-auto flex min-h-[50vh] max-w-md flex-col justify-center px-4 py-10 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-emerald-300/90">
          {BRAND_NAME}
        </p>
        <h1 className="mt-3 text-2xl font-semibold text-white">Sign in required</h1>
        <p className="mt-2 text-sm text-zinc-400">
          Your personal office opens after Login or Register. You can still buy a
          website or bot without an account from the public site.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            href={`/client/login?next=${encodeURIComponent(pathname || "/client")}`}
            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
          >
            Sign in
          </Link>
          <Link
            href={`/client/register?next=${encodeURIComponent(pathname || "/client")}`}
            className="rounded-xl border border-white/20 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/5"
          >
            Register
          </Link>
          <Link href="/site" className="w-full text-sm text-emerald-300 hover:underline sm:w-auto">
            ← Buy without account
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
