/** Shared company profile helpers for order flows (same public prices — no discounts). */

export type ClientCompanyProfile = {
  company_name: string;
  email: string;
  phone: string;
  primary_niche: string;
  complete: boolean;
};

export function companyProfileFromMe(
  me: Record<string, unknown> | null | undefined,
): ClientCompanyProfile {
  const nested =
    me && typeof me.company_profile === "object" && me.company_profile
      ? (me.company_profile as Record<string, unknown>)
      : {};
  const account =
    me && typeof me.account === "object" && me.account
      ? (me.account as Record<string, unknown>)
      : {};
  const company_name = String(
    nested.company_name || me?.company_display_name || me?.company_name || "",
  ).trim();
  const email = String(nested.email || me?.email || account.email || "").trim();
  const phone = String(nested.phone || me?.phone || "").trim();
  const primary_niche = String(
    nested.primary_niche || me?.primary_niche || "",
  ).trim();
  const complete =
    typeof nested.complete === "boolean"
      ? nested.complete
      : Boolean(company_name && email);
  return { company_name, email, phone, primary_niche, complete };
}
