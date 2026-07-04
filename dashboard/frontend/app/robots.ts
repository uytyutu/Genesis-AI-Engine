import type { MetadataRoute } from "next";
import { SITE_URL } from "./lib/siteConfig";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: ["/site", "/services", "/order", "/pricing", "/faq", "/kontakt", "/impressum", "/datenschutz", "/agb"],
      disallow: ["/finance", "/company", "/ai", "/cursor", "/revenue", "/marketplace", "/monitor", "/dev", "/check", "/create", "/settings", "/launch", "/opportunities", "/projects", "/products", "/growth", "/tasks"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
