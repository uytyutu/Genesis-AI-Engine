import type { MetadataRoute } from "next";
import { SITE_URL } from "./lib/siteConfig";

/**
 * P0 — Only public marketing/legal pages are crawlable.
 * All CEO / client / API / studio paths are disallowed.
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: [
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
      ],
      disallow: [
        "/",
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
        "/ceo-site",
        "/engine",
        "/reviews",
        "/capture",
        "/api/",
        "/portal/",
        "/package-previews/",
      ],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
