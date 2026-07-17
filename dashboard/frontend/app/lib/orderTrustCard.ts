export type OrderPurchaseType = "one_time" | "subscription";

export type OrderTrustLine = {
  emoji: string;
  text: string;
  links?: { href: string; label: string }[];
  bullets?: string[];
};

export const ORDER_TRUST_CONTENT: Record<OrderPurchaseType, OrderTrustLine[]> = {
  one_time: [
    {
      emoji: "🔒",
      text: "Ihre Daten sind gemäß den DSGVO-Anforderungen geschützt.",
    },
    {
      emoji: "📄",
      text: "Rechtliche Informationen finden Sie unter",
      links: [
        { href: "/impressum", label: "Impressum" },
        { href: "/datenschutz", label: "Datenschutz" },
      ],
    },
    {
      emoji: "🏢",
      text: "Virtus Core verkauft keine personenbezogenen Daten an Dritte.",
    },
    {
      emoji: "✅",
      text: "Vor der Zahlung sehen Sie die vorläufige Projektkalkulation.",
    },
    {
      emoji: "📦",
      text: "Nach der Zahlung erhalten Sie das vollständige Projektpaket:",
      bullets: [
        "ZIP",
        "Quellcode",
        "Anleitungen",
        "Nutzungsrechte gemäß Kaufbedingungen",
      ],
    },
  ],
  subscription: [
    {
      emoji: "🔒",
      text: "Ihre Daten sind gemäß den DSGVO-Anforderungen geschützt.",
    },
    {
      emoji: "📄",
      text: "",
      links: [
        { href: "/impressum", label: "Impressum" },
        { href: "/datenschutz", label: "Datenschutz" },
      ],
    },
    {
      emoji: "🏢",
      text: "Virtus Core verkauft keine personenbezogenen Daten.",
    },
    {
      emoji: "✅",
      text: "Das Projekt bleibt innerhalb von Virtus Core gespeichert.",
    },
    {
      emoji: "🔄",
      text: "Vector begleitet das Projekt weiterhin im Rahmen des Abos.",
    },
  ],
};

export function parseOrderPurchaseType(value: string | null | undefined): OrderPurchaseType {
  return value === "subscription" ? "subscription" : "one_time";
}
