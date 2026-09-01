#!/usr/bin/env node
/** npm run vcore:routes */
"use strict";

const fs = require("fs");
const path = require("path");
const { findVcoreRoutes } = require("./lib/vcoreRouteFinder");

const OUT = path.join(__dirname, "..", ".runtime", "vcore_routes_last.json");

async function main() {
  const amount = process.argv.includes("--amount")
    ? process.argv[process.argv.indexOf("--amount") + 1]
    : "1000000";
  const report = await findVcoreRoutes({ amountHuman: amount });
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report, null, 2));
  const anyZc = report.routes.some((r) => r.classification === "ZERO_CAPITAL_EXECUTABLE");
  process.exitCode = anyZc ? 0 : 2;
}

main().catch((e) => {
  console.error(JSON.stringify({ ok: false, error: e.message || String(e) }, null, 2));
  process.exit(1);
});
