export function formatEur(value: number | undefined | null): string {
  return formatLocalizedMoney(value, "EUR");
}

const LOCALE_BY_CURRENCY: Record<string, string> = {
  EUR: "de-DE",
  PLN: "pl-PL",
  UAH: "uk-UA",
  CZK: "cs-CZ",
  USD: "en-US",
  GBP: "en-GB",
  CHF: "de-CH",
  AUD: "en-AU",
  BRL: "pt-BR",
  MXN: "es-MX",
  JPY: "ja-JP",
  KRW: "ko-KR",
  INR: "en-IN",
  AED: "ar-AE",
  SAR: "ar-SA",
  ZAR: "en-ZA",
  SGD: "en-SG",
  NZD: "en-NZ",
};

export function formatLocalizedMoney(
  value: number | undefined | null,
  currency: string = "EUR",
  locale?: string,
): string {
  const n = value ?? 0;
  const code = currency.toUpperCase();
  const loc = locale ?? LOCALE_BY_CURRENCY[code] ?? "de-DE";
  const fractionDigits = code === "PLN" || code === "UAH" || code === "CZK" ? 0 : 2;
  return new Intl.NumberFormat(loc, {
    style: "currency",
    currency: code,
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(n);
}

export function formatSignedEur(value: number): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${formatEur(value)}`;
}
