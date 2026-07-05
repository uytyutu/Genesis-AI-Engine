"use client";

import { usePathname } from "next/navigation";
import { GenesisSidebar } from "./GenesisSidebar";
import { GenesisTopBar } from "./GenesisTopBar";
import { GenesisMobileNav } from "./GenesisMobileNav";

/** Routes that show Mission Control chrome (sidebar nav). Everything else = public marketing shell. */
const MC_PREFIXES = [
  "/finance",
  "/company",
  "/ai",
  "/cursor",
  "/revenue",
  "/marketplace",
  "/monitor",
  "/dev",
  "/check",
  "/create",
  "/settings",
  "/launch",
  "/opportunities",
  "/acquisition",
  "/projects",
  "/products",
  "/growth",
  "/tasks",
];

function isMissionControlRoute(pathname: string): boolean {
  if (pathname === "/") return true;
  return MC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";

  if (!isMissionControlRoute(pathname)) {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="genesis-app-shell">
      <GenesisSidebar />
      <div className="genesis-app-main">
        <GenesisTopBar />
        <GenesisMobileNav />
        <div className="genesis-app-content">{children}</div>
      </div>
    </div>
  );
}
