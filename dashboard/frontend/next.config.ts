import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    // microphone=(self) — required for getUserMedia / voice chat on /site
    value: "camera=(), microphone=(self), geolocation=()",
  },
];

const apiBase = (
  process.env.NEXT_PUBLIC_API_URL?.trim() || "http://localhost:8000"
).replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  productionBrowserSourceMaps: false,
  experimental: {
    // LLM via Ollama can exceed the default 30s rewrite proxy limit.
    proxyTimeout: 120_000,
  },
  async headers() {
    // Package demo HTML is embedded in <iframe> on /site and /order.
    // Global X-Frame-Options: DENY would blank those previews (PC + mobile).
    // Later matching sources override earlier ones for the same header key.
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
      {
        source: "/package-previews/:path*",
        headers: [{ key: "X-Frame-Options", value: "SAMEORIGIN" }],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/public/:path*",
        destination: `${apiBase}/api/public/:path*`,
      },
      {
        source: "/api/sales/:path*",
        destination: `${apiBase}/api/sales/:path*`,
      },
      {
        source: "/api/factory/:path*",
        destination: `${apiBase}/api/factory/:path*`,
      },
      {
        source: "/research-3d/:path*",
        destination: `${apiBase}/research-3d/:path*`,
      },
      {
        source: "/api/webhooks/stripe",
        destination: `${apiBase}/api/webhooks/stripe`,
      },
      {
        source: "/webhooks/stripe",
        destination: `${apiBase}/webhooks/stripe`,
      },
    ];
  },
};

export default nextConfig;
