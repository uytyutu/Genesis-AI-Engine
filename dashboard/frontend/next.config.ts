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
  // S1.2 baseline CSP — allow Next runtime; tighten further in later slices.
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob: https:",
      "font-src 'self' data:",
      "connect-src 'self' http://127.0.0.1:* http://localhost:* https:",
      "media-src 'self' blob:",
      "frame-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join("; "),
  },
];

/** TikTok / OAuth portals embed Privacy + Terms in iframe — only these two paths. */
const legalEmbedCsp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "connect-src 'self' http://127.0.0.1:* http://localhost:* https:",
  "media-src 'self' blob:",
  "frame-src 'self'",
  "frame-ancestors *",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const securityHeadersNoFrameDeny = securityHeaders.filter(
  (h) => h.key !== "X-Frame-Options" && h.key !== "Content-Security-Policy",
);

const legalEmbedHeaders = [
  ...securityHeadersNoFrameDeny,
  // No X-Frame-Options — required for cross-origin TikTok portal iframe.
  { key: "Content-Security-Policy", value: legalEmbedCsp },
];

// Docker/VPS: INTERNAL_API_URL=http://genesis:8000 for server rewrites.
// Browser: NEXT_PUBLIC_API_URL empty → same-origin /api via nginx.
const apiBase = (
  process.env.INTERNAL_API_URL?.trim() ||
  process.env.NEXT_PUBLIC_API_URL?.trim() ||
  "http://localhost:8000"
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
      // Root + everything except Privacy/Terms keep clickjacking DENY.
      {
        source: "/",
        headers: securityHeaders,
      },
      {
        source: "/((?!agb$|datenschutz$).*)",
        headers: securityHeaders,
      },
      {
        source: "/package-previews/:path*",
        headers: [
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "Cache-Control", value: "public, max-age=300, must-revalidate" },
        ],
      },
      {
        source: "/agb",
        headers: legalEmbedHeaders,
      },
      {
        source: "/datenschutz",
        headers: legalEmbedHeaders,
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
        source: "/api/acquisition/:path*",
        destination: `${apiBase}/api/acquisition/:path*`,
      },
      {
        source: "/api/support/:path*",
        destination: `${apiBase}/api/support/:path*`,
      },
      {
        source: "/api/leads/:path*",
        destination: `${apiBase}/api/leads/:path*`,
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
      {
        source: "/portal/:path*",
        destination: `${apiBase}/portal/:path*`,
      },
      // Mission Control boards (Возможности / Adapter / Work Farm) — same-origin
      {
        source: "/api/:path*",
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
