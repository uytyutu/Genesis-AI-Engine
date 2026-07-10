import type { MetadataRoute } from "next";
import { SITE_URL } from "./lib/siteConfig";

const PATHS = [
  "/site",
  "/services",
  "/order",
  "/products",
  "/pricing",
  "/faq",
  "/kontakt",
  "/impressum",
  "/datenschutz",
  "/agb",
  "/trust",
  "/widerruf",
  "/cookies",
  "/ai-disclaimer",
  "/intellectual-property",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return PATHS.map((path) => ({
    url: `${SITE_URL}${path}`,
    lastModified: now,
    changeFrequency: path === "/site" ? "weekly" : "monthly",
    priority: path === "/order" || path === "/site" ? 1 : 0.7,
  }));
}
