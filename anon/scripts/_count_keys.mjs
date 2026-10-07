import fs from "fs";
const s = fs.readFileSync("src/lib/i18n/dictionaries.ts", "utf8");
function extract(name, next) {
  const re = new RegExp(`const ${name}: Dict = \\{([\\s\\S]*?)\\n\\};\\n\\nconst ${next}`);
  const m = s.match(re);
  if (!m) return new Set();
  return new Set([...m[1].matchAll(/"([^"]+)":/g)].map((x) => x[1]));
}
const en = extract("en", "de");
const de = extract("de", "ru");
const ru = extract("ru", "uk");
const uk = extract("uk", "DICTS");
console.log({ en: en.size, de: de.size, ru: ru.size, uk: uk.size });
console.log("en-not-ru", [...en].filter((k) => !ru.has(k)).length);
console.log("en-not-de", [...en].filter((k) => !de.has(k)).length);
console.log("en-not-uk", [...en].filter((k) => !uk.has(k)).length);
console.log("sample missing ru", [...en].filter((k) => !ru.has(k)).slice(0, 30));
