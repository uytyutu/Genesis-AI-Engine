import type { Metadata } from "next";
import { CONTACT_EMAIL, SITE_NAME, SITE_TAGLINE, SITE_URL } from "./siteConfig";

export function publicPageMetadata(
  title: string,
  description: string,
  path: string
): Metadata {
  const url = `${SITE_URL}${path}`;
  return {
    title: `${title} — ${SITE_NAME}`,
    description,
    openGraph: {
      type: "website",
      locale: "ru_RU",
      url,
      siteName: SITE_NAME,
      title: `${title} — ${SITE_NAME}`,
      description,
    },
    twitter: {
      card: "summary_large_image",
      title: `${title} — ${SITE_NAME}`,
      description,
    },
    alternates: { canonical: url },
    other: { contact: CONTACT_EMAIL },
  };
}

export const DEFAULT_PUBLIC_DESCRIPTION =
  "Современный сайт для бизнеса под ключ: цена сразу, оплата онлайн, статус заказа. " +
  SITE_TAGLINE;
