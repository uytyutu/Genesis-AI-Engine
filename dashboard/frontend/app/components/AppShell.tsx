"use client";

import { usePathname } from "next/navigation";
import { Nav } from "./Nav";

const PUBLIC_PREFIXES = ["/site", "/order"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";
  const isPublic =
    PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));

  if (isPublic) {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-3 pb-10 pt-4 sm:px-5 lg:px-6">
      <Nav />
      {children}
    </div>
  );
}
