import type { MetadataRoute } from "next";
import { SITE_URL } from "./lib/siteConfig";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: ["/site", "/services", "/products", "/order", "/pricing", "/faq", "/kontakt", "/trust", "/impressum", "/datenschutz", "/agb", "/widerruf", "/cookies", "/ai-disclaimer", "/intellectual-property"],
      disallow: ["/finance", "/company", "/ai", "/cursor", "/revenue", "/marketplace", "/monitor", "/dev", "/check", "/create", "/settings", "/launch", "/opportunities", "/acquisition", "/projects", "/products/", "/growth", "/tasks"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
