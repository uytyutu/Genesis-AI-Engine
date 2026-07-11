"use client";

import { usePathname } from "next/navigation";
import { resolveNavigationSurface } from "../lib/surfaceNavConfig";
import { GenesisSidebar } from "./GenesisSidebar";
import { GenesisTopBar } from "./GenesisTopBar";
import { GenesisMobileNav } from "./GenesisMobileNav";
import { ClientWorkspaceNav } from "./navigation/ClientWorkspaceNav";
import { ClientWorkspaceTopBar } from "./navigation/ClientWorkspaceTopBar";
import { ClientMobileNav } from "./navigation/ClientMobileNav";

/** M3.2: three navigation shells — one product, one Vector, shared kernel. */

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";
  const surface = resolveNavigationSurface(pathname);

  if (surface === "public") {
    return (
      <div className="virtus-surface-public min-h-screen" data-surface="public">
        {children}
      </div>
    );
  }

  if (surface === "client") {
    return (
      <div className="genesis-app-shell virtus-surface-client" data-surface="client">
        <ClientWorkspaceNav />
        <div className="genesis-app-main">
          <ClientWorkspaceTopBar />
          <ClientMobileNav />
          <div className="genesis-app-content">{children}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="genesis-app-shell virtus-surface-ceo" data-surface="ceo">
      <GenesisSidebar />
      <div className="genesis-app-main">
        <GenesisTopBar />
        <GenesisMobileNav />
        <div className="genesis-app-content">{children}</div>
      </div>
    </div>
  );
}
