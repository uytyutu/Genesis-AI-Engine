/**
 * Smoke test for A1.3 orderLiveGuidance (no DOM).
 * Run: npx tsx scripts/smoke_order_live_guidance.ts
 */
import {
  buildOrderLiveGuidance,
  normalizeNicheId,
  progressBars,
  resolveStyleId,
} from "../app/lib/orderLiveGuidance";

function assert(cond: unknown, msg: string): asserts cond {
  if (!cond) throw new Error(msg);
}

const dental = buildOrderLiveGuidance({
  businessName: "Zahnarztpraxis Mueller",
  description: "Prophylaxe und Implantate in Koeln",
  niche: "dental",
  brandStyle: "auto",
  packageId: "business",
  marketCode: "DE",
  city: "Koeln",
  email: "a@b.de",
  phone: "+49 221",
  needsLogo: false,
  hasMaterials: false,
  formStep: 2,
});

assert(normalizeNicheId("dental") === "dental", "niche");
assert(resolveStyleId("auto", "dental") === "modern", "dental default style");
assert(dental.heroHint.includes("Clinic") || dental.heroLayout === "A", "hero");
assert(dental.marketCode === "DE" && dental.languageCode === "de", "market/lang");
assert(dental.previewTitle.includes("Mueller"), "title");
assert(dental.progressFilled >= 4, "progress");
assert(progressBars(2, 6) === "■■□□□□", "bars");

const auto = buildOrderLiveGuidance({
  businessName: "Garage Schmidt",
  description: "",
  niche: "auto",
  brandStyle: "premium",
  packageId: "basic",
  marketCode: "ES",
  city: "",
  email: "",
  phone: "",
  needsLogo: true,
  hasMaterials: false,
  formStep: 1,
});
assert(auto.styleId === "premium", "manual style");
assert(auto.languageCode === "es", "ES lang");
assert(auto.palette.accent === "#d4af37", "premium gold");

console.log("orderLiveGuidance A1.3 smoke PASS");
