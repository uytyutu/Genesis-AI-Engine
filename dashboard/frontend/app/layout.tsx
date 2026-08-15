import { cookies } from "next/headers";
import type { Metadata } from "next";
import { AppShell } from "./components/AppShell";
import { LocaleProvider } from "./context/LocaleContext";
import { ToastProvider } from "./components/ToastProvider";
import { SITE_URL } from "./lib/siteConfig";
import { DEFAULT_UI_LOCALE, isPlatformLocale } from "./lib/locale/types";
import type { UiLocale } from "./lib/locale/types";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Virtus Core",
    template: "%s · Virtus Core",
  },
  description: "Virtus Core — Vector ведёт ваш проект: чат, черновик сайта и оформление в одном рабочем месте.",
  // P0 — default noindex; public marketing pages opt in via publicPageMetadata.
  robots: {
    index: false,
    follow: false,
    nocache: true,
    googleBot: {
      index: false,
      follow: false,
      noimageindex: true,
    },
  },
  icons: {
    icon: [
      { url: "/brand/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/brand/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/brand/vector-mark.svg", type: "image/svg+xml" },
    ],
    apple: [{ url: "/brand/apple-touch-icon.png", sizes: "180x180" }],
  },
  manifest: "/manifest.webmanifest",
  other: {
    "virtus-git-commit":
      process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 12) ||
      process.env.NEXT_PUBLIC_GIT_COMMIT ||
      "local",
    // Meta Business domain verification (beta.genesis-ai-engine.com)
    "facebook-domain-verification": "ca153v2cn5616g7usu96lb5iyzcmmr",
  },
};

function readInitialLocale(raw: string | undefined): UiLocale {
  return isPlatformLocale(raw) ? raw : DEFAULT_UI_LOCALE;
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const jar = await cookies();
  const raw = jar.get("virtus_ui_locale")?.value;
  const localeFromCookie = isPlatformLocale(raw);
  const initialLocale = readInitialLocale(raw);

  return (
    <html lang={initialLocale}>
      <body className="genesis-os-shell overflow-x-hidden antialiased">
        <LocaleProvider
          initialLocale={initialLocale}
          localeFromCookie={localeFromCookie}
        >
          <ToastProvider>
            <AppShell>{children}</AppShell>
          </ToastProvider>
        </LocaleProvider>
      </body>
    </html>
  );
}
