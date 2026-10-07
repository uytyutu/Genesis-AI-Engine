import type { Metadata } from "next";
import { cookies } from "next/headers";
import { Fraunces, Manrope } from "next/font/google";
import { AppShell } from "@/components/AppShell";
import { I18nProvider } from "@/components/I18nProvider";
import { LOCALE_COOKIE } from "@/lib/i18n/core";
import { resolveLocale } from "@/lib/i18n/dictionaries";
import "./globals.css";

const display = Fraunces({
  variable: "--font-display",
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600", "700"],
});

const body = Manrope({
  variable: "--font-body",
  subsets: ["latin", "latin-ext", "cyrillic"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "ANON",
    template: "%s · ANON",
  },
  description: "ANON — say what you don't dare to say. Secret messages, moments, people.",
  metadataBase: new URL(
    (process.env.ANON_PUBLIC_URL || "").trim() || "http://localhost:3100"
  ),
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    apple: [{ url: "/apple-touch-icon.svg", type: "image/svg+xml" }],
    shortcut: ["/favicon.svg"],
  },
  openGraph: {
    title: "🔐 Someone left you a secret",
    description: "Open it on ANON.",
    type: "website",
    images: [{ url: "/brand/veil-mark.svg" }],
  },
  robots: { index: true, follow: true },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jar = await cookies();
  const initialLocale = resolveLocale(jar.get(LOCALE_COOKIE)?.value);

  return (
    <html lang={initialLocale}>
      <body className={`${display.variable} ${body.variable} antialiased`}>
        <I18nProvider initialLocale={initialLocale}>
          <AppShell>{children}</AppShell>
        </I18nProvider>
      </body>
    </html>
  );
}
