"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { nextFunnelStep } from "../../lib/publicFunnel";
import { PublicFunnelSteps, PublicNextStepBanner } from "./PublicIntroTeaser";

export function PublicFunnelFooter() {
  const pathname = usePathname() ?? "";
  const searchParams = useSearchParams();
  const view = searchParams.get("view") ?? "";
  const next = nextFunnelStep(pathname, view);
  const activeId =
    view === "vector"
      ? "vector"
      : pathname.startsWith("/site")
        ? "home"
        : pathname.startsWith("/services")
          ? "services"
          : undefined;

  if (!pathname.startsWith("/site") && !pathname.startsWith("/services") && pathname !== "/pricing") {
    return null;
  }

  return (
    <footer className="mt-10 space-y-4 border-t border-white/5 pt-6">
      <PublicFunnelSteps activeId={activeId} />
      {next ? <PublicNextStepBanner step={next} /> : null}
    </footer>
  );
}
