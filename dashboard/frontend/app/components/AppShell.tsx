"use client";

import { usePathname } from "next/navigation";
import { Nav } from "./Nav";

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
    <div className="mx-auto min-h-screen max-w-6xl px-3 pb-10 pt-4 sm:px-5 lg:px-6">
      <Nav />
      {children}
    </div>
  );
}
