"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { PUBLIC_NAV_LINKS } from "../../lib/surfaceNavConfig";

export function PublicWorkspaceNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname() ?? "";
  const searchParams = useSearchParams();
  const view = searchParams.get("view") ?? "";

  return (
    <>
      {PUBLIC_NAV_LINKS.map((link) => {
        const active = link.match(pathname, view);
        return (
          <Link
            key={link.href}
            href={link.href}
            onClick={onNavigate}
            className={`rounded-lg px-3 py-2 text-center text-sm transition-smooth hover:bg-genesis-elevated hover:text-white sm:text-left ${
              active
                ? "bg-genesis-elevated/80 font-medium text-white"
                : "text-genesis-muted"
            }`}
            aria-current={active ? "page" : undefined}
          >
            {link.label}
          </Link>
        );
      })}
    </>
  );
}
