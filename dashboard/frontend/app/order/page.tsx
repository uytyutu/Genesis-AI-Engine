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
import { OrderTrustCard } from "../components/OrderTrustCard";
import { OrderProjectSummary } from "../components/OrderProjectSummary";
import { fetchProjectPlatform } from "../lib/projectApi";
import { buildOrderLaunchContext, type OrderLaunchContext } from "../lib/orderProjectLaunch";
import { Badge, Button, ButtonLink, Card, Field, Input, Textarea } from "../components/ui";
import { publicApiBase } from "../lib/publicApiBase";
import { logCommerceEvent } from "../lib/commerceFunnel";
import { uiLangForMarket } from "../lib/marketLang";
import { PackagePreviewCarousel } from "../components/PackagePreviewCarousel";
import { filterPublicPackages, showSmokePackageInUi } from "../lib/showSmokePackage";
import { parseClientServices } from "../lib/packagePreviewGallery";
import { resolveOrderCoachHints } from "../lib/orderFormCoach";
import { getVisitorId } from "../lib/visitorId";
import {
  clearOrderDraft,
  createDebouncedOrderDraftSaver,
  isMeaningfulOrderDraft,
  loadOrderDraft,
  type OrderDraftPayload,
} from "../lib/orderDraft";

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
  const [marketParam, setMarketParam] = useState("");
  const [marketReady, setMarketReady] = useState(false);
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
    if (!marketParam) return;
    const lang = uiLangForMarket(marketParam);
    const current = (i18n.language || "").slice(0, 2).toLowerCase();
    if (current !== lang) {
      void i18n.changeLanguage(lang);
    }
  }, [marketParam, i18n]);
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
  const [packageId, setPackageId] = useState("basic");
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
  } | null>(null);
  const [payBusy, setPayBusy] = useState(false);
  const [payError, setPayError] = useState("");
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

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const pkg = params.get("package");
    if (pkg && ["basic", "business", "premium"].includes(pkg)) {
      setPackageId(pkg);
      setManualPackage(true);
      urlPackageRef.current = pkg;
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
    setPurchaseType(parseOrderPurchaseType(params.get("purchase_type")));
    const vid = params.get("visitor_id")?.trim();
    setVisitorId(vid || getVisitorId("public"));
    logCommerceEvent("tier_page_view", pkg, "order");
  }, []);

  // Restore Path A order draft once visitor + market URL are known (URL package/niche win).
  useEffect(() => {
    if (!visitorId || !marketReady || draftReady) return;
    const market = (marketParam || commerce.market_code || "DE").toUpperCase();
    const draft = loadOrderDraft(market, visitorId);
    if (isMeaningfulOrderDraft(draft) && draft) {
      applyOrderDraft(draft);
      if (urlPackageRef.current) {
        setPackageId(urlPackageRef.current);
        setManualPackage(true);
      }
      if (urlNicheRef.current) setNiche(urlNicheRef.current);
      setDraftBanner(true);
    }
    setDraftReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- hydrate once per visitor/market
  }, [visitorId, marketReady, marketParam, commerce.market_code, draftReady]);

  function applyOrderDraft(d: OrderDraftPayload) {
    setFormStep(Math.min(4, Math.max(1, Math.floor(d.formStep) || 1)));
    setPackageId(d.packageId || "basic");
    setManualPackage(Boolean(d.manualPackage));
    setBrandStyle(d.brandStyle || "auto");
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
      packageId,
      manualPackage,
      brandStyle,
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
    packageId,
    manualPackage,
    brandStyle,
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
        if (Array.isArray(body?.niches)) setNicheOptions(body.niches);
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
    if (!packages.some((p) => p.id === packageId)) {
      setPackageId(packages[0]!.id);
    }
  }, [packages, packageId]);

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

  const selected = packages.find((p) => p.id === packageId) ?? packages[0];
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
      if (!email.trim() || !email.includes("@")) {
        setError(t("order.coachNeedEmail"));
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
    const next = Math.min(4, formStep + 1);
    setFormStep(next);
    if (next === 2) await loadInsightsPreview();
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
      const res = await fetch(`${API}/api/sales/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: businessName.trim() || launch?.company || "Projekt",
          description: description.trim() || launch?.projectLabel || "Landing Launch",
          city: city.trim() || null,
          phone: phone.trim() || null,
          whatsapp: whatsapp.trim() || null,
          email: email.trim() || null,
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
          extra_wishes: [
            extraWishes.trim(),
            packageId === "premium" && parseClientServices(serviceList).length
              ? `Services: ${parseClientServices(serviceList).join(", ")}`
              : "",
          ]
            .filter(Boolean)
            .join("\n") || null,
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
          brand_style: brandStyle || "auto",
          niche: niche || null,
          specialization: specialization.trim() || null,
          services_list: parseClientServices(serviceList),
          market_code: commerce.market_code || marketParam || undefined,
          visitor_id: visitorId,
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
      });
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
    } catch {
      setError(t("order.serverDown"));
    } finally {
      setBusy(false);
    }
  }

  async function payNow() {
    if (!done) return;
    setPayBusy(true);
    setPayError("");
    try {
      logCommerceEvent("checkout_start", packageId, "order", {
        order_id: done.order_id,
        niche,
      });
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
          <Card glow className="text-center" padding="lg">
            <p className="text-4xl text-emerald-400" aria-hidden>
              ✓
            </p>
            <h1 className="mt-4 text-2xl font-bold">
              {launch ? t("order.projectLocked") : t("order.thanks")}
            </h1>
            <p className="mt-3 text-genesis-muted">{done.message}</p>
            <Badge variant="muted" className="mt-3">
              № {done.order_id}
            </Badge>
            <Card hover={false} className="mt-6 text-left" padding="md">
              {launch ? (
                <>
                  <p className="text-sm text-genesis-muted">{t("order.toPay")}</p>
                  <p className="mt-1 text-xl font-semibold">
                    {launch.projectLabel} {launch.company} — {formatPrice(done.price_eur, done)}
                  </p>
                  <p className="genesis-label mt-4">{t("order.afterPay")}</p>
                  <ul className="mt-2 space-y-1.5 text-sm">
                    {(launch && done.deliverables.length > 0
                      ? done.deliverables
                      : launchDeliverables
                    ).map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400">✔</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <>
                  <p className="text-sm text-genesis-muted">{t("order.projectPriced")}</p>
                  <p className="mt-1 text-xl font-semibold">
                    {done.package_name} — {formatPrice(done.price_eur, done)}
                  </p>
                  <p className="genesis-label mt-4">{t("order.youReceive")}</p>
                  <ul className="mt-2 space-y-1.5 text-sm">
                    {done.deliverables.map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400">✔</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                  {done.buyer_insights?.checks && done.buyer_insights.checks.length > 0 ? (
                    <>
                      <p className="genesis-label mt-4">{t("order.insightsTitle")}</p>
                      <ul className="mt-2 space-y-1.5 text-sm">
                        {done.buyer_insights.checks.map((c) => (
                          <li key={c.id} className="flex gap-2">
                            <span className="text-emerald-400">✓</span>
                            <span>{c.label_de}</span>
                          </li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                </>
              )}
            </Card>
            {paymentReady ? (
              <div className="mt-6 space-y-3">
                <OrderTrustCard purchaseType={purchaseType} />
                <Button variant="success" size="lg" fullWidth loading={payBusy} onClick={payNow}>
                  {payBusy
                    ? t("order.payBusy")
                    : t("order.payNow", { price: formatPrice(done.price_eur, done) })}
                </Button>
                {payError && (
                  <p className="text-xs text-rose-300" role="alert">
                    {payError}
                  </p>
                )}
              </div>
            ) : (
              <p className="mt-6 text-sm text-amber-200/90">{t("order.payUnavailable")}</p>
            )}
            <ButtonLink
              href={`/order/status/${done.order_id}`}
              variant="ghost"
              size="sm"
              className="mt-4"
            >
              {t("order.trackStatus")}
            </ButtonLink>
          </Card>
        </main>
      </PublicPageShell>
    );
  }

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-4xl py-2">
        <OrderSteps current={1} launch={Boolean(launch)} />
        <div className="mb-8 text-center animate-fade-up">
          <Badge variant="accent" className="tracking-[0.2em]">
            {t("order.badge")}
          </Badge>
          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">
            {launch ? t("order.titleLaunch") : t("order.title")}
          </h1>
          <p className="mt-2 text-genesis-muted">
            {launch ? t("order.subtitleLaunch") : t("order.subtitle")}
          </p>
          {!launch ? (
            <ul className="mx-auto mt-4 max-w-lg space-y-1 text-left text-sm text-white/75">
              <li>• {t("order.bulletPkg")}</li>
              <li>• {t("order.bulletAfterPay")}</li>
              <li>• {t("order.bulletSorglos")}</li>
            </ul>
          ) : null}
          {!launch ? (
            <ul className="mx-auto mt-4 flex max-w-xl flex-wrap justify-center gap-2 text-xs">
              {[t("pathA.benefitMobile"), t("pathA.benefitSeo"), t("pathA.benefitSpeed")].map(
                (label) => (
                  <li
                    key={label}
                    className="rounded-full border border-emerald-500/30 bg-emerald-950/30 px-3 py-1 text-emerald-100/90"
                  >
                    ✓ {label}
                  </li>
                ),
              )}
            </ul>
          ) : null}
        </div>

        {launch ? <OrderProjectSummary launch={launch} /> : null}
        {launchLoading && !launch ? (
          <p className="mb-6 text-center text-sm text-genesis-muted">{t("order.loadingProject")}</p>
        ) : null}

        <form onSubmit={submit} className={`grid gap-6 lg:grid-cols-5 ${launch ? "mt-6" : ""}`}>
          <div className="space-y-4 lg:col-span-3">
            {!launch ? (
              <>
                <FormStepBar current={formStep} />
                {draftBanner ? (
                  <div
                    className="flex flex-col gap-2 rounded-xl border border-genesis-border/80 bg-genesis-surface/80 px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between"
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
                    <Field label={t("order.businessName")} required>
                      <Input
                        value={businessName}
                        onChange={(e) => setBusinessName(e.target.value)}
                        placeholder={t("order.businessNamePh")}
                        required
                      />
                    </Field>
                    <Field label={t("order.email")} required error={error && !email.trim() ? error : undefined}>
                      <Input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="hello@…"
                        required
                        error={Boolean(error && !email.trim())}
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
                      <Field label={t("order.phone")}>
                        <Input
                          type="tel"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="+49 …"
                        />
                      </Field>
                    </div>
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
                      <Field label="Google Business">
                        <Input value={googleBusiness} onChange={(e) => setGoogleBusiness(e.target.value)} placeholder="https://…" />
                      </Field>
                      <Field label="Instagram">
                        <Input value={instagram} onChange={(e) => setInstagram(e.target.value)} placeholder="@… / https://…" />
                      </Field>
                      <Field label="Facebook">
                        <Input value={facebook} onChange={(e) => setFacebook(e.target.value)} placeholder="https://…" />
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

                <div className="flex flex-wrap gap-2 pt-1">
                  {formStep > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="md"
                      onClick={() => setFormStep((s) => Math.max(1, s - 1))}
                    >
                      {t("order.back")}
                    </Button>
                  )}
                  {formStep < 4 && (
                    <Button type="button" variant="primary" size="md" onClick={() => void goNext()}>
                      {t("order.next")}
                    </Button>
                  )}
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
            <Card glow className="sticky top-4" padding="md">
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
                    {formatPrice(selected.price_eur, selected)}
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
                  {packages.map((p) => (
                    <label
                      key={p.id}
                      className={`flex cursor-pointer items-center justify-between rounded-xl border px-3 py-2.5 text-sm transition-smooth ${
                        packageId === p.id
                          ? "border-genesis-accent/50 bg-genesis-accent/10"
                          : "border-genesis-border-subtle hover:border-genesis-accent/30"
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="package"
                          checked={packageId === p.id}
                          onChange={() => {
                            setManualPackage(true);
                            setPackageId(p.id);
                            logCommerceEvent("tier_select", p.id, "order", { niche });
                          }}
                          className="accent-genesis-accent"
                        />
                        {p.name}
                      </span>
                      <span className="font-semibold tabular-nums">{formatPrice(p.price_eur, p)}</span>
                    </label>
                  ))}
                </div>
              )}
              {!launch && (
                <>
                  {packageId === "premium" ? (
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
                  ) : null}
                  <PackagePreviewCarousel
                    packageId={packageId}
                    niche={niche}
                    services={
                      packageId === "premium" ? parseClientServices(serviceList) : undefined
                    }
                  />
                  {packageId !== "premium" ? (
                    <button
                      type="button"
                      onClick={() => {
                        setManualPackage(true);
                        setPackageId("premium");
                        logCommerceEvent("upgrade_click", "premium", "order", { niche });
                      }}
                      className="mt-2 w-full rounded-lg border border-emerald-500/40 bg-emerald-950/40 px-2 py-1.5 text-xs font-medium text-emerald-100 hover:bg-emerald-900/50"
                    >
                      {t("order.upgradePremium")}
                    </button>
                  ) : null}
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
                    {selected.deliverables.map((d) => (
                      <li key={d} className="flex gap-2">
                        <span className="text-emerald-400">✔</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
              <Button type="submit" variant="primary" size="lg" fullWidth loading={busy} className="mt-4">
                {busy
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

function FormStepBar({ current }: { current: number }) {
  const { t } = useTranslation("site");
  const steps = [
    t("order.formStep1"),
    t("order.formStep2"),
    t("order.formStep3"),
    t("order.formStep4"),
  ];
  const journey = [
    t("order.journeyWelcome"),
    t("order.journeyBusiness"),
    t("order.journeyAnalysis"),
    t("order.journeyPackage"),
    t("order.journeyPersonal"),
    t("order.journeyCheckout"),
  ];
  return (
    <div className="mb-4 space-y-3">
      <ol className="flex flex-wrap gap-1.5" aria-label={t("order.journeyAria")}>
        {journey.map((label, i) => {
          const active =
            (current === 1 && i <= 1) ||
            (current === 2 && i <= 2) ||
            (current === 3 && i <= 4) ||
            (current === 4 && i <= 4);
          return (
            <li
              key={label}
              className={`rounded-full px-2 py-0.5 text-[10px] ${
                active
                  ? "bg-emerald-500/20 text-emerald-100"
                  : "bg-white/5 text-genesis-muted"
              }`}
            >
              {label}
            </li>
          );
        })}
      </ol>
      <ol className="mb-2 flex flex-wrap gap-2" aria-label={t("order.formStepsAria")}>
        {steps.map((label, idx) => {
          const n = idx + 1;
          return (
            <li
              key={label}
              className={`rounded-full px-2.5 py-1 text-[11px] ${
                n === current
                  ? "bg-genesis-accent/20 text-white"
                  : n < current
                    ? "text-emerald-400"
                    : "text-genesis-muted"
              }`}
              aria-current={n === current ? "step" : undefined}
            >
              {n}. {label}
            </li>
          );
        })}
      </ol>
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
    <ol className="mb-8 flex justify-center gap-2 sm:gap-4" aria-label={t("order.stepsAria")}>
      {steps.map((s) => (
        <li
          key={s.n}
          className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs transition-smooth sm:text-sm ${
            s.n === current
              ? "bg-genesis-accent/20 text-white"
              : s.n < current
                ? "text-emerald-400"
                : "text-genesis-muted"
          }`}
          aria-current={s.n === current ? "step" : undefined}
        >
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold ${
              s.n === current ? "bg-genesis-accent text-white" : "bg-white/5"
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
