/**
 * M3.1 Surface Registry — Public / Client / CEO classification.
 * Source of truth: dashboard/platform/surface_registry.json
 */

import registry from "../../../platform/surface_registry.json";

export type SurfaceTarget = "public" | "client" | "ceo";
export type ShellKind = "public" | "mission_control" | "transitional";

export type SurfaceRoute = {
  path: string;
  label: string;
  target: SurfaceTarget;
  current_shell: ShellKind;
  capabilities: string[];
  overlap?: SurfaceTarget[];
  migration_note?: string;
};

export type SurfaceRegistry = {
  version: string;
  routes: SurfaceRoute[];
  kernel_layers: string[];
  slice_gate: string[];
};

export const SURFACE_REGISTRY = registry as SurfaceRegistry;

function patternToRegex(path: string): RegExp {
  const escaped = path
    .split("/")
    .map((seg) => (seg.startsWith(":") ? "[^/]+" : seg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
    .join("/");
  return new RegExp(`^${escaped}$`);
}

export function classifyPath(pathname: string): SurfaceRoute | undefined {
  let best: SurfaceRoute | undefined;
  let bestLen = -1;
  for (const route of SURFACE_REGISTRY.routes) {
    if (patternToRegex(route.path).test(pathname) && route.path.length > bestLen) {
      best = route;
      bestLen = route.path.length;
    }
  }
  return best;
}

export function routesForTarget(target: SurfaceTarget): SurfaceRoute[] {
  return SURFACE_REGISTRY.routes.filter(
    (r) => r.target === target || (r.overlap ?? []).includes(target),
  );
}

/** Mission Control chrome prefixes — mirrors AppShell until M3.2 wires registry directly. */
export function missionControlPrefixes(): string[] {
  const prefixes = new Set<string>();
  for (const route of SURFACE_REGISTRY.routes) {
    if (route.current_shell === "mission_control") {
      const base = route.path.split("/:")[0] || "/";
      prefixes.add(base === "" ? "/" : base);
    }
  }
  return Array.from(prefixes);
}

export function isMissionControlRoute(pathname: string): boolean {
  if (pathname === "/") return true;
  if (pathname === "/products") return false;
  return missionControlPrefixes().some(
    (p) => pathname === p || (p !== "/" && pathname.startsWith(`${p}/`)),
  );
}

export const SLICE_GATE = SURFACE_REGISTRY.slice_gate;
