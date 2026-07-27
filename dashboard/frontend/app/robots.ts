import type { MetadataRoute } from "next";
import { SITE_URL } from "./lib/siteConfig";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: ["/site", "/services", "/order", "/pricing", "/faq", "/kontakt", "/impressum", "/datenschutz", "/agb"],
      disallow: ["/", "/finance", "/business", "/company", "/ai", "/cursor", "/revenue", "/marketplace", "/monitor", "/dev", "/check", "/create", "/settings", "/launch", "/opportunities", "/acquisition", "/client", "/projects", "/products", "/growth", "/tasks", "/owner-gate", "/api/"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
