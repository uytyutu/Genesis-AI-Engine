export function formatEur(value: number | undefined | null): string {
  const n = value ?? 0;
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

export function formatSignedEur(value: number): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${formatEur(value)}`;
}
