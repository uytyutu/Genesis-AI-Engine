import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Native SQLite binding — keep outside the Next bundler.
  serverExternalPackages: ["better-sqlite3", "libsql"],
  // Docker/OVH only — Vercel uses its own Next output.
  ...(process.env.VERCEL ? {} : { output: "standalone" as const }),
  // Repo has a root lockfile — pin tracing to anon/ so Docker standalone is correct.
  outputFileTracingRoot: path.join(__dirname),
  images: {
    remotePatterns: [],
  },
  async rewrites() {
    // Share links: /@username → public profile (middleware also rewrites).
    return [{ source: "/@:username", destination: "/u/:username" }];
  },
};

export default nextConfig;
