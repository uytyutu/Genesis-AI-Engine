/**
 * Legal entity loader — NEVER invents operator identity.
 * Sources (first match wins):
 * 1) anon/content/legal/entity.json (optional local copy of project entity)
 * 2) Same GENESIS_LEGAL_* / NEXT_PUBLIC_LEGAL_* ENV keys as Virtus
 */
import fs from "fs";
import path from "path";

export type LegalEntity = {
  full_name: string;
  trade_name: string;
  legal_form: string;
  address_street: string;
  address_zip: string;
  address_city: string;
  address_country: string;
  email: string;
  phone: string;
  website: string;
  vat_id: string;
  handelsregister: string;
  register_court: string;
  managing_director: string;
  documents_last_review: string;
  data_location: string;
  dpo_email: string;
  supervisory_authority: string;
};

const EMPTY: LegalEntity = {
  full_name: "",
  trade_name: "",
  legal_form: "",
  address_street: "",
  address_zip: "",
  address_city: "",
  address_country: "DE",
  email: "",
  phone: "",
  website: "",
  vat_id: "",
  handelsregister: "",
  register_court: "",
  managing_director: "",
  documents_last_review: "2026-07",
  data_location: "EU / Deutschland",
  dpo_email: "",
  supervisory_authority: "Sächsische Datenschutz- und Transparenzbeauftragte",
};

function fromEnv(): LegalEntity {
  const e = { ...EMPTY };
  e.full_name =
    process.env.GENESIS_LEGAL_OPERATOR_NAME?.trim() ||
    process.env.NEXT_PUBLIC_LEGAL_NAME?.trim() ||
    "";
  e.legal_form = process.env.GENESIS_LEGAL_LEGAL_FORM?.trim() || "";
  e.trade_name = process.env.GENESIS_LEGAL_TRADE_NAME?.trim() || "ANON";
  e.address_street = process.env.GENESIS_LEGAL_ADDRESS_STREET?.trim() || "";
  e.address_zip = process.env.GENESIS_LEGAL_ADDRESS_ZIP?.trim() || "";
  e.address_city = process.env.GENESIS_LEGAL_ADDRESS_CITY?.trim() || "";
  e.email =
    process.env.GENESIS_LEGAL_EMAIL?.trim() ||
    process.env.ANON_LEGAL_EMAIL?.trim() ||
    "";
  e.phone =
    process.env.GENESIS_LEGAL_PHONE?.trim() ||
    process.env.NEXT_PUBLIC_LEGAL_PHONE?.trim() ||
    "";
  e.website =
    process.env.ANON_PUBLIC_URL?.trim() ||
    process.env.GENESIS_PUBLIC_URL?.trim() ||
    "";
  e.vat_id =
    process.env.GENESIS_LEGAL_VAT_ID?.trim() ||
    process.env.NEXT_PUBLIC_LEGAL_VAT_ID?.trim() ||
    "";
  e.managing_director = process.env.GENESIS_LEGAL_MANAGING_DIRECTOR?.trim() || "";
  e.handelsregister = process.env.GENESIS_LEGAL_HANDELSREGISTER?.trim() || "";
  e.register_court = process.env.GENESIS_LEGAL_REGISTER_COURT?.trim() || "";
  e.dpo_email = e.email;
  const combined = process.env.NEXT_PUBLIC_LEGAL_ADDRESS?.trim() || "";
  if (!e.address_street && combined) e.address_street = combined;
  return e;
}

function fromFile(): LegalEntity | null {
  const p = path.join(process.cwd(), "content", "legal", "entity.json");
  if (!fs.existsSync(p)) return null;
  try {
    const raw = JSON.parse(fs.readFileSync(p, "utf8"));
    const op = raw.operator || raw;
    const dp = raw.data_processing || {};
    return {
      ...EMPTY,
      full_name: String(op.full_name || "").trim(),
      trade_name: String(op.trade_name || "ANON").trim(),
      legal_form: String(op.legal_form || "").trim(),
      address_street: String(op.address_street || "").trim(),
      address_zip: String(op.address_zip || "").trim(),
      address_city: String(op.address_city || "").trim(),
      address_country: String(op.address_country || "DE").trim(),
      email: String(op.email || "").trim(),
      phone: String(op.phone || "").trim(),
      website: String(op.website || "").trim(),
      vat_id: String(op.vat_id || "").trim(),
      handelsregister: String(op.handelsregister || "").trim(),
      register_court: String(op.register_court || "").trim(),
      managing_director: String(op.managing_director || "").trim(),
      documents_last_review: String(raw.documents_last_review || "2026-07"),
      data_location: String(dp.data_location || "EU / Deutschland"),
      dpo_email: String(dp.dpo_email || op.email || "").trim(),
      supervisory_authority: String(
        dp.supervisory_authority || EMPTY.supervisory_authority
      ),
    };
  } catch {
    return null;
  }
}

export function loadEntity(): { entity: LegalEntity; source: "file_entity" | "env_entity" } {
  const file = fromFile();
  if (file && file.full_name && file.address_street && file.address_city && file.email) {
    return { entity: file, source: "file_entity" };
  }
  return { entity: fromEnv(), source: "env_entity" };
}

export function impressumMissing(e: LegalEntity): string[] {
  const miss: string[] = [];
  if (!e.full_name) miss.push("full_name");
  if (!e.address_street) miss.push("address_street");
  if (!e.address_zip) miss.push("address_zip");
  if (!e.address_city) miss.push("address_city");
  if (!e.email) miss.push("email");
  return miss;
}

export function formatAddress(e: LegalEntity): string {
  return [e.address_street, `${e.address_zip} ${e.address_city}`.trim(), e.address_country]
    .filter(Boolean)
    .join("\n");
}
