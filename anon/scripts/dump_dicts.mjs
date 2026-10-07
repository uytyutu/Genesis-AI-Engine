import fs from "fs";

const s = fs.readFileSync("src/lib/i18n/dictionaries.ts", "utf8");

function extract(name) {
  const start = s.indexOf(`const ${name}: Dict = {`);
  if (start < 0) return {};
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
    o[m[1]] = m[2]
      .replace(/\\n/g, "\n")
      .replace(/\\"/g, '"')
      .replace(/\\\\/g, "\\");
  }
  return o;
}

const en = extract("en");
const de = extract("de");
const ru = extract("ru");
const uk = extract("uk");
console.log({
  en: Object.keys(en).length,
  de: Object.keys(de).length,
  ru: Object.keys(ru).length,
  uk: Object.keys(uk).length,
});
fs.writeFileSync(
  "scripts/_dicts_dump.json",
  JSON.stringify({ en, de, ru, uk })
);
console.log("dumped scripts/_dicts_dump.json");
