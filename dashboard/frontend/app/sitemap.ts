import type { MetadataRoute } from "next";
import { SITE_URL } from "./lib/siteConfig";

const PATHS = [
  "/site",
  "/services",
  "/order",
  "/pricing",
  "/faq",
  "/kontakt",
  "/impressum",
  "/datenschutz",
  "/agb",
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
