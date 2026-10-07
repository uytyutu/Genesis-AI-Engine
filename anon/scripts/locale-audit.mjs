/**
 * Fail if homepage HTML for a forced locale still contains banned internal/EN leaks
 * when locale=ru was requested via cookie simulation is hard on static HTML —
 * instead audit source for forbidden UI string patterns.
 */
import fs from "fs";
import path from "path";

const ROOT = path.join(process.cwd(), "src");
const BANNED = [
  />\s*SEND\s*</,
  />\s*OPEN WHEN\s*</,
  /Send a moment\./,
  /Play something together/,
  /Emotional messaging/,
  /ANON sells a moment/,
  /Moments layer/,
  /Privacy-first\. Real anonymity/,
  /Play with your crew/,
  /Team vs team/,
  /Hidden missions/,
];

const IGNORE = ["dictionaries.ts", "pricing.ts", "catalog.ts", "stripe.ts", "api/"];

let bad = 0;
function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    const rel = path.relative(ROOT, p).replace(/\\/g, "/");
    if (IGNORE.some((i) => rel.includes(i))) continue;
    const st = fs.statSync(p);
    if (st.isDirectory()) walk(p);
    else if (/\.(tsx|ts)$/.test(name)) {
      const text = fs.readFileSync(p, "utf8");
      for (const re of BANNED) {
        if (re.test(text)) {
          console.error("LEAK", rel, String(re));
          bad++;
        }
      }
    }
  }
}

walk(ROOT);
if (bad) {
  console.error(`locale-audit FAIL (${bad})`);
  process.exit(1);
}
console.log("locale-audit PASS");
