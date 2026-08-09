import type { MetadataRoute } from "next";
import { SITE_URL } from "./lib/siteConfig";

/**
 * P0 — Only public marketing/legal pages are crawlable.
 * All CEO / client / API / studio paths are disallowed.
 *
 * Do NOT use a catch-all `Disallow: /` — strict parsers (TikTok URL checks)
 * treat it as "site closed" and ignore path-level Allow rules.
 */
export default function robots(): MetadataRoute.Robots {
  const publicAllow = [
    "/site",
    "/services",
    "/products",
    "/order",
    "/pricing",
    "/faq",
    "/kontakt",
    "/trust",
    "/impressum",
    "/datenschutz",
    "/agb",
    "/widerruf",
    "/cookies",
    "/ai-disclaimer",
    "/intellectual-property",
  ];

  const privateDisallow = [
    "/owner-gate",
    "/owner",
    "/admin",
    "/vector",
    "/workspace",
    "/studio",
    "/dashboard",
    "/client",
    "/projects",
    "/business",
    "/finance",
    "/company",
    "/ai",
    "/cursor",
    "/revenue",
    "/marketplace",
    "/monitor",
    "/dev",
    "/check",
    "/create",
    "/settings",
    "/setup",
    "/launch",
    "/journal",
    "/opportunities",
    "/acquisition",
    "/support",
    "/scanner",
    "/growth",
    "/tasks",
    "/tiktok-horizon",
    "/horizon",
    "/ceo-site",
    "/engine",
    "/reviews",
    "/capture",
    "/api/",
    "/portal/",
    "/package-previews/",
  ];

  return {
    rules: [
      {
        userAgent: "*",
        allow: publicAllow,
        disallow: privateDisallow,
      },
      // TikTok / ByteDance crawlers — explicit allow for legal URL validation.
      {
        userAgent: ["Bytespider", "TikTokSpider", "TikTok"],
        allow: ["/agb", "/datenschutz", "/impressum", "/cookies", "/widerruf"],
        disallow: privateDisallow,
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
