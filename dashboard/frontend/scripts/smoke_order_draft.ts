/**
 * Smoke test for A1.1 orderDraft (Node + localStorage polyfill).
 * Run: npx tsx scripts/smoke_order_draft.ts
 */
class MemStorage {
  store = new Map<string, string>();
  getItem(k: string) {
    return this.store.has(k) ? this.store.get(k)! : null;
  }
  setItem(k: string, v: string) {
    this.store.set(k, String(v));
  }
  removeItem(k: string) {
    this.store.delete(k);
  }
  clear() {
    this.store.clear();
  }
  get length() {
    return this.store.size;
  }
  key(i: number) {
    return [...this.store.keys()][i] ?? null;
  }
}

(globalThis as unknown as { window: unknown }).window = globalThis;
(globalThis as unknown as { localStorage: MemStorage }).localStorage = new MemStorage();

async function main() {
  const {
    orderDraftStorageKey,
    isMeaningfulOrderDraft,
    saveOrderDraft,
    loadOrderDraft,
    clearOrderDraft,
    ORDER_DRAFT_VERSION,
  } = await import("../app/lib/orderDraft");

  const market = "DE";
  const vid = "test-visitor-a11";
  clearOrderDraft(market, vid);
  if (loadOrderDraft(market, vid) !== null) throw new Error("expected null");
  const key = orderDraftStorageKey(market, vid);
  if (!key.includes("vc_order_draft_v1:DE:test-visitor-a11")) {
    throw new Error("bad key " + key);
  }
  saveOrderDraft(market, vid, {
    formStep: 2,
    maxReachedStep: 3,
    packageId: "business",
    manualPackage: true,
    brandStyle: "auto",
    businessName: "Mueller Praxis",
    description: "Zahnarzt in Koeln",
    companyWebsite: "",
    city: "Koeln",
    phone: "",
    whatsapp: "",
    email: "a@b.de",
    needsLogo: false,
    needsDomain: false,
    domainStatus: "none",
    existingDomain: "",
    googleBusiness: "",
    instagram: "",
    facebook: "",
    tiktok: "",
    linkedin: "",
    youtube: "",
    telegram: "",
    extraWishes: "",
    niche: "dental",
    specialization: "",
    serviceList: "",
    legalOwner: "",
    legalForm: "",
    legalStreet: "",
    legalZip: "",
    legalCity: "",
    legalDirector: "",
    legalVat: "",
    legalMaps: false,
    legalAnalytics: false,
    materials: [],
    purchaseType: "one_time",
  });
  const loaded = loadOrderDraft(market, vid);
  if (!loaded || loaded.v !== ORDER_DRAFT_VERSION) throw new Error("load failed");
  if (!isMeaningfulOrderDraft(loaded)) throw new Error("not meaningful");
  if (loaded.businessName !== "Mueller Praxis" || loaded.formStep !== 2) {
    throw new Error("fields mismatch");
  }
  if (loaded.maxReachedStep !== 3) throw new Error("maxReachedStep mismatch");
  clearOrderDraft(market, vid);
  if (loadOrderDraft(market, vid) !== null) throw new Error("clear failed");
  console.log("orderDraft A1.1/A1.2 smoke PASS");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
