/**
 * Stripe Smoke €1 must never appear for normal buyers.
 * Dev only: NEXT_PUBLIC_SHOW_SMOKE_PACKAGE=1 or ?debug=smoke
 */
export function showSmokePackageInUi(): boolean {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_SHOW_SMOKE_PACKAGE === "1") {
    return true;
  }
  if (typeof window === "undefined") return false;
  try {
    return new URLSearchParams(window.location.search).get("debug") === "smoke";
  } catch {
    return false;
  }
}

export function filterPublicPackages<T extends { id: string }>(packages: T[]): T[] {
  if (showSmokePackageInUi()) return packages;
  return packages.filter((p) => p.id !== "smoke");
}
