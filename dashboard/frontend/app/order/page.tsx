"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { PackageSkeleton } from "../components/Skeleton";
import { formatLocalizedMoney } from "../lib/formatEur";
import { formatApiDetail } from "../lib/formatApiError";
import { startOrderCheckout, fetchPaymentReady } from "../lib/orderCheckout";
import { parseOrderPurchaseType } from "../lib/orderTrustCard";
import { OrderProjectSummary } from "../components/OrderProjectSummary";
import { OrderCheckoutSummary } from "../components/OrderCheckoutSummary";
import { fetchProjectPlatform } from "../lib/projectApi";
import { buildOrderLaunchContext, type OrderLaunchContext } from "../lib/orderProjectLaunch";
import { Badge, Button, ButtonLink, Card, Field, Input, Textarea } from "../components/ui";
import { publicApiBase } from "../lib/publicApiBase";
import { logCommerceEvent } from "../lib/commerceFunnel";
import { uiLangForMarket } from "../lib/marketLang";
import { useLocale } from "../context/LocaleContext";
import type { UiLocale } from "../lib/locale/types";
import { OrderProjectPreview } from "../components/OrderProjectPreview";
import { filterPublicPackages, showSmokePackageInUi } from "../lib/showSmokePackage";
import { parseClientServices } from "../lib/packagePreviewGallery";
import { resolveOrderCoachHints } from "../lib/orderFormCoach";
import { getVisitorId } from "../lib/visitorId";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { companyProfileFromMe } from "../lib/companyProfile";
import {
  clearOrderDraft,
  createDebouncedOrderDraftSaver,
  isMeaningfulOrderDraft,
  loadOrderDraft,
  type OrderDraftPayload,
} from "../lib/orderDraft";
import {
  BusinessInterviewPanel,
  emptyInterview,
  interviewOrderFields,
  type InterviewState,
} from "../components/BusinessInterviewPanel";

const API = publicApiBase();

type Package = {
  id: string;
  name: string;
  price_eur: number;
  deliverables: string[];
  currency?: string;
  symbol?: string;
  market_code?: string;
  price_label?: string;
};

const REPAIR_PACKAGES: Package[] = [
  {
    id: "repair_lite",
    name: "Website Repair Lite",
    price_eur: 199,
    deliverables: [
      "Ремонт по отчёту Website Analysis",
      "Статус в кабинете",
      "Выполняет оператор Virtus Core",
    ],
  },
  {
    id: "repair_standard",
    name: "Website Repair Standard",
    price_eur: 349,
    deliverables: [
      "Расширенный ремонт по анализу",
      "Before/after кратко",
      "Оператор Virtus Core",
    ],
  },
  {
    id: "repair_complete",
    name: "Website Repair Complete",
    price_eur: 499,
    deliverables: [
      "Полный объём согласованных правок",
      "Before/after + остаточные рекомендации",
    ],
  },
];

/** G2.X — standalone services (orderable without a Landing website). */
const ADDON_PACKAGES: Package[] = [
  {
    id: "ai_website_analysis",
    name: "AI Website Analysis",
    price_eur: 149,
    deliverables: ["AI report", "Priorities", "Repair vs new site advice"],
  },
  {
    id: "website_repair",
    name: "Website Repair",
    price_eur: 199,
    deliverables: ["Agreed repair scope", "Cabinet status", "Vector support"],
  },
  {
    id: "seo_audit",
    name: "SEO Audit",
    price_eur: 249,
    deliverables: ["Technical SEO", "Meta / structure", "Action plan"],
  },
  {
    id: "speed_optimization",
    name: "Speed Optimization",
    price_eur: 199,
    deliverables: ["Before/after metrics", "Image & cache fixes"],
  },
  {
    id: "security_check",
    name: "Security Check",
    price_eur: 299,
    deliverables: ["HTTPS & forms review", "Priority report"],
  },
  {
    id: "google_business_setup",
    name: "Google Business Profile Setup",
    price_eur: 149,
    deliverables: ["Profile setup", "Hours / photos / categories"],
  },
  {
    id: "website_migration",
    name: "Website Migration",
    price_eur: 299,
    deliverables: ["Migration plan", "Cutover check"],
  },
];

type CommerceContext = {
  currency: string;
  symbol: string;
  market_code: string;
};

function suggestPackage(needsLogo: boolean, needsDomain: boolean, extra: string): string {
  if (needsDomain) return "premium";
  // Logo-Einbindung allein ist kein Premium-Upsell — nur komplexere Wünsche → Business
  if (extra.trim().length > 120) return "business";
  if (needsLogo) return "business";
  return "basic";
}

export default function OrderSitePage() {
  const { t, i18n } = useTranslation("site");
  const { applyUiLocale } = useLocale();
  const [marketParam, setMarketParam] = useState("");
  const [marketReady, setMarketReady] = useState(false);
  // Guest checkout (Launch Blocker): order form is public — no register redirect.
  useEffect(() => {
    try {
      const p = new URLSearchParams(window.location.search);
      const pkg = (p.get("package") || "").trim();
      const ADDONS = new Set([
        "ai_website_analysis",
        "website_repair",
        "seo_audit",
        "speed_optimization",
        "security_check",
        "google_business_setup",
        "website_migration",
      ]);
      if (ADDONS.has(pkg)) {
        window.location.replace(`/order/service/${pkg}`);
      }
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    try {
      const p = new URLSearchParams(window.location.search);
      setMarketParam((p.get("market") || p.get("country") || "").toUpperCase());
    } catch {
      setMarketParam("");
    } finally {
      setMarketReady(true);
    }
  }, []);
  // Country Desk market → order UI language (packages already currency-synced via API)
  useEffect(() => {
    if (!marketReady) return;
    const market = (marketParam || "DE").toUpperCase();
    const lang = uiLangForMarket(market) as UiLocale;
    applyUiLocale(lang);
    // Win race vs LocaleProvider hydration that re-applies browser "auto" English.
    const t = window.setTimeout(() => applyUiLocale(lang), 0);
    const t2 = window.setTimeout(() => applyUiLocale(lang), 50);
    return () => {
      window.clearTimeout(t);
      window.clearTimeout(t2);
    };
  }, [marketParam, marketReady, applyUiLocale]);
  const launchDeliverables = useMemo(
    () => [t("order.launchD1"), t("order.launchD2"), t("order.launchD3"), t("order.launchD4")],
    [t],
  );
  const [packages, setPackages] = useState<Package[]>([]);
  const [commerce, setCommerce] = useState<CommerceContext>({
    currency: "EUR",
    symbol: "€",
    market_code: "DE",
  });
  const [packagesLoading, setPackagesLoading] = useState(true);
  const [businessName, setBusinessName] = useState("");
  const [projectType, setProjectType] = useState<"website" | "shop" | "ai" | "other">(
    "website",
  );
  const [description, setDescription] = useState("");
  const [companyWebsite, setCompanyWebsite] = useState("");
  const [city, setCity] = useState("");
  const [phone, setPhone] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [email, setEmail] = useState("");
  const [needsLogo, setNeedsLogo] = useState(false);
  const [needsDomain, setNeedsDomain] = useState(false);
  const [domainStatus, setDomainStatus] = useState<"none" | "have_domain" | "need_help">("none");
  const [existingDomain, setExistingDomain] = useState("");
  const [googleBusiness, setGoogleBusiness] = useState("");
  const [instagram, setInstagram] = useState("");
  const [facebook, setFacebook] = useState("");
  const [tiktok, setTiktok] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [youtube, setYoutube] = useState("");
  const [telegram, setTelegram] = useState("");
  const [materials, setMaterials] = useState<
    { id: string; filename: string; size: number; status_de: string; findings: { label_de?: string }[] }[]
  >([]);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [formStep, setFormStep] = useState(1);
  const [maxReachedStep, setMaxReachedStep] = useState(1);
  const [insights, setInsights] = useState<{ checks: { id: string; label_de: string; detail?: string }[]; note_de?: string } | null>(
    null,
  );
  const [insightsBusy, setInsightsBusy] = useState(false);
  const [extraWishes, setExtraWishes] = useState("");
  const [legalOwner, setLegalOwner] = useState("");
  const [legalForm, setLegalForm] = useState("");
  const [legalStreet, setLegalStreet] = useState("");
  const [legalZip, setLegalZip] = useState("");
  const [legalCity, setLegalCity] = useState("");
  const [legalDirector, setLegalDirector] = useState("");
  const [legalVat, setLegalVat] = useState("");
  const [legalMaps, setLegalMaps] = useState(false);
  const [legalAnalytics, setLegalAnalytics] = useState(false);
  const [niche, setNiche] = useState("generic");
  const [specialization, setSpecialization] = useState("");
  const [nicheOptions, setNicheOptions] = useState<{ id: string; label_de: string }[]>([]);
  const [specOptions, setSpecOptions] = useState<{ id: string; niche?: string; label: string }[]>(
    [],
  );
  const [packageId, setPackageId] = useState("business");
  const [interview, setInterview] = useState<InterviewState>(() => emptyInterview());
  const [serviceList, setServiceList] = useState("");
  const [brandStyle, setBrandStyle] = useState("auto");
  const [manualPackage, setManualPackage] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState<{
    order_id: string;
    message: string;
    package_name: string;
    price_eur: number;
    deliverables: string[];
    currency?: string;
    price_label?: string;
    buyer_insights?: { checks?: { id: string; label_de: string; detail?: string }[]; note_de?: string } | null;
    demo?: boolean;
    demo_payment_available?: boolean;
    demo_payment_banner?: string | null;
  } | null>(null);
  const [payBusy, setPayBusy] = useState(false);
  const [payError, setPayError] = useState("");
  const [checkoutConfirmed, setCheckoutConfirmed] = useState(false);
  const [paymentReady, setPaymentReady] = useState(false);
  const [purchaseType, setPurchaseType] = useState<"one_time" | "subscription">("one_time");
  const [visitorId, setVisitorId] = useState<string | null>(null);
  const [launch, setLaunch] = useState<OrderLaunchContext | null>(null);
  const [launchLoading, setLaunchLoading] = useState(false);
  const [draftBanner, setDraftBanner] = useState(false);
  const [draftReady, setDraftReady] = useState(false);
  const draftSaverRef = useRef(createDebouncedOrderDraftSaver(400));
  const urlPackageRef = useRef<string | null>(null);
  const urlNicheRef = useRef<string | null>(null);
  const urlProjectTypeRef = useRef<"website" | "shop" | "ai" | "other" | null>(null);
  const urlPackageHydratedRef = useRef(false);
  const analysisCaseRef = useRef<string | null>(null);
  const orderStartedRef = useRef(false);
  const checkoutSummaryViewedRef = useRef(false);
  const checkoutConfirmedLoggedRef = useRef(false);
  const [ownerDemo, setOwnerDemo] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const pkg = params.get("package");
    const intent = (params.get("intent") || "").toLowerCase();
    // Bot orders use a dedicated wizard — never the website form.
    if (intent === "bot" || (pkg && pkg.toLowerCase().startsWith("bot_"))) {
      window.location.replace(`/order/bot?${params.toString()}`);
      return;
    }
    if (
      pkg &&
      [
        "standalone",
        "connected",
        "basic",
        "business",
        "premium",
        "repair_lite",
        "repair_standard",
        "repair_complete",
      ].includes(pkg)
    ) {
      // Public ladder is basic/business/premium; old Standalone/Connected → Business/Premium
      const mapped =
        pkg === "standalone" ? "business" : pkg === "connected" ? "premium" : pkg;
      setPackageId(mapped);
      setManualPackage(true);
      urlPackageRef.current = mapped;
    } else if (pkg === "smoke" && showSmokePackageInUi()) {
      setPackageId("smoke");
      setManualPackage(true);
      urlPackageRef.current = "smoke";
    }
    const n = params.get("niche")?.trim();
    if (n) {
      setNiche(n);
      urlNicheRef.current = n;
    }
    const projectParam = (
      params.get("project_type") ||
      params.get("type") ||
      params.get("project") ||
      ""
    ).toLowerCase();
    if (
      projectParam === "shop" ||
      projectParam === "store" ||
      projectParam === "ecommerce_shop"
    ) {
      setProjectType("shop");
      urlProjectTypeRef.current = "shop";
    } else if (
      projectParam === "ai" ||
      projectParam === "bot" ||
      projectParam === "ai_assistant"
    ) {
      setProjectType("ai");
      urlProjectTypeRef.current = "ai";
    } else if (projectParam === "other" || projectParam === "sonstiges") {
      setProjectType("other");
      urlProjectTypeRef.current = "other";
    } else if (projectParam === "website") {
      setProjectType("website");
      urlProjectTypeRef.current = "website";
    }
    const ac = params.get("analysis_case")?.trim();
    if (ac) analysisCaseRef.current = ac;
    setPurchaseType(parseOrderPurchaseType(params.get("purchase_type")));
    const vid = params.get("visitor_id")?.trim();
    setVisitorId(vid || getVisitorId("public"));
    // Owner walkthrough: ?demo=1 → skip real pay, Factory generates after Demo Payment
    const demoFlag =
      params.get("demo") === "1" ||
      params.get("owner_demo") === "1" ||
      params.get("payment") === "demo";
    if (demoFlag) {
      setOwnerDemo(true);
      // Prefill so tag works even if bridge needs name/email cues
      setBusinessName((prev) => prev || "Golden Website Test Nordlicht");
      setEmail((prev) => prev || "golden.owner@example.com");
      if (!params.get("package")) {
        setPackageId("premium");
        setManualPackage(true);
      }
    }
    logCommerceEvent("tier_page_view", pkg, "order");
    if (!orderStartedRef.current) {
      orderStartedRef.current = true;
      logCommerceEvent("order_started", pkg, "order", {
        niche: n || undefined,
        mode: "order_experience_v2",
      });
    }
  }, []);

  // Restore Path A order draft once visitor + market URL are known (URL package/niche win).
  useEffect(() => {
    if (!visitorId || !marketReady || draftReady) return;
    // Owner demo walkthrough: do not overwrite demo prefill with an old draft
    if (ownerDemo) {
      setDraftReady(true);
      return;
    }
    const market = (marketParam || commerce.market_code || "DE").toUpperCase();
    const draft = loadOrderDraft(market, visitorId);
    if (isMeaningfulOrderDraft(draft) && draft) {
      applyOrderDraft(draft);
      if (urlPackageRef.current) {
        setPackageId(urlPackageRef.current);
        setManualPackage(true);
      }
      if (urlNicheRef.current) setNiche(urlNicheRef.current);
      if (urlProjectTypeRef.current) setProjectType(urlProjectTypeRef.current);
      setDraftBanner(true);
      logCommerceEvent("draft_restored", draft.packageId || urlPackageRef.current, "order", {
        form_step: draft.formStep,
        niche: draft.niche || urlNicheRef.current || undefined,
        market_code: market,
        mode: "order_experience_v2",
      });
    }
    setDraftReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- hydrate once per visitor/market
  }, [visitorId, marketReady, marketParam, commerce.market_code, draftReady, ownerDemo]);

  function applyOrderDraft(d: OrderDraftPayload) {
    const step = Math.min(4, Math.max(1, Math.floor(d.formStep) || 1));
    const maxR = Math.min(
      4,
      Math.max(step, Math.floor(d.maxReachedStep || step) || step),
    );
    setFormStep(step);
    setMaxReachedStep(maxR);
    setPackageId(d.packageId || "basic");
    setManualPackage(Boolean(d.manualPackage));
    setBrandStyle(d.brandStyle || "auto");
    setProjectType(
      d.projectType === "shop" || d.projectType === "ai" || d.projectType === "other"
        ? d.projectType
        : "website",
    );
    setBusinessName(d.businessName || "");
    setDescription(d.description || "");
    setCompanyWebsite(d.companyWebsite || "");
    setCity(d.city || "");
    setPhone(d.phone || "");
    setWhatsapp(d.whatsapp || "");
    setEmail(d.email || "");
    setNeedsLogo(Boolean(d.needsLogo));
    setNeedsDomain(Boolean(d.needsDomain));
    setDomainStatus(d.domainStatus || "none");
    setExistingDomain(d.existingDomain || "");
    setGoogleBusiness(d.googleBusiness || "");
    setInstagram(d.instagram || "");
    setFacebook(d.facebook || "");
    setTiktok(d.tiktok || "");
    setLinkedin(d.linkedin || "");
    setYoutube(d.youtube || "");
    setTelegram(d.telegram || "");
    setExtraWishes(d.extraWishes || "");
    setNiche(d.niche || "generic");
    setSpecialization(d.specialization || "");
    setServiceList(d.serviceList || "");
    setLegalOwner(d.legalOwner || "");
    setLegalForm(d.legalForm || "");
    setLegalStreet(d.legalStreet || "");
    setLegalZip(d.legalZip || "");
    setLegalCity(d.legalCity || "");
    setLegalDirector(d.legalDirector || "");
    setLegalVat(d.legalVat || "");
    setLegalMaps(Boolean(d.legalMaps));
    setLegalAnalytics(Boolean(d.legalAnalytics));
    setMaterials(Array.isArray(d.materials) ? d.materials : []);
    if (d.purchaseType === "subscription" || d.purchaseType === "one_time") {
      setPurchaseType(d.purchaseType);
    }
  }

  function startOverDraft() {
    const market = (marketParam || commerce.market_code || "DE").toUpperCase();
    draftSaverRef.current.cancel();
    clearOrderDraft(market, visitorId);
    setDraftBanner(false);
    setFormStep(1);
    setMaxReachedStep(1);
    setProjectType(urlProjectTypeRef.current || "website");
    setBusinessName("");
    setDescription("");
    setCompanyWebsite("");
    setCity("");
    setPhone("");
    setWhatsapp("");
    setEmail("");
    setNeedsLogo(false);
    setNeedsDomain(false);
    setDomainStatus("none");
    setExistingDomain("");
    setGoogleBusiness("");
    setInstagram("");
    setFacebook("");
    setTiktok("");
    setLinkedin("");
    setYoutube("");
    setTelegram("");
    setExtraWishes("");
    setNiche(urlNicheRef.current || "generic");
    setSpecialization("");
    setServiceList("");
    setLegalOwner("");
    setLegalForm("");
    setLegalStreet("");
    setLegalZip("");
    setLegalCity("");
    setLegalDirector("");
    setLegalVat("");
    setLegalMaps(false);
    setLegalAnalytics(false);
    setMaterials([]);
    setBrandStyle("auto");
    setManualPackage(Boolean(urlPackageRef.current));
    setPackageId(urlPackageRef.current || "basic");
    setInsights(null);
    setError("");
  }

  useEffect(() => {
    if (!draftReady || !visitorId || done) return;
    const market = (marketParam || commerce.market_code || "DE").toUpperCase();
    draftSaverRef.current.schedule(market, visitorId, {
      formStep,
      maxReachedStep,
      packageId,
      manualPackage,
      brandStyle,
      projectType,
      businessName,
      description,
      companyWebsite,
      city,
      phone,
      whatsapp,
      email,
      needsLogo,
      needsDomain,
      domainStatus,
      existingDomain,
      googleBusiness,
      instagram,
      facebook,
      tiktok,
      linkedin,
      youtube,
      telegram,
      extraWishes,
      niche,
      specialization,
      serviceList,
      legalOwner,
      legalForm,
      legalStreet,
      legalZip,
      legalCity,
      legalDirector,
      legalVat,
      legalMaps,
      legalAnalytics,
      materials,
      purchaseType,
    });
  }, [
    draftReady,
    visitorId,
    done,
    marketParam,
    commerce.market_code,
    formStep,
    maxReachedStep,
    packageId,
    manualPackage,
    brandStyle,
    projectType,
    businessName,
    description,
    companyWebsite,
    city,
    phone,
    whatsapp,
    email,
    needsLogo,
    needsDomain,
    domainStatus,
    existingDomain,
    googleBusiness,
    instagram,
    facebook,
    tiktok,
    linkedin,
    youtube,
    telegram,
    extraWishes,
    niche,
    specialization,
    serviceList,
    legalOwner,
    legalForm,
    legalStreet,
    legalZip,
    legalCity,
    legalDirector,
    legalVat,
    legalMaps,
    legalAnalytics,
    materials,
    purchaseType,
  ]);

  useEffect(() => {
    const saver = draftSaverRef.current;
    return () => {
      saver.flush();
      saver.cancel();
    };
  }, []);

  useEffect(() => {
    if (!visitorId) return;
    // Storefront /order is always the brief form. Launch checkout only when
    // Vector explicitly sends the buyer with ?launch=1 (never auto from visitor project).
    let wantLaunch = false;
    try {
      const p = new URLSearchParams(window.location.search);
      wantLaunch =
        p.get("launch") === "1" ||
        p.get("from") === "vector" ||
        p.get("from") === "project";
      if (p.get("form") === "1") wantLaunch = false;
    } catch {
      wantLaunch = false;
    }
    if (!wantLaunch) {
      setLaunch(null);
      setLaunchLoading(false);
      return;
    }
    let cancelled = false;
    setLaunchLoading(true);
    fetchProjectPlatform(visitorId)
      .then((state) => {
        if (cancelled) return;
        const ctx = buildOrderLaunchContext(state);
        setLaunch(ctx);
        if (ctx) {
          setBusinessName(ctx.company);
          setDescription(ctx.description);
          if (ctx.logoResolved) setNeedsLogo(false);
        }
      })
      .finally(() => {
        if (!cancelled) setLaunchLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [visitorId]);

  useEffect(() => {
    fetch(`${API}/api/public/niches`)
      .then((res) => (res.ok ? res.json() : null))
      .then((body) => {
        if (Array.isArray(body?.niches)) {
          setNicheOptions(
            body.niches.filter(
              (n: { id?: string; label_de?: string }) => {
                const id = String(n?.id || "").toLowerCase();
                const label = String(n?.label_de || "").toLowerCase();
                return (
                  !id.includes("family") &&
                  !label.includes("familien") &&
                  !id.includes("psycholog") &&
                  !label.includes("psycholog") &&
                  id !== "family_psychology" &&
                  id !== "family_care"
                );
              },
            ),
          );
        }
        if (Array.isArray(body?.specializations)) setSpecOptions(body.specializations);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    void fetchPaymentReady().then((ready) => {
      if (!cancelled) setPaymentReady(ready);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Reuse company profile for logged-in clients (same public prices — no Workspace discount).
  useEffect(() => {
    if (!getClientToken()) return;
    let cancelled = false;
    fetch(`${API}/api/client/me`, {
      headers: { ...clientAuthHeaders() },
      cache: "no-store",
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((me) => {
        if (cancelled || !me) return;
        const profile = companyProfileFromMe(me);
        if (profile.company_name) {
          setBusinessName((prev) => prev || profile.company_name);
        }
        if (profile.email) {
          setEmail((prev) => prev || profile.email);
        }
        if (profile.phone) {
          setPhone((prev) => prev || profile.phone);
        }
        if (profile.primary_niche) {
          setNiche((prev) =>
            !prev || prev === "generic" ? profile.primary_niche : prev,
          );
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams();
      if (visitorId) params.set("visitor_id", visitorId);
      if (city.trim()) params.set("city", city.trim());
      if (description.trim()) params.set("text", description.trim());
      if (marketParam) params.set("market", marketParam);
      const qs = params.toString();
      const load = async () => {
        let lastFail = false;
        for (let i = 0; i < 4; i++) {
          try {
            const res = await fetch(`${API}/api/sales/packages${qs ? `?${qs}` : ""}`);
            if (res.status >= 500 && i < 3) {
              await new Promise((r) => setTimeout(r, 400 * (i + 1)));
              continue;
            }
            const body = await res.json();
            setPackages(filterPublicPackages(body.packages ?? []));
            setCommerce({
              currency: body.currency ?? "EUR",
              symbol: body.symbol ?? "€",
              market_code: body.market_code ?? "DE",
            });
            lastFail = false;
            break;
          } catch {
            lastFail = true;
            if (i < 3) await new Promise((r) => setTimeout(r, 400 * (i + 1)));
          }
        }
        if (lastFail) setPackages([]);
        setPackagesLoading(false);
      };
      void load();
    }, 300);
    return () => window.clearTimeout(timer);
  }, [visitorId, city, description, marketParam]);

  const suggestedId = useMemo(
    () =>
      suggestPackage(
        needsLogo,
        needsDomain || domainStatus === "need_help",
        extraWishes,
      ),
    [needsLogo, needsDomain, domainStatus, extraWishes],
  );

  useEffect(() => {
    if (!manualPackage) setPackageId(suggestedId);
  }, [suggestedId, manualPackage]);

  useEffect(() => {
    if (!packages.length) return;
    // Hydrate URL package once — later radio clicks must stick even if catalog reloads.
    const fromUrl = urlPackageRef.current;
    if (
      fromUrl &&
      !urlPackageHydratedRef.current &&
      packages.some((p) => p.id === fromUrl)
    ) {
      setPackageId(fromUrl);
      setManualPackage(true);
      urlPackageHydratedRef.current = true;
      return;
    }
    if (!packages.some((p) => p.id === packageId)) {
      const fallback =
        packages.find((p) => p.id === "business")?.id ||
        packages.find((p) => p.id === "premium")?.id ||
        packages[0]!.id;
      setPackageId(fallback);
    }
    // Intentionally depend only on `packages` so manual radio changes stick.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [packages]);

  useEffect(() => {
    if (domainStatus === "need_help" || domainStatus === "none") {
      setNeedsDomain(domainStatus === "need_help");
    } else {
      setNeedsDomain(false);
    }
  }, [domainStatus]);

  const formatPrice = (
    amount: number,
    pkg?: { currency?: string; price_label?: string }
  ) =>
    pkg?.price_label ??
    formatLocalizedMoney(amount, pkg?.currency ?? commerce.currency);

  const displayPackages = useMemo(() => {
    const repair = REPAIR_PACKAGES.find((p) => p.id === packageId);
    const addon = ADDON_PACKAGES.find((p) => p.id === packageId);
    const extra = [repair, addon].filter(Boolean) as Package[];
    let list = packages;
    for (const row of extra) {
      if (!list.some((p) => p.id === row.id)) {
        list = [row, ...list];
      }
    }
    return list;
  }, [packages, packageId]);
  const selected = displayPackages.find((p) => p.id === packageId) ?? displayPackages[0];
  // Business + Premium share presentation quality; Premium adds depth/control (no +99 add-on).
  const presentationIncluded =
    (packageId || "").toLowerCase() === "business" ||
    (packageId || "").toLowerCase() === "standalone" ||
    (packageId || "").toLowerCase() === "premium" ||
    (packageId || "").toLowerCase() === "connected";
  const orderTotalEur = selected?.price_eur || 0;
  const packagePriceBullet = useMemo(() => {
    const tiers = ["basic", "business", "premium"]
      .map((id) => packages.find((p) => p.id === id))
      .filter(Boolean) as Package[];
    if (tiers.length === 0) return t("order.bulletPkg");
    return tiers
      .map((p) => {
        const label = (p.name || p.id).replace(/^Landing\s+/i, "");
        return `${label} ${p.price_label || formatPrice(p.price_eur, p)}`;
      })
      .join(" · ");
  }, [packages, commerce.currency, t]);

  const selectedPackageBenefits = useMemo(() => {
    const id = (packageId || "").toLowerCase();
    if (id === "premium" || id === "connected") {
      return [
        "Alles aus Business — gleiche visuelle Qualität",
        "Responsive + Mobile",
        "Kontaktformular & Legal-Seiten",
        "SEO-Grundlage",
        "Virtus Workspace",
        "Erweiterte Website-Steuerung",
        "Tiefere Seitenstruktur",
        "Erweiterte Formulare & Content",
        "Fortgeschrittenes Management",
        "Analytics",
        "Versionen & Wiederherstellung",
        "Übergabe als fertiges Projekt",
      ];
    }
    if (id === "business" || id === "standalone") {
      return [
        "Fertige Website für Ihre Branche",
        "Responsive + Mobile",
        "Kontaktformular & Legal-Seiten",
        "SEO-Grundlage",
        "Virtus Workspace",
        "Hochwertige Präsentation wie in den Business-Beispielen",
        "Texte, Bilder und Kontakte selbst bearbeiten",
        "Analytics",
        "Versionen & Wiederherstellung",
        "Übergabe als fertiges Projekt",
      ];
    }
    return [
      "Fertige Website für Ihre Branche",
      "Responsive + Mobile",
      "Kontaktformular & Legal-Seiten",
      "SEO-Grundlage",
      "Standard-Medien & Kontakte",
      "Übergabe als fertiges Projekt",
      "Keine Virtus-Verwaltung",
    ];
  }, [packageId]);

  const afterPayBullet = useMemo(() => {
    const id = (packageId || "").toLowerCase();
    if (id === "business" || id === "premium" || id === "connected" || id === "standalone") {
      return t("order.bulletAfterPayWorkspace", {
        defaultValue:
          "Nach Zahlung erhalten Sie Ihr Projekt, den Status Ihrer Bestellung und Zugang zum Virtus Workspace.",
      });
    }
    return t("order.bulletAfterPayBasic", {
      defaultValue:
        "Nach Zahlung erhalten Sie die fertigen Website-Dateien und den Status Ihrer Bestellung.",
    });
  }, [packageId, t]);
  const coachHints = useMemo(
    () =>
      resolveOrderCoachHints({
        formStep,
        businessName,
        email,
        description,
        city,
        phone,
        niche,
        companyWebsite,
        packageId,
        serviceList,
        domainStatus,
        existingDomain,
      }),
    [
      formStep,
      businessName,
      email,
      description,
      city,
      phone,
      niche,
      companyWebsite,
      packageId,
      serviceList,
      domainStatus,
      existingDomain,
    ],
  );

  async function uploadMaterials(files: FileList | null) {
    if (!files?.length) return;
    setUploadBusy(true);
    setUploadError("");
    try {
      const seenKeys = new Set(
        materials.map((m) => `${m.filename.toLowerCase()}:${m.size}`),
      );
      for (const file of Array.from(files)) {
        const dedupeKey = `${file.name.toLowerCase()}:${file.size}`;
        // Same name+size already in the list — skip re-upload (double change / re-select).
        if (seenKeys.has(dedupeKey)) continue;
        seenKeys.add(dedupeKey);

        const fd = new FormData();
        fd.append("file", file);
        const res = await fetch(
          `${API}/api/sales/order-materials?session_id=${encodeURIComponent(visitorId || "anon")}`,
          { method: "POST", body: fd },
        );
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          setUploadError(formatApiDetail(body.detail) || t("order.uploadFail"));
          continue;
        }
        setMaterials((prev) => {
          if (prev.some((m) => m.id === body.id)) return prev;
          if (prev.some((m) => m.filename.toLowerCase() === String(body.filename || "").toLowerCase() && m.size === body.size)) {
            return prev;
          }
          return [
            ...prev,
            {
              id: body.id,
              filename: body.filename,
              size: body.size,
              status_de: body.status_de,
              findings: body.findings || [],
            },
          ];
        });
      }
    } catch {
      setUploadError(t("order.serverDown"));
    } finally {
      setUploadBusy(false);
    }
  }

  async function loadInsightsPreview() {
    setInsightsBusy(true);
    try {
      const res = await fetch(`${API}/api/sales/order-insights-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_website: companyWebsite.trim() || null,
          domain_status: domainStatus,
          existing_domain: existingDomain.trim() || null,
          google_business: googleBusiness.trim() || null,
          instagram: instagram.trim() || null,
          facebook: facebook.trim() || null,
          tiktok: tiktok.trim() || null,
          linkedin: linkedin.trim() || null,
          youtube: youtube.trim() || null,
          telegram: telegram.trim() || null,
          whatsapp: whatsapp.trim() || null,
          material_ids: materials.map((m) => m.id),
          niche: niche || null,
          specialization: specialization.trim() || null,
          package_id: packageId,
          services_list: parseClientServices(serviceList),
          city: city.trim() || null,
        }),
      });
      const body = await res.json();
      if (res.ok) {
        setInsights({ checks: body.checks || [], note_de: body.note_de });
      }
    } catch {
      /* preview optional — order still works */
    } finally {
      setInsightsBusy(false);
    }
  }

  function canAdvance(step: number): boolean {
    if (step === 1) {
      if (!businessName.trim()) {
        setError(t("order.coachNeedBusiness"));
        return false;
      }
      if (!description.trim() || description.trim().length < 8) {
        setError(t("order.coachNeedDescription"));
        return false;
      }
    }
    if (step === 3 && domainStatus === "have_domain" && !existingDomain.trim()) {
      setError(t("order.coachNeedDomainName"));
      return false;
    }
    setError("");
    return true;
  }

  async function goNext() {
    if (!canAdvance(formStep)) return;
    const completed = formStep;
    const next = Math.min(4, formStep + 1);
    setFormStep(next);
    setMaxReachedStep((m) => Math.max(m, next));
    const stepEvent =
      completed === 1
        ? "step_1_completed"
        : completed === 2
          ? "step_2_completed"
          : completed === 3
            ? "step_3_completed"
            : null;
    if (stepEvent) {
      logCommerceEvent(stepEvent, packageId, "order", {
        form_step: completed,
        niche: niche || undefined,
        mode: "order_experience_v2",
      });
    }
    if (next === 2) await loadInsightsPreview();
  }

  function goBack() {
    setError("");
    setFormStep((s) => Math.max(1, s - 1));
  }

  function goToStep(step: number) {
    const target = Math.min(4, Math.max(1, Math.floor(step)));
    if (target > maxReachedStep) return;
    setError("");
    setFormStep(target);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      setError(t("order.emailRequired"));
      return;
    }
    if (!launch && formStep < 4) {
      await goNext();
      return;
    }
    setBusy(true);
    setError("");
    try {
      let customerId: string | null = null;
      try {
        const meRes = await fetch(`${API}/api/client/me`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        });
        if (meRes.ok) {
          const me = await meRes.json();
          customerId =
            String(me?.customer_id || me?.account?.customer_id || "").trim() || null;
        }
      } catch {
        /* guest fallback — register gate should already run */
      }
      const res = await fetch(`${API}/api/sales/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...clientAuthHeaders() },
        body: JSON.stringify({
          business_name: businessName.trim() || launch?.company || "Projekt",
          description: [
            projectType === "shop"
              ? "[Online-Shop]"
              : projectType === "ai"
                ? "[AI Assistant]"
                : projectType === "other"
                  ? "[Projekt]"
                  : "[Website]",
            description.trim() || launch?.projectLabel || "Website Launch",
            interview.dialogue ? `\n\n[Owner story]\n${interview.dialogue}` : "",
          ]
            .filter(Boolean)
            .join(" "),
          project_type: projectType,
          city: city.trim() || interview.city || null,
          phone: phone.trim() || null,
          whatsapp: whatsapp.trim() || null,
          email: email.trim() || null,
          customer_id: customerId,
          commerce_mode:
            packageId === "connected" || packageId === "premium"
              ? "connected"
              : "standalone",
          ...interviewOrderFields({
            ...interview,
            company_name: interview.company_name || businessName.trim(),
            city: interview.city || city.trim(),
            niche: interview.niche || niche,
            top_services: interview.top_services || serviceList,
            style: interview.style || brandStyle || "modern",
            wishes: interview.wishes || extraWishes,
          }),
          needs_logo: needsLogo,
          needs_domain: needsDomain || domainStatus === "need_help",
          domain_status: domainStatus,
          existing_domain: existingDomain.trim() || null,
          google_business: googleBusiness.trim() || null,
          instagram: instagram.trim() || null,
          facebook: facebook.trim() || null,
          tiktok: tiktok.trim() || null,
          linkedin: linkedin.trim() || null,
          youtube: youtube.trim() || null,
          telegram: telegram.trim() || null,
          material_ids: materials.map((m) => m.id),
          extra_wishes: extraWishes.trim() || null,
          company_website: companyWebsite.trim() || null,
          client_legal: {
            owner_name: legalOwner.trim() || businessName.trim() || null,
            legal_form: legalForm.trim() || null,
            street: legalStreet.trim() || null,
            zip: legalZip.trim() || null,
            city: legalCity.trim() || city.trim() || null,
            country: "DE",
            email: email.trim() || null,
            phone: phone.trim() || null,
            managing_director: legalDirector.trim() || null,
            vat_id: legalVat.trim() || null,
            uses_maps: legalMaps,
            uses_analytics: legalAnalytics,
          },
          package_id: packageId,
          // Business package owns presentation quality — not a +99 € add-on, not Premium USP.
          cinematic_enabled: presentationIncluded,
          analysis_case_id: analysisCaseRef.current || null,
          brand_style: brandStyle || "auto",
          niche: niche || null,
          specialization: specialization.trim() || null,
          services_list: parseClientServices(serviceList),
          market_code: commerce.market_code || marketParam || undefined,
          ui_lang: (i18n.language || "").slice(0, 2).toLowerCase() || undefined,
          visitor_id: visitorId,
          ...(ownerDemo
            ? { demo: true, payment_mode: "demo", is_demo: true }
            : {}),
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(formatApiDetail(body.detail) || t("order.submitFail"));
        return;
      }
      setDone({
        order_id: body.order_id,
        message: body.message,
        package_name: body.package_name,
        price_eur: body.price_eur,
        deliverables: body.deliverables ?? [],
        currency: body.currency ?? commerce.currency,
        price_label: body.price_label,
        buyer_insights: body.buyer_insights ?? insights,
        demo: Boolean(body.demo),
        demo_payment_available: Boolean(
          body.demo_payment_available || (body.demo && body.payment_mode === "demo"),
        ),
        demo_payment_banner: body.demo_payment_banner ?? null,
      });
      if (
        body.demo_payment_available ||
        (body.demo && body.payment_mode === "demo")
      ) {
        setPaymentReady(true);
      }
      draftSaverRef.current.cancel();
      clearOrderDraft(
        (marketParam || commerce.market_code || "DE").toUpperCase(),
        visitorId,
      );
      setDraftBanner(false);
      logCommerceEvent("tier_select", packageId, "order", {
        niche,
        specialization: specialization || null,
        order_id: body.order_id,
      });
      logCommerceEvent("step_4_completed", packageId, "order", {
        niche: niche || undefined,
        order_id: body.order_id,
        form_step: 4,
        mode: "order_experience_v2",
      });
    } catch {
      setError(t("order.serverDown"));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!done?.order_id || checkoutSummaryViewedRef.current) return;
    checkoutSummaryViewedRef.current = true;
    logCommerceEvent("checkout_summary_viewed", packageId, "order", {
      order_id: done.order_id,
      niche: niche || undefined,
      mode: "order_experience_v2",
    });
  }, [done, packageId, niche]);

  useEffect(() => {
    if (!done?.order_id || !checkoutConfirmed || checkoutConfirmedLoggedRef.current) return;
    checkoutConfirmedLoggedRef.current = true;
    logCommerceEvent("checkout_confirmed", packageId, "order", {
      order_id: done.order_id,
      niche: niche || undefined,
      mode: "order_experience_v2",
    });
  }, [checkoutConfirmed, done, packageId, niche]);

  async function payNow() {
    if (!done || !checkoutConfirmed) return;
    setPayBusy(true);
    setPayError("");
    try {
      if (done.demo_payment_available) {
        const res = await fetch(`${API}/api/sales/orders/${done.order_id}/pay-demo`, {
          method: "POST",
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          setPayError(
            typeof body.detail === "string"
              ? body.detail
              : t("order.serverDown"),
          );
          setPayBusy(false);
          return;
        }
        window.location.href = `/order/status/${done.order_id}?paid=1&demo=1`;
        return;
      }
      const url = await startOrderCheckout(done.order_id);
      window.location.href = url;
    } catch (e) {
      setPayError(e instanceof Error ? e.message : t("order.serverDown"));
      setPayBusy(false);
    }
  }

  if (done) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-2xl py-4">
          <OrderSteps current={paymentReady ? 3 : 2} launch={Boolean(launch)} />
          <OrderCheckoutSummary
            orderId={done.order_id}
            message={done.message}
            businessName={businessName.trim() || launch?.company || done.package_name}
            niche={niche}
            marketCode={marketParam || commerce.market_code || "DE"}
            packageName={done.package_name}
            packageId={packageId}
            priceLabel={formatPrice(done.price_eur, done)}
            deliverables={
              launch && done.deliverables.length === 0 ? launchDeliverables : done.deliverables
            }
            purchaseType={purchaseType}
            paymentReady={paymentReady}
            confirmed={checkoutConfirmed}
            onConfirmedChange={setCheckoutConfirmed}
            payBusy={payBusy}
            payError={payError}
            onPay={() => void payNow()}
            launch={Boolean(launch)}
            demoPaymentAvailable={Boolean(done.demo_payment_available)}
            demoPaymentBanner={done.demo_payment_banner}
          />
          <div className="mt-4 text-center">
            <ButtonLink
              href={`/order/status/${done.order_id}`}
              variant="ghost"
              size="sm"
            >
              {t("order.trackStatus")}
            </ButtonLink>
          </div>
        </main>
      </PublicPageShell>
    );
  }

  return (
    <PublicPageShell>
      <main className="storefront relative z-[1] mx-auto max-w-4xl space-y-5 overflow-x-hidden py-2 sm:space-y-6">
        {ownerDemo ? (
          <div
            className="rounded-lg border border-amber-400/40 bg-amber-500/15 px-4 py-3 text-sm text-amber-50"
            role="status"
          >
            <strong className="font-semibold">Owner Demo</strong>
            {" — "}
            Оплата пропускается (Demo Payment). Заполните бриф как клиент → подтвердите →
            сайт сгенерируется Factory. Сравните с{" "}
            <Link href="/site" className="underline underline-offset-2">
              /site
            </Link>
            {" "}(Virtus Core bar).
          </div>
        ) : null}
        <OrderSteps current={1} launch={Boolean(launch)} />
        <div className="mb-2 text-center animate-fade-up">
          <Badge variant="accent" className="tracking-[0.2em]">
            {t("order.badge")}
          </Badge>
          <h1 className="mt-3 text-2xl font-bold leading-tight text-white sm:text-4xl">
            {launch ? t("order.titleLaunch") : t("order.titleHero")}
          </h1>
          <p className="mx-auto mt-2 max-w-2xl text-sm text-zinc-300 sm:text-base">
            {launch ? t("order.subtitleLaunch") : t("order.subtitleHero")}
          </p>
          {!launch ? (
            <ul className="mx-auto mt-4 max-w-lg space-y-1 text-left text-sm text-white/75">
              <li>• {packagePriceBullet}</li>
              <li>• {afterPayBullet}</li>
              <li>• {t("order.bulletSorglos")}</li>
            </ul>
          ) : null}
          {!launch ? (
            <ul className="mx-auto mt-4 flex max-w-xl flex-wrap justify-center gap-2 text-xs">
              {[t("pathA.benefitMobile"), t("pathA.benefitSeo"), t("pathA.benefitSpeed")].map(
                (label) => (
                  <li
                    key={label}
                    className="rounded-full border border-violet-400/35 bg-violet-950/35 px-3 py-1 text-violet-100/90"
                  >
                    ✓ {label}
                  </li>
                ),
              )}
            </ul>
          ) : null}
        </div>

        {launch ? (
          <OrderProjectSummary launch={launch} packageId={packageId} niche={niche} />
        ) : null}
        {launchLoading && !launch ? (
          <p className="mb-6 text-center text-sm text-genesis-muted">{t("order.loadingProject")}</p>
        ) : null}

        <form onSubmit={submit} className={`grid gap-6 lg:grid-cols-5 ${launch ? "mt-6" : ""}`}>
          <div className="storefront-module-card order-virtus-form space-y-4 rounded-3xl border border-white/12 bg-[#0b1018]/85 p-4 shadow-[0_0_48px_-24px_rgba(91,141,239,0.35)] backdrop-blur-sm sm:p-5 lg:col-span-3 [&_.genesis-label]:text-zinc-100 [&_input]:border-white/15 [&_input]:bg-black/40 [&_input]:text-white [&_input]:placeholder:text-zinc-500 [&_textarea]:border-white/15 [&_textarea]:bg-black/40 [&_textarea]:text-white [&_textarea]:placeholder:text-zinc-500">
            <div className="rounded-2xl border border-emerald-400/30 bg-emerald-950/30 px-3.5 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-200/90">
                {t("order.whyFormBadge")}
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-zinc-100">
                {t("order.whyFormBody")}
              </p>
            </div>
            {!launch ? (
              <>
                <FormStepBar
                  current={formStep}
                  maxReached={maxReachedStep}
                  onSelectStep={goToStep}
                />
                {draftBanner ? (
                  <div
                    className="flex flex-col gap-2 rounded-2xl border border-violet-400/25 bg-violet-950/20 px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between"
                    role="status"
                  >
                    <div className="min-w-0">
                      <p className="text-sm text-white">{t("order.draftRestored")}</p>
                      <p className="mt-0.5 text-xs text-genesis-muted">{t("order.draftSavedHint")}</p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      className="shrink-0 self-start sm:self-auto"
                      onClick={startOverDraft}
                    >
                      {t("order.draftStartOver")}
                    </Button>
                  </div>
                ) : draftReady ? (
                  <p className="text-xs text-genesis-muted">{t("order.draftSavedHint")}</p>
                ) : null}
                <OrderCoachPanel hints={coachHints} />
                {formStep === 1 && (
                  <>
                    <div>
                      <p className="mb-2 text-sm font-medium text-white">
                        {t("order.projectTypeTitle")}
                      </p>
                      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                        {(
                          [
                            [
                              "website",
                              "order.projectTypeWebsite",
                              "order.projectTypeWebsiteHint",
                            ],
                            [
                              "shop",
                              "order.projectTypeShop",
                              "order.projectTypeShopHint",
                            ],
                            [
                              "ai",
                              "order.projectTypeAi",
                              "order.projectTypeAiHint",
                            ],
                            [
                              "other",
                              "order.projectTypeOther",
                              "order.projectTypeOtherHint",
                            ],
                          ] as const
                        ).map(([id, labelKey, hintKey]) => {
                          const selected = projectType === id;
                          return (
                            <button
                              key={id}
                              type="button"
                              onClick={() => {
                                setProjectType(id);
                                if (typeof window === "undefined") return;
                                try {
                                  const url = new URL(window.location.href);
                                  const param =
                                    id === "shop"
                                      ? "ecommerce_shop"
                                      : id === "ai"
                                        ? "ai_assistant"
                                        : id;
                                  url.searchParams.set("project_type", param);
                                  url.searchParams.delete("type");
                                  url.searchParams.delete("project");
                                  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
                                } catch {
                                  /* ignore */
                                }
                              }}
                              aria-pressed={selected}
                              className={
                                selected
                                  ? "rounded-2xl border border-emerald-400/55 bg-emerald-500/15 px-3.5 py-3 text-left shadow-[0_0_28px_-12px_rgba(16,185,129,0.65)]"
                                  : "rounded-2xl border border-white/12 bg-black/35 px-3.5 py-3 text-left text-zinc-300 hover:border-white/25 hover:bg-white/[0.04]"
                              }
                            >
                              <span
                                className={`block text-sm font-semibold ${
                                  selected ? "text-emerald-50" : "text-white"
                                }`}
                              >
                                {t(labelKey)}
                              </span>
                              <span className="mt-1 block text-[11px] leading-snug text-zinc-400">
                                {t(hintKey)}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                    <BusinessInterviewPanel
                      value={interview}
                      onChange={(next) => {
                        setInterview(next);
                        if (next.company_name) setBusinessName(next.company_name);
                        if (next.city) setCity(next.city);
                        if (next.niche) setNiche(next.niche);
                        if (next.top_services) setServiceList(next.top_services);
                        if (next.style) setBrandStyle(next.style);
                        if (next.about || next.dialogue) {
                          setDescription(next.about || next.dialogue);
                        }
                        if (next.wishes) setExtraWishes(next.wishes);
                      }}
                    />
                    <Field label={t("order.businessName")} required>
                      <Input
                        value={businessName}
                        onChange={(e) => setBusinessName(e.target.value)}
                        placeholder={t("order.businessNamePh")}
                        required
                      />
                    </Field>
                    <Field label={t("order.description")} required>
                      <Textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder={t("order.descriptionPh")}
                        required
                      />
                    </Field>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field label={t("order.city")}>
                        <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder={t("order.cityPh")} />
                      </Field>
                      <Field label={t("order.companyWebsite")} hint={t("order.companyWebsiteHint")}>
                        <Input
                          type="text"
                          inputMode="url"
                          value={companyWebsite}
                          onChange={(e) => setCompanyWebsite(e.target.value)}
                          placeholder={t("order.companyWebsitePh")}
                          autoComplete="url"
                        />
                      </Field>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field label={t("order.niche")}>
                        <select
                          className="w-full rounded-xl border border-genesis-border-subtle bg-genesis-bg/60 px-3 py-2 text-sm text-white"
                          value={niche}
                          onChange={(e) => {
                            const next = e.target.value;
                            setNiche(next);
                            setSpecialization("");
                            logCommerceEvent("specialization_selected", packageId, "order", {
                              niche: next,
                            });
                          }}
                        >
                          {(nicheOptions.length
                            ? nicheOptions
                            : [{ id: "generic", label_de: "Lokalgeschäft" }]
                          ).map((n) => (
                            <option key={n.id} value={n.id}>
                              {n.label_de}
                            </option>
                          ))}
                        </select>
                      </Field>
                      <Field label={t("order.specialization")}>
                        <select
                          className="w-full rounded-xl border border-genesis-border-subtle bg-genesis-bg/60 px-3 py-2 text-sm text-white"
                          value={specialization}
                          onChange={(e) => {
                            const next = e.target.value;
                            setSpecialization(next);
                            logCommerceEvent("specialization_selected", packageId, "order", {
                              niche,
                              specialization_id: next || null,
                            });
                          }}
                        >
                          <option value="">{t("order.specializationNone")}</option>
                          {specOptions
                            .filter((s) => !s.niche || s.niche === niche)
                            .map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.label}
                              </option>
                            ))}
                        </select>
                      </Field>
                    </div>
                  </>
                )}

                {formStep === 2 && (
                  <>
                    <div className="rounded-xl border border-sky-500/25 bg-sky-950/20 p-4">
                      <p className="text-sm font-medium text-white">{t("order.analysisTitle")}</p>
                      <p className="mt-1 text-xs text-genesis-muted">{t("order.analysisHint")}</p>
                      {insightsBusy ? (
                        <p className="mt-3 text-sm text-sky-100/90">{t("order.analysisBusy")}</p>
                      ) : insights && insights.checks.length > 0 ? (
                        <ul className="mt-3 space-y-2 text-sm">
                          {insights.checks.map((c) => (
                            <li key={c.id} className="rounded-lg border border-white/10 px-3 py-2">
                              <span className="font-medium text-white">{c.label_de}</span>
                              {c.detail ? (
                                <span className="mt-0.5 block text-xs text-genesis-muted">{c.detail}</span>
                              ) : null}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="mt-3 text-sm text-genesis-muted">{t("order.analysisEmpty")}</p>
                      )}
                      {insights?.note_de ? (
                        <p className="mt-2 text-xs text-genesis-muted">{insights.note_de}</p>
                      ) : null}
                    </div>
                    <p className="text-xs text-genesis-muted">{t("order.packageHint")}</p>
                  </>
                )}

                {formStep === 3 && (
                  <>
                    <Field label={t("order.companyWebsite")} hint={t("order.companyWebsiteHint")}>
                      <Input
                        type="text"
                        inputMode="url"
                        value={companyWebsite}
                        onChange={(e) => setCompanyWebsite(e.target.value)}
                        placeholder={t("order.companyWebsitePh")}
                        autoComplete="url"
                      />
                    </Field>
                    <fieldset className="space-y-2">
                      <legend className="text-sm font-medium text-white">{t("order.domainStatusTitle")}</legend>
                      {(
                        [
                          ["none", t("order.domainNone")],
                          ["have_domain", t("order.domainHave")],
                          ["need_help", t("order.domainNeedHelp")],
                        ] as const
                      ).map(([value, label]) => (
                        <label key={value} className="flex cursor-pointer items-center gap-2 text-sm">
                          <input
                            type="radio"
                            name="domainStatus"
                            checked={domainStatus === value}
                            onChange={() => setDomainStatus(value)}
                            className="accent-genesis-accent"
                          />
                          {label}
                        </label>
                      ))}
                    </fieldset>
                    {(domainStatus === "none" || domainStatus === "need_help") && (
                      <p className="rounded-lg border border-amber-500/20 bg-amber-950/20 px-3 py-2 text-xs text-amber-100/90">
                        {t("order.domainHelpNote")}
                      </p>
                    )}
                    {domainStatus === "have_domain" && (
                      <Field label={t("order.existingDomain")}>
                        <Input
                          value={existingDomain}
                          onChange={(e) => setExistingDomain(e.target.value)}
                          placeholder="meine-firma.de"
                        />
                      </Field>
                    )}
                    <p className="text-sm font-medium text-white">{t("order.socialTitle")}</p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Field label="WhatsApp">
                        <Input value={whatsapp} onChange={(e) => setWhatsapp(e.target.value)} placeholder="+49 …" />
                      </Field>
                      <Field label="Telegram">
                        <Input value={telegram} onChange={(e) => setTelegram(e.target.value)} placeholder="@… / https://t.me/…" />
                      </Field>
                      <Field label="Google Business">
                        <Input value={googleBusiness} onChange={(e) => setGoogleBusiness(e.target.value)} placeholder="https://…" />
                      </Field>
                      <Field label="Instagram">
                        <Input value={instagram} onChange={(e) => setInstagram(e.target.value)} placeholder="@… / https://…" />
                      </Field>
                      <Field label="Facebook">
                        <Input value={facebook} onChange={(e) => setFacebook(e.target.value)} placeholder="https://…" />
                      </Field>
                      <Field label="LinkedIn">
                        <Input value={linkedin} onChange={(e) => setLinkedin(e.target.value)} placeholder="https://…" />
                      </Field>
                      <Field label="TikTok">
                        <Input value={tiktok} onChange={(e) => setTiktok(e.target.value)} placeholder="@… / https://…" />
                      </Field>
                      <Field label="YouTube">
                        <Input value={youtube} onChange={(e) => setYoutube(e.target.value)} placeholder="https://…" />
                      </Field>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-3">
                      <p className="text-sm font-medium text-white">{t("order.materialsTitle")}</p>
                      <p className="text-xs text-genesis-muted">{t("order.materialsHint")}</p>
                      <input
                        type="file"
                        multiple
                        accept=".png,.jpg,.jpeg,.svg,.webp,.pdf,.docx,.xlsx,.pptx,.txt,.zip,.mp4"
                        onChange={(e) => {
                          void uploadMaterials(e.target.files);
                          e.target.value = "";
                        }}
                        className="block w-full text-sm text-genesis-muted file:mr-3 file:rounded-lg file:border-0 file:bg-genesis-accent/20 file:px-3 file:py-1.5 file:text-sm file:text-white"
                      />
                      {uploadBusy && <p className="text-xs text-genesis-muted">{t("order.uploadBusy")}</p>}
                      {uploadError && (
                        <p className="text-xs text-rose-300" role="alert">
                          {uploadError}
                        </p>
                      )}
                      {materials.length > 0 && (
                        <ul className="space-y-2 text-sm">
                          {materials.map((m) => (
                            <li
                              key={m.id}
                              className="flex items-start justify-between gap-2 rounded-lg border border-white/10 px-3 py-2"
                            >
                              <span>
                                <span className="font-medium text-white">{m.filename}</span>
                                <span className="mt-0.5 block text-xs text-genesis-muted">{m.status_de}</span>
                              </span>
                              <button
                                type="button"
                                className="text-xs text-rose-300 hover:underline"
                                onClick={() => setMaterials((prev) => prev.filter((x) => x.id !== m.id))}
                              >
                                {t("order.removeFile")}
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <label className="flex cursor-pointer items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={needsLogo}
                        onChange={(e) => setNeedsLogo(e.target.checked)}
                        className="rounded border-genesis-border accent-genesis-accent"
                      />
                      {t("order.needsLogo")}
                    </label>
                  </>
                )}

                {formStep === 4 && (
                  <>
                    <div className="rounded-xl border border-emerald-500/25 bg-emerald-950/20 p-4 space-y-3">
                      <p className="text-sm font-medium text-white">{t("order.contactBeforePayTitle")}</p>
                      <p className="text-xs text-genesis-muted">{t("order.contactBeforePayHint")}</p>
                      <Field
                        label={t("order.email")}
                        required
                        error={error && !email.trim() ? error : undefined}
                      >
                        <Input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="hello@…"
                          required
                          error={Boolean(error && !email.trim())}
                          autoComplete="email"
                        />
                      </Field>
                      <Field label={t("order.phoneOptional")}>
                        <Input
                          type="tel"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="+49 …"
                          autoComplete="tel"
                        />
                      </Field>
                    </div>
                    {(insightsBusy || (insights && insights.checks.length > 0)) && (
                      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                        <p className="text-sm font-medium text-white">{t("order.insightsTitle")}</p>
                        {insightsBusy ? (
                          <p className="mt-2 text-xs text-genesis-muted">…</p>
                        ) : (
                          <ul className="mt-2 space-y-1.5 text-xs text-genesis-muted">
                            {(insights?.checks || []).map((c) => (
                              <li key={c.id}>• {c.label_de}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}
                    <Field label={t("order.extraWishes")}>
                      <Textarea
                        value={extraWishes}
                        onChange={(e) => setExtraWishes(e.target.value)}
                        placeholder={t("order.extraWishesPh")}
                      />
                    </Field>
                    <fieldset>
                      <legend className="text-sm font-medium text-white">
                        {t("order.brandStyleTitle")}
                      </legend>
                      <p className="mt-1 text-xs text-genesis-muted">{t("order.brandStyleHint")}</p>
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        {(
                          [
                            "auto",
                            "modern",
                            "premium",
                            "elegant",
                            "minimal",
                            "corporate",
                            "friendly",
                          ] as const
                        ).map((id) => (
                          <label
                            key={id}
                            className={`cursor-pointer rounded-xl border px-3 py-2.5 text-sm transition ${
                              brandStyle === id
                                ? "border-emerald-400/50 bg-emerald-950/30"
                                : "border-genesis-border-subtle bg-genesis-bg/40 hover:bg-genesis-elevated"
                            }`}
                          >
                            <input
                              type="radio"
                              className="sr-only"
                              name="brandStyle"
                              checked={brandStyle === id}
                              onChange={() => setBrandStyle(id)}
                            />
                            <span className="font-medium text-white">
                              {t(`order.brandStyles.${id}.label`)}
                            </span>
                            <span className="mt-0.5 block text-[11px] text-genesis-muted">
                              {t(`order.brandStyles.${id}.hint`)}
                            </span>
                          </label>
                        ))}
                      </div>
                    </fieldset>
                    <p className="text-sm font-medium text-white">{t("order.legalTitle")}</p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Field label={t("order.legalOwner")}>
                        <Input value={legalOwner} onChange={(e) => setLegalOwner(e.target.value)} />
                      </Field>
                      <Field label={t("order.legalForm")}>
                        <Input value={legalForm} onChange={(e) => setLegalForm(e.target.value)} />
                      </Field>
                      <Field label={t("order.legalStreet")}>
                        <Input value={legalStreet} onChange={(e) => setLegalStreet(e.target.value)} />
                      </Field>
                      <Field label={t("order.legalZip")}>
                        <Input value={legalZip} onChange={(e) => setLegalZip(e.target.value)} />
                      </Field>
                      <Field label={t("order.legalCity")}>
                        <Input value={legalCity} onChange={(e) => setLegalCity(e.target.value)} />
                      </Field>
                      <Field label={t("order.legalDirector")}>
                        <Input value={legalDirector} onChange={(e) => setLegalDirector(e.target.value)} />
                      </Field>
                      <Field label={t("order.legalVat")}>
                        <Input value={legalVat} onChange={(e) => setLegalVat(e.target.value)} />
                      </Field>
                    </div>
                    <label className="flex cursor-pointer items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={legalMaps}
                        onChange={(e) => setLegalMaps(e.target.checked)}
                        className="accent-genesis-accent"
                      />
                      {t("order.legalMaps")}
                    </label>
                    <label className="flex cursor-pointer items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={legalAnalytics}
                        onChange={(e) => setLegalAnalytics(e.target.checked)}
                        className="accent-genesis-accent"
                      />
                      {t("order.legalAnalytics")}
                    </label>
                  </>
                )}

                <div className="sticky bottom-0 z-20 -mx-1 mt-3 border-t border-white/10 bg-[rgba(8,12,20,0.92)] px-1 py-3 backdrop-blur-md">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="md"
                      disabled={formStep <= 1}
                      onClick={goBack}
                    >
                      ← {t("order.back")}
                    </Button>
                    <p className="text-[11px] text-zinc-400">
                      {t("order.stepProgress", {
                        current: formStep,
                        total: 4,
                      })}
                    </p>
                    {formStep < 4 ? (
                      <div className="flex max-w-full flex-col items-end gap-1">
                        <Button
                          type="button"
                          variant="primary"
                          size="md"
                          disabled={
                            formStep === 1 &&
                            (!businessName.trim() ||
                              description.trim().length < 8)
                          }
                          className="storefront-cta-primary !rounded-2xl !bg-emerald-500 !text-black !shadow-[0_0_40px_-6px_rgba(16,185,129,0.75)] disabled:!bg-zinc-700 disabled:!text-zinc-400 disabled:!shadow-none"
                          onClick={() => void goNext()}
                        >
                          {t("order.next")} →
                        </Button>
                        {formStep === 1 &&
                        (!businessName.trim() ||
                          description.trim().length < 8) ? (
                          <p className="max-w-[16rem] text-right text-[10px] leading-snug text-amber-200/90">
                            {t("order.nextDisabledHint")}
                          </p>
                        ) : null}
                      </div>
                    ) : (
                      <span className="text-xs text-zinc-400">{t("order.stepNavConfirmHint")}</span>
                    )}
                  </div>
                </div>
                {error && formStep < 4 && (
                  <p className="text-xs text-rose-300" role="alert">
                    {error}
                  </p>
                )}
              </>
            ) : (
              <>
                <Field
                  label={t("order.emailLaunch")}
                  required
                  error={error && !email.trim() ? error : undefined}
                >
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="hello@…"
                    required
                    error={Boolean(error && !email.trim())}
                  />
                </Field>
                <Field label={t("order.phoneOptional")}>
                  <Input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+49 …"
                  />
                </Field>
              </>
            )}
          </div>

          <aside className="lg:col-span-2">
            <Card
              glow
              hover={false}
              className="storefront-module-card sticky top-4 !rounded-3xl border-white/10 bg-white/[0.03]"
              padding="md"
            >
              <p className="genesis-label">
                {launch ? t("order.launchTitle") : t("order.packageAndPrice")}
              </p>
              {packagesLoading ? (
                <PackageSkeleton />
              ) : packages.length === 0 ? (
                <p className="mt-4 text-sm text-genesis-muted">{t("order.packagesFail")}</p>
              ) : launch && selected ? (
                <div className="mt-3">
                  <p className="text-lg font-semibold">
                    {launch.projectLabel} {launch.company}
                  </p>
                  <p className="mt-2 text-3xl font-bold tabular-nums">
                    {formatPrice(orderTotalEur, selected)}
                  </p>
                  <p className="mt-2 text-xs text-genesis-muted leading-relaxed">
                    {t("order.launchFixed")}
                  </p>
                  <p className="genesis-label mt-4">{t("order.launchIncludes")}</p>
                  <ul className="space-y-1.5 text-xs">
                    {launchDeliverables.map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400">✔</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="mt-3 space-y-2">
                  {displayPackages.map((p) => {
                    const workspaceNote =
                      p.id === "basic"
                        ? "Keine Virtus-Verwaltung"
                        : p.id === "business"
                          ? "Virtus Workspace · Präsentationsniveau"
                          : p.id === "premium"
                            ? "Gleiche Qualität wie Business + mehr Steuerung und Tiefe"
                            : "";
                    return (
                    <label
                      key={p.id}
                      className={`flex cursor-pointer items-center justify-between gap-2 rounded-xl border px-3 py-2.5 text-sm transition-smooth ${
                        packageId === p.id
                          ? "border-genesis-accent/50 bg-genesis-accent/10"
                          : "border-genesis-border-subtle hover:border-genesis-accent/30"
                      }`}
                    >
                      <span className="flex min-w-0 items-start gap-2">
                        <input
                          type="radio"
                          name="package"
                          checked={packageId === p.id}
                          onChange={() => {
                            setManualPackage(true);
                            setPackageId(p.id);
                            logCommerceEvent("tier_select", p.id, "order", { niche });
                          }}
                          className="mt-1 accent-genesis-accent"
                        />
                        <span className="min-w-0">
                          <span className="block font-medium">{p.name}</span>
                          {workspaceNote ? (
                            <span className="mt-0.5 block text-[11px] text-genesis-muted">
                              {workspaceNote}
                            </span>
                          ) : null}
                        </span>
                      </span>
                      <span className="shrink-0 text-right">
                        <span className="block font-semibold tabular-nums">
                          {formatPrice(p.price_eur, p)}
                        </span>
                        {p.id === "business" ? (
                          <span className="mt-0.5 block text-[10px] font-medium text-emerald-300/90">
                            Präsentation
                          </span>
                        ) : p.id === "premium" ? (
                          <span className="mt-0.5 block text-[10px] font-medium text-emerald-300/90">
                            Mehr Tiefe
                          </span>
                        ) : null}
                      </span>
                    </label>
                    );
                  })}
                </div>
              )}
              {!launch && presentationIncluded ? (
                <div className="mt-3 rounded-xl border border-emerald-500/25 bg-emerald-950/20 px-3 py-2.5 text-sm">
                  <p className="font-medium text-emerald-100">
                    {(packageId || "").toLowerCase() === "premium" ||
                    (packageId || "").toLowerCase() === "connected"
                      ? "✓ Premium = Business-Qualität + erweiterte Steuerung"
                      : "✓ Hochwertige Präsentation im Business-Paket"}
                  </p>
                  <p className="mt-1 text-xs text-genesis-muted">
                    {(packageId || "").toLowerCase() === "premium" ||
                    (packageId || "").toLowerCase() === "connected"
                      ? "Kein anderer Design-Stil — mehr Möglichkeiten, Struktur und Management. Kein Extra-Aufpreis."
                      : "Wie in den Business-Beispielen auf /site — kein separates Add-on."}
                  </p>
                </div>
              ) : null}
              {!launch && (
                <>
                  <div className="mt-3">
                    <Field label={t("order.premiumServicesLabel")}>
                      <Textarea
                        value={serviceList}
                        onChange={(e) => setServiceList(e.target.value)}
                        placeholder={t("order.premiumServicesPh")}
                        rows={3}
                      />
                    </Field>
                    <p className="mt-1 text-[11px] text-genesis-muted">
                      {t("order.premiumServicesHint")}
                    </p>
                  </div>
                  <OrderProjectPreview
                    projectType={projectType}
                    packageId={packageId}
                    niche={niche}
                    serviceList={serviceList}
                  />
                </>
              )}
              {!launch && !manualPackage && selected && (
                <p className="mt-2 text-xs text-genesis-muted">
                  {t("order.recommend", { name: selected.name })}
                </p>
              )}
              {!launch && selected && (
                <>
                  <p className="genesis-label mt-4">{t("order.youGet")}</p>
                  <ul className="space-y-1.5 text-xs">
                    {selectedPackageBenefits.map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400">✔</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                loading={busy}
                className="storefront-cta-primary mt-4 !rounded-2xl !bg-genesis-purple-soft !shadow-[0_0_40px_-6px_rgba(167,139,250,0.7)]"
              >                {busy
                  ? t("order.submitBusy")
                  : launch
                    ? t("order.submitLaunch", {
                        price: selected ? formatPrice(selected.price_eur, selected) : "…",
                      })
                    : formStep < 4
                      ? t("order.next")
                      : t("order.submit")}
              </Button>
              {error && email.trim() && (
                <p className="mt-2 text-xs text-rose-300" role="alert">
                  {error}
                </p>
              )}
              <p className="mt-3 text-[10px] text-genesis-muted">{t("order.payAfter")}</p>
            </Card>
          </aside>
        </form>

        <p className="mt-6 text-center text-xs text-genesis-muted">
          {launch ? t("order.agreeLaunch") : t("order.agreeSubmit")}
          <Link href="/agb" className="text-genesis-accent hover:underline">
            AGB
          </Link>
          {t("order.and")}
          <Link href="/datenschutz" className="text-genesis-accent hover:underline">
            Datenschutz
          </Link>
          .
        </p>
      </main>
    </PublicPageShell>
  );
}

function OrderCoachPanel({
  hints,
}: {
  hints: { id: string; messageKey: string; severity: "block" | "tip" }[];
}) {
  const { t } = useTranslation("site");
  if (hints.length === 0) return null;
  const hasBlock = hints.some((h) => h.severity === "block");
  return (
    <div
      className={`mb-4 rounded-xl border px-3 py-2.5 ${
        hasBlock
          ? "border-amber-500/35 bg-amber-950/25"
          : "border-emerald-500/25 bg-emerald-950/20"
      }`}
      role="status"
    >
      <p className="text-[11px] font-semibold uppercase tracking-wide text-emerald-200/90">
        {t("order.coachTitle")}
      </p>
      <ul className="mt-1.5 space-y-1">
        {hints.map((h) => (
          <li
            key={h.id}
            className={`text-xs leading-snug ${
              h.severity === "block" ? "text-amber-100" : "text-white/80"
            }`}
          >
            {h.severity === "block" ? "→ " : "· "}
            {t(`order.${h.messageKey}`)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function FormStepBar({
  current,
  maxReached,
  onSelectStep,
}: {
  current: number;
  maxReached: number;
  onSelectStep: (step: number) => void;
}) {
  const { t } = useTranslation("site");
  const steps = [
    t("order.formStep1"),
    t("order.formStep2"),
    t("order.formStep3"),
    t("order.formStep4"),
    t("order.formStep5"),
  ];
  return (
    <div className="mb-4 space-y-2">
      <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-zinc-400">
        {t("order.progressLabel")}
      </p>
      <p className="text-xs text-zinc-500 sm:hidden" aria-live="polite">
        {current} / 4 · {steps[current - 1]}
      </p>
      <ol
        className="flex flex-col gap-1.5 sm:flex-row sm:flex-wrap sm:gap-2"
        aria-label={t("order.formStepsAria")}
      >
        {steps.slice(0, 4).map((label, idx) => {
          const n = idx + 1;
          const isCurrent = n === current;
          const isDone = n < current;
          const isReachable = n <= maxReached;
          const isLocked = n > maxReached;
          const marker = isDone ? "✓" : isCurrent ? "➜" : "○";
          const className = isCurrent
            ? "border-emerald-400/45 bg-emerald-500/15 text-white"
            : isDone
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
              : isReachable
                ? "border-white/15 bg-white/5 text-zinc-400 hover:border-white/30 hover:text-white"
                : "border-transparent bg-transparent text-zinc-600";
          const inner = (
            <>
              <span className="font-medium" aria-hidden="true">
                {marker}
              </span>
              <span>
                {n}. {label}
              </span>
            </>
          );
          return (
            <li key={label} className="min-w-0">
              {isReachable && !isLocked ? (
                <button
                  type="button"
                  onClick={() => onSelectStep(n)}
                  className={`inline-flex w-full items-center gap-2 rounded-full border px-2.5 py-1.5 text-left text-[11px] transition-smooth sm:w-auto ${className}`}
                  aria-current={isCurrent ? "step" : undefined}
                  aria-label={
                    isCurrent
                      ? t("order.stepNavCurrent", { step: label })
                      : t("order.stepNavGoTo", { step: label })
                  }
                >
                  {inner}
                </button>
              ) : (
                <span
                  className={`inline-flex w-full items-center gap-2 rounded-full border px-2.5 py-1.5 text-[11px] sm:w-auto ${className}`}
                  aria-disabled="true"
                >
                  {inner}
                </span>
              )}
            </li>
          );
        })}
        <li className="min-w-0">
          <span className="inline-flex w-full items-center gap-2 rounded-full border border-dashed border-white/10 px-2.5 py-1.5 text-[11px] text-zinc-500 sm:w-auto">
            <span aria-hidden>5</span>
            <span>{steps[4]}</span>
          </span>
        </li>
      </ol>
      <p className="text-[11px] text-zinc-500">{t("order.progressHint")}</p>
    </div>
  );
}

function OrderSteps({ current, launch = false }: { current: number; launch?: boolean }) {
  const { t } = useTranslation("site");
  const steps = launch
    ? [
        { n: 1, label: t("order.stepProject") },
        { n: 2, label: t("order.stepLaunch") },
        { n: 3, label: t("order.stepPublish") },
      ]
    : [
        { n: 1, label: t("order.stepForm") },
        { n: 2, label: t("order.stepConfirm") },
        { n: 3, label: t("order.stepPay") },
      ];
  return (
    <ol
      className="mb-2 flex justify-center gap-2 sm:gap-3"
      aria-label={t("order.stepsAria")}
    >
      {steps.map((s) => (
        <li
          key={s.n}
          className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition-smooth sm:text-sm ${
            s.n === current
              ? "border-violet-400/50 bg-violet-500/20 text-white shadow-[0_0_24px_-8px_rgba(167,139,250,0.8)]"
              : s.n < current
                ? "border-emerald-400/30 text-emerald-300"
                : "border-white/10 text-genesis-muted"
          }`}
          aria-current={s.n === current ? "step" : undefined}
        >
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold ${
              s.n === current
                ? "bg-genesis-purple-soft text-white"
                : "bg-white/5"
            }`}
          >
            {s.n}
          </span>
          {s.label}
        </li>
      ))}
    </ol>
  );
}
