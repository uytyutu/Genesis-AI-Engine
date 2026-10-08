import type { Metadata } from "next";
import { Bricolage_Grotesque, Source_Sans_3 } from "next/font/google";
import { VieworaShell } from "./components/VieworaShell";

const display = Bricolage_Grotesque({
  subsets: ["latin", "latin-ext"],
  variable: "--font-viewora-display",
  weight: ["500", "700", "800"],
});

const body = Source_Sans_3({
  subsets: ["latin", "latin-ext", "cyrillic"],
  variable: "--font-viewora-body",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "Virtus Video AI — Content Studio",
    template: "%s · Virtus Video AI",
  },
  description:
    "Virtus Video AI — professional AI Content Studio. Describe it. Upload it. Remix it. Modes, Hook Lab, Watchability Score, Product Ads, Podcast→Shorts. Create something that gets watched.",
  robots: { index: true, follow: true },
  openGraph: {
    title: "Virtus Video AI — Create something that gets watched.",
    description:
      "Professional AI video & content factory by Virtus Core. Not a model picker — an outcome studio.",
    type: "website",
  },
};

export default function VieworaLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={`${display.variable} ${body.variable}`}>
      <VieworaShell>{children}</VieworaShell>
    </div>
  );
}
