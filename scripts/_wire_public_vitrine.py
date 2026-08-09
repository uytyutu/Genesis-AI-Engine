"""Wire AppStoreHub to publicVitrineCatalog + commercial price SSOT."""
from pathlib import Path

path = Path("dashboard/frontend/app/components/storefront/AppStoreHub.tsx")
text = path.read_text(encoding="utf-8")

old_imp = """import {
  CHATBOT_PRICE_TIERS,
  STORE_MODULES_PRIMARY,
  STORE_MODULES_SOON,
  WEBSITE_COMPARE_ROWS,
  WEBSITE_PRICE_TIERS,
  type StoreModule,
} from \"./modules\";
import { ServiceCatalogGrid } from \"../ServiceCatalogCards\";"""

new_imp = """import {
  CHATBOT_PRICE_TIERS,
  STORE_MODULES_PRIMARY,
  STORE_MODULES_SOON,
  WEBSITE_COMPARE_ROWS,
  WEBSITE_PRICE_TIERS,
  type StoreModule,
} from \"./modules\";
import { ServiceCatalogGrid } from \"../ServiceCatalogCards\";
import { LANDING_PACKAGES_EUR } from \"../../lib/commercialCatalog\";
import {
  PUBLIC_DENTAL_TIER_COMPARE,
  PUBLIC_VITRINE_EXAMPLES,
} from \"../../lib/publicVitrineCatalog\";"""

if old_imp not in text:
    raise SystemExit("import block not found")
text = text.replace(old_imp, new_imp, 1)

start = text.index("  const exampleProjects = [")
end = text.index("  return (", start)
new_block = """  const websitePriceLine = `Website · ab ${LANDING_PACKAGES_EUR.standalone} €`;
  const storePriceLine = \"AI Store · ab 799 €\";
  const exampleProjects = PUBLIC_VITRINE_EXAMPLES.map((ex) => ({
    ...ex,
    price: ex.priceKind === \"store\" ? storePriceLine : websitePriceLine,
  }));

"""
text = text[:start] + new_block + text[end:]

# Tier compare block: find LUMIA link section and rewrite the whole compare box content
marker = '{t(`${ns}.examples.tierCompareTitle`'
if marker not in text:
    raise SystemExit("tier compare marker missing")

# Replace defaultValue price hint + links by rewriting from rounded-xl tier box
old_tier_start = text.index(
    '<div className="rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-left">'
)
# Only the first one after examples - there may be several; find the one with tierCompareTitle
idx = text.index(marker)
# walk back to the div
old_tier_start = text.rfind(
    '<div className="rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-left">',
    0,
    idx,
)
old_tier_end = text.index("</div>\n      </section>", old_tier_start) + len("</div>")

new_tier = """<div className="rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-left">
          <p className="text-xs font-semibold text-white">
            {t(`${ns}.examples.tierCompareTitle`, {
              defaultValue: "Gleiche Nische · drei Design-Stufen (Unterschied sehen)",
            })}
          </p>
          <p className="mt-1 text-[11px] text-zinc-500">
            {t(`${ns}.examples.tierCompareHint`, {
              defaultValue: `Basic · Business · Premium (Zahnarzt) — gleicher Branch, unterschiedliche Tiefe. Kaufmodell: Standalone ab ${LANDING_PACKAGES_EUR.standalone} €.`,
            })}
          </p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {PUBLIC_DENTAL_TIER_COMPARE.map((tier) => (
              <a
                key={tier.id}
                href={tier.href}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-white/15 px-2.5 py-1 text-zinc-200 hover:border-emerald-400/50"
              >
                {tier.label}
              </a>
            ))}
          </div>
        </div>"""

text = text[:old_tier_start] + new_tier + text[old_tier_end:]

# Fix remaining hardcoded Path-A euro amounts in this file (public copy)
replacements = {
    '"From 1 500–5 000 €", "From 199 €"': '"From 1 500–5 000 €", `From ${LANDING_PACKAGES_EUR.standalone} €`',
    "Website from 199 € · AI Store from 799 € · often ready in minutes": "Website from ${LANDING_PACKAGES_EUR.standalone} € · AI Store from 799 € · often ready in minutes",
    "Pages, contact path, Impressum — visitors understand who you are and how to reach you. From 199 €.": "Pages, contact path, Impressum — visitors understand who you are and how to reach you. From ${LANDING_PACKAGES_EUR.standalone} €.",
    "What you get for 199 €, 399 € and 699 € — same amounts at checkout.": "What you get for Standalone / Connected — same amounts at checkout (from ${LANDING_PACKAGES_EUR.standalone} €).",
}
for a, b in replacements.items():
    if a in text:
        # defaultValue strings need template literals
        if "Website from ${" in b or "From ${" in b or "from ${" in b:
            # wrap surrounding defaultValue quotes into backticks when needed — simple replace inside defaultValue
            text = text.replace(a, b)
        else:
            text = text.replace(a, b)

# Convert defaultValue strings that now contain ${ to template literals where still quoted with "
# Fix hero/subtitle lines that got ${ inside double quotes
import re

def fix_default_value_templates(s: str) -> str:
    def repl(m: re.Match[str]) -> str:
        inner = m.group(1)
        if "${" in inner and "`" not in m.group(0):
            return "defaultValue: `" + inner.replace("`", "\\`") + "`"
        return m.group(0)

    return re.sub(r'defaultValue:\s*"([^"]*\$\{[^"]*)"', repl, s)

text = fix_default_value_templates(text)

# why.rowPrice array entry — may still be string "From 199"
text = text.replace('"From 199 €"', "`From ${LANDING_PACKAGES_EUR.standalone} €`")

path.write_text(text, encoding="utf-8")
print("ok")
print("has catalog", "PUBLIC_VITRINE_EXAMPLES" in path.read_text(encoding="utf-8"))
print("has lumia public?", "studio-lumia" in path.read_text(encoding="utf-8"))
