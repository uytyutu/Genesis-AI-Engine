/** Shared company profile helpers — prefer Business Profile SSOT when present. */

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
  const bpWrap =
    me && typeof me.business_profile === "object" && me.business_profile
      ? (me.business_profile as Record<string, unknown>)
      : {};
  const bp =
    bpWrap && typeof bpWrap.profile === "object" && bpWrap.profile
      ? (bpWrap.profile as Record<string, unknown>)
      : {};
  const bpContacts =
    bp && typeof bp.contacts === "object" && bp.contacts
      ? (bp.contacts as Record<string, unknown>)
      : {};
  const nested =
    me && typeof me.company_profile === "object" && me.company_profile
      ? (me.company_profile as Record<string, unknown>)
      : {};
  const account =
    me && typeof me.account === "object" && me.account
      ? (me.account as Record<string, unknown>)
      : {};
  const company_name = String(
    bp.company_name ||
      nested.company_name ||
      me?.company_display_name ||
      me?.company_name ||
      "",
  ).trim();
  const email = String(
    bpContacts.email || nested.email || me?.email || account.email || "",
  ).trim();
  const phone = String(
    bpContacts.phone || nested.phone || me?.phone || "",
  ).trim();
  const primary_niche = String(
    bp.niche || nested.primary_niche || me?.primary_niche || "",
  ).trim();
  const complete =
    Boolean(bpWrap.has_profile) ||
    (typeof nested.complete === "boolean"
      ? nested.complete
      : Boolean(company_name && email));
  return { company_name, email, phone, primary_niche, complete };
}
