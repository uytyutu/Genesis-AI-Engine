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
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
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
