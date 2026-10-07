import fs from "fs";

const s = fs.readFileSync("src/lib/i18n/dictionaries.ts", "utf8");

function extract(name) {
  const start = s.indexOf(`const ${name}: Dict = {`);
  const brace = s.indexOf("{", start);
  let i = brace;
  let depth = 0;
  for (; i < s.length; i++) {
    if (s[i] === "{") depth++;
    else if (s[i] === "}") {
      depth--;
      if (depth === 0) {
        i++;
        break;
      }
    }
  }
  const body = s.slice(brace + 1, i - 1);
  const o = {};
  for (const m of body.matchAll(/"([^"]+)":\s*"((?:\\.|[^"])*)"/g)) {
    o[m[1]] = m[2];
  }
  return o;
}

const en = extract("en");
const ru = extract("ru");
const de = extract("de");
const uk = extract("uk");

const need = [
  "nav.leave",
  "leave.title",
  "leave.eyebrow",
  "leave.sub",
  "leave.createLink",
  "leave.openSecrets",
  "leave.homeCta",
  "leave.alreadyLink",
  "viral.hub.think.title",
  "viral.hub.think.blurb",
  "viral.hub.think.price",
  "viral.hub.map.title",
  "loops.honestLive",
];

for (const k of need) {
  console.log(k, {
    en: en[k] ?? "MISSING",
    ru: ru[k] ?? "MISSING",
    de: de[k] ?? "MISSING",
  });
}

const missRu = Object.keys(en).filter((k) => !ru[k]);
const missDe = Object.keys(en).filter((k) => !de[k]);
console.log("\nen", Object.keys(en).length, "ru", Object.keys(ru).length, "de", Object.keys(de).length, "uk", Object.keys(uk).length);
console.log("missing in ru", missRu.length);
console.log(
  missRu
    .filter(
      (k) =>
        k.startsWith("leave.") ||
        k.startsWith("viral.") ||
        k.startsWith("loops.") ||
        k === "nav.leave" ||
        k.startsWith("common.") ||
        k.startsWith("home.")
    )
    .join("\n")
);
console.log("\nmissing in de (leave/viral)", missDe.filter((k) => k.startsWith("leave.") || k.startsWith("viral.") || k === "nav.leave").length);
