/**
 * Writes public/build-info.json so Production can be compared to local git HEAD.
 * Run automatically before `next build`.
 */
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

function gitShort() {
  try {
    return execSync("git rev-parse --short HEAD", { encoding: "utf8" }).trim();
  } catch {
    return process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 12) || "unknown";
  }
}

function gitFull() {
  try {
    return execSync("git rev-parse HEAD", { encoding: "utf8" }).trim();
  } catch {
    return process.env.VERCEL_GIT_COMMIT_SHA || "unknown";
  }
}

const out = {
  git_commit: gitShort(),
  git_commit_full: gitFull(),
  built_at: new Date().toISOString(),
  deploy_status: "SUCCESS",
  source: process.env.VERCEL ? "vercel" : "local_build",
};

const dest = path.join(__dirname, "..", "public", "build-info.json");
fs.mkdirSync(path.dirname(dest), { recursive: true });
fs.writeFileSync(dest, JSON.stringify(out, null, 2) + "\n", "utf8");
console.log("build-info.json →", out.git_commit);
