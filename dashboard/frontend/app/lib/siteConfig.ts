export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.trim() || "https://virtuscore.com";

export const SITE_NAME = "Virtus Core";
export const SITE_TAGLINE = "Vector · Digital Company";
/** Public contact — override via NEXT_PUBLIC_SUPPORT_EMAIL when DNS is ready. */
export const CONTACT_EMAIL =
  process.env.NEXT_PUBLIC_SUPPORT_EMAIL?.trim() ||
  process.env.NEXT_PUBLIC_CONTACT_EMAIL?.trim() ||
  "hello@virtuscore.com";

/** Filled via env after Gewerbeanmeldung — DOB must never be published */
export const LEGAL = {
  fullName: process.env.NEXT_PUBLIC_LEGAL_NAME ?? "Ramish Oltiiev",
  address:
    process.env.NEXT_PUBLIC_LEGAL_ADDRESS ?? "Tornaer Straße 23, 01237 Dresden",
  phone: process.env.NEXT_PUBLIC_LEGAL_PHONE ?? "",
  vatId: process.env.NEXT_PUBLIC_LEGAL_VAT_ID ?? "",
};

export const LEGAL_PENDING = !LEGAL.fullName || !LEGAL.address;
