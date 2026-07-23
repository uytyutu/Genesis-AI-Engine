export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://beta.genesis-ai-engine.com";

export const SITE_NAME = "Virtus Core";
export const SITE_TAGLINE = "Vector · Digital Company";
export const CONTACT_EMAIL = "hello@genesis-ai-engine.com";

/** Filled via env after Gewerbeanmeldung — DOB must never be published */
export const LEGAL = {
  fullName: process.env.NEXT_PUBLIC_LEGAL_NAME ?? "Ramish Oltiiev",
  address:
    process.env.NEXT_PUBLIC_LEGAL_ADDRESS ?? "Tornaer Straße 23, 01237 Dresden",
  phone: process.env.NEXT_PUBLIC_LEGAL_PHONE ?? "",
  vatId: process.env.NEXT_PUBLIC_LEGAL_VAT_ID ?? "",
};

export const LEGAL_PENDING = !LEGAL.fullName || !LEGAL.address;
