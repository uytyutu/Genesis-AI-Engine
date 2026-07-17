"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { BRAND_NAME, ASSISTANT_NAME } from "../lib/publicBrand";
import { CONTACT_EMAIL } from "../lib/siteConfig";

const LEGAL_MORE = [
  { href: "/impressum", label: "Impressum" },
  { href: "/agb", label: "AGB" },
  { href: "/widerruf", label: "Widerruf" },
  { href: "/cookies", label: "Cookies" },
  { href: "/ai-disclaimer", label: "KI-Hinweis" },
  { href: "/intellectual-property", label: "Urheberrecht" },
] as const;

export function PublicSiteFooter() {
  const { t } = useTranslation("common");
  const mainLinks = [
    { href: "/trust", label: t("footer.about") },
    { href: "/datenschutz", label: t("footer.privacy") },
    { href: "/faq", label: t("footer.support") },
    { href: "/kontakt", label: t("footer.contact") },
  ];

  return (
    <footer className="mt-16 border-t border-white/5 pt-8 pb-6">
      <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold">{BRAND_NAME}</p>
          <p className="mt-2 text-sm text-genesis-muted">
            {t("footer.tagline", { name: ASSISTANT_NAME })}
          </p>
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="mt-3 inline-block text-sm text-genesis-accent hover:underline"
          >
            {CONTACT_EMAIL}
          </a>
        </div>
        <nav aria-label={t("footer.mainNav")} className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
          {mainLinks.map((l) => (
            <Link key={l.href} href={l.href} className="text-genesis-muted hover:text-white">
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
      <details className="mt-6 text-sm">
        <summary className="cursor-pointer text-genesis-muted hover:text-white">
          {t("footer.legal")}
        </summary>
        <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
          {LEGAL_MORE.map((l) => (
            <li key={l.href}>
              <Link href={l.href} className="text-genesis-muted hover:text-white">
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </details>
      <p className="mt-8 text-center text-[11px] text-genesis-muted/80">
        © {new Date().getFullYear()} {BRAND_NAME}
      </p>
    </footer>
  );
}
