"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BRAND_NAME } from "../../lib/publicBrand";

const TITLES: Record<string, string> = {
  "/projects": "Проекты",
  "/create": "Создать",
};

export function ClientWorkspaceTopBar() {
  const pathname = usePathname() ?? "/";
  const base = `/${pathname.split("/").filter(Boolean)[0] ?? ""}`;
  const title = TITLES[pathname] ?? TITLES[base] ?? "Моя компания";

  return (
    <header className="genesis-topbar">
      <div>
        <p className="genesis-topbar__eyebrow">{BRAND_NAME}</p>
        <h1 className="genesis-topbar__title">{title}</h1>
      </div>
      <div className="genesis-topbar__actions">
        <Link href="/site?view=vector" className="genesis-topbar__cta">
          Vector
        </Link>
      </div>
    </header>
  );
}
