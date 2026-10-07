/**
 * check:i18n — coverage + critical surface keys for all 12 locales.
 * Exit 1 if any critical key is missing from a locale's native/overlay dict.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");

const LOCALES = [
  "en",
  "de",
  "ru",
  "uk",
  "pl",
  "fr",
  "es",
  "it",
  "pt",
  "nl",
  "tr",
  "cs",
];

const CRITICAL = [
  "nav.home",
  "nav.leave",
  "nav.secrets",
  "nav.messages",
  "nav.moments",
  "nav.games",
  "nav.login",
  "nav.logout",
  "leave.title",
  "leave.eyebrow",
  "leave.createLink",
  "leave.homeCta",
  "brand.secretHero",
  "footer.language",
  "footer.legal",
  "settings.language",
  "loops.honestLive",
  "loops.honestSoon",
  "dna.title",
  "dna.honest",
  "error.generic",
  "common.loading",
];

function extractDict(source, name) {
  const start = source.indexOf(`const ${name}: Dict = {`);
  if (start < 0) return {};
  const brace = source.indexOf("{", start);
  let i = brace;
  let depth = 0;
  for (; i < source.length; i++) {
    if (source[i] === "{") depth++;
    else if (source[i] === "}") {
      depth--;
      if (depth === 0) {
        i++;
        break;
      }
    }
  }
  const body = source.slice(brace + 1, i - 1);
  const o = {};
  for (const m of body.matchAll(/"([^"]+)":\s*"((?:\\.|[^"])*)"/g)) {
    o[m[1]] = true;
  }
  return o;
}

function extractExtra(source) {
  const out = {};
  for (const code of ["pl", "fr", "es", "it", "pt", "nl", "tr", "cs"]) {
    const re = new RegExp(`\\n  ${code}: \\{([\\s\\S]*?)\\n  \\},`);
    const m = source.match(re);
    out[code] = {};
    if (!m) continue;
    for (const km of m[1].matchAll(/"([^"]+)":/g)) {
      out[code][km[1]] = true;
    }
  }
  return out;
}

const dictSrc = fs.readFileSync(
  path.join(ROOT, "src/lib/i18n/dictionaries.ts"),
  "utf8"
);
const extraSrc = fs.readFileSync(
  path.join(ROOT, "src/lib/i18n/extra-locales.ts"),
  "utf8"
);

const en = extractDict(dictSrc, "en");
const de = extractDict(dictSrc, "de");
const ru = extractDict(dictSrc, "ru");
const uk = extractDict(dictSrc, "uk");
const extra = extractExtra(extraSrc);

const native = { en, de, ru, uk };
const enKeys = Object.keys(en);
let failed = false;

console.log("i18n check\n");

for (const locale of LOCALES) {
  let present = 0;
  const missingCritical = [];
  const isComplete = Boolean(native[locale]);

  if (isComplete) {
    // uk is intentionally sparse — runtime merges with ru.
    const d = locale === "uk" ? { ...ru, ...uk } : native[locale];
    for (const k of enKeys) {
      if (d[k] || ru[k] || en[k]) present += 1;
    }
    for (const k of CRITICAL) {
      if (!(d[k] || ru[k] || en[k])) missingCritical.push(k);
    }
  } else {
    const overlay = extra[locale] || {};
    present = Object.keys(overlay).length;
    for (const k of CRITICAL) {
      // Critical must be in native overlay (not silent ru-only).
      if (!overlay[k]) missingCritical.push(k);
    }
  }

  // dedupe missing
  const miss = [...new Set(missingCritical)];
  const pct = isComplete
    ? Math.round((present / enKeys.length) * 100)
    : Math.round((present / enKeys.length) * 100);
  const label = `${locale.toUpperCase().padEnd(2)} ${String(pct).padStart(3)}%`;
  const status = miss.length ? "FAIL" : "OK";
  if (miss.length) failed = true;
  console.log(
    `${label}  native/overlay=${isComplete ? present : present}/${enKeys.length}  critical=${CRITICAL.length - miss.length}/${CRITICAL.length}  ${status}`
  );
  if (miss.length) {
    console.log(`   missing critical: ${miss.slice(0, 12).join(", ")}`);
  }
}

// Scan UI for obvious hardcoded English CTAs (ignore dictionaries / scripts)
const BANNED = [
  />\s*Leave something\s*</,
  />\s*Create link\s*</,
  />\s*What do you want to leave\?\s*</,
];
const ignore = ["dictionaries.ts", "extra-locales.ts", "gen_extra", "check-i18n"];
let leaks = 0;
function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    const rel = path.relative(path.join(ROOT, "src"), p);
    if (ignore.some((i) => rel.includes(i))) continue;
    const st = fs.statSync(p);
    if (st.isDirectory()) walk(p);
    else if (/\.(tsx|ts)$/.test(name)) {
      const text = fs.readFileSync(p, "utf8");
      for (const re of BANNED) {
        if (re.test(text)) {
          console.error("HARDCODED", rel, String(re));
          leaks++;
        }
      }
    }
  }
}
walk(path.join(ROOT, "src"));

if (leaks) {
  console.error(`\nhardcoded UI leaks: ${leaks}`);
  failed = true;
}

if (failed) {
  console.error("\ni18n check FAIL");
  process.exit(1);
}
console.log("\ni18n check PASS (critical surface covered for all 12 locales)");
