/**
 * Order form coach — Virtus Core tips when required/helpful fields are missing.
 * Keeps the buyer moving toward payment without feeling blocked by silence.
 */

export type OrderCoachHint = {
  id: string;
  /** i18n key under order.* */
  messageKey: string;
  severity: "block" | "tip";
};

export type OrderCoachInput = {
  formStep: number;
  businessName: string;
  email: string;
  description: string;
  city: string;
  phone: string;
  niche: string;
  companyWebsite: string;
  packageId: string;
  serviceList: string;
  domainStatus: string;
  existingDomain: string;
};

function filled(s: string, min = 1): boolean {
  return s.trim().length >= min;
}

/** Hints for the current step — blockers first, then soft tips (max 4). */
export function resolveOrderCoachHints(input: OrderCoachInput): OrderCoachHint[] {
  const out: OrderCoachHint[] = [];
  const step = input.formStep;

  if (step === 1) {
    if (!filled(input.businessName)) {
      out.push({ id: "biz", messageKey: "coachNeedBusiness", severity: "block" });
    }
    if (!filled(input.email) || !input.email.includes("@")) {
      out.push({ id: "email", messageKey: "coachNeedEmail", severity: "block" });
    }
    if (!filled(input.description, 8)) {
      out.push({ id: "desc", messageKey: "coachNeedDescription", severity: "block" });
    }
    if (out.length === 0 && !filled(input.city)) {
      out.push({ id: "city", messageKey: "coachTipCity", severity: "tip" });
    }
    if (out.length < 3 && !filled(input.niche)) {
      out.push({ id: "niche", messageKey: "coachTipNiche", severity: "tip" });
    }
    if (out.length < 3 && !filled(input.companyWebsite) && !filled(input.phone)) {
      out.push({ id: "contact", messageKey: "coachTipContactOrSite", severity: "tip" });
    }
  }

  if (step === 2) {
    if (!filled(input.packageId)) {
      out.push({ id: "pkg", messageKey: "coachNeedPackage", severity: "block" });
    } else {
      out.push({ id: "pkgOk", messageKey: "coachTipPackageOk", severity: "tip" });
    }
  }

  if (step === 3) {
    if (input.domainStatus === "have_domain" && !filled(input.existingDomain)) {
      out.push({ id: "dom", messageKey: "coachNeedDomainName", severity: "block" });
    }
    if (out.every((h) => h.severity !== "block")) {
      out.push({ id: "domTip", messageKey: "coachTipDomain", severity: "tip" });
      out.push({ id: "matTip", messageKey: "coachTipMaterials", severity: "tip" });
    }
  }

  if (step === 4) {
    if ((input.packageId || "").toLowerCase() === "premium" && !filled(input.serviceList, 4)) {
      out.push({ id: "svc", messageKey: "coachTipPremiumServices", severity: "tip" });
    }
    out.push({ id: "pay", messageKey: "coachTipReadyPay", severity: "tip" });
    out.push({ id: "legal", messageKey: "coachTipLegal", severity: "tip" });
  }

  return out.slice(0, 4);
}

export function orderCoachHasBlocker(hints: OrderCoachHint[]): boolean {
  return hints.some((h) => h.severity === "block");
}
