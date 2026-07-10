export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://genesis-ai-engine.vercel.app";

export const SITE_NAME = "Virtus Core";
export const SITE_TAGLINE = "Vector · Digital Company";
export const CONTACT_EMAIL = "hello@genesis-ai-engine.com";

/** Filled via env after Gewerbeanmeldung */
export const LEGAL = {
  fullName: process.env.NEXT_PUBLIC_LEGAL_NAME ?? "",
  address: process.env.NEXT_PUBLIC_LEGAL_ADDRESS ?? "",
  phone: process.env.NEXT_PUBLIC_LEGAL_PHONE ?? "",
  vatId: process.env.NEXT_PUBLIC_LEGAL_VAT_ID ?? "",
};

export const LEGAL_PENDING = !LEGAL.fullName || !LEGAL.address;
