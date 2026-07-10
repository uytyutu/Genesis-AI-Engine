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
      text: "Ваши данные защищены согласно требованиям GDPR.",
    },
    {
      emoji: "📄",
      text: "Юридическая информация доступна в",
      links: [
        { href: "/impressum", label: "Impressum" },
        { href: "/datenschutz", label: "Datenschutz" },
      ],
    },
    {
      emoji: "🏢",
      text: "Virtus Core не продаёт персональные данные третьим лицам.",
    },
    {
      emoji: "✅",
      text: "До оплаты вы видите предварительную смету проекта.",
    },
    {
      emoji: "📦",
      text: "После оплаты вы получите полный комплект проекта:",
      bullets: [
        "ZIP",
        "исходный код",
        "инструкции",
        "права использования согласно условиям покупки",
      ],
    },
  ],
  subscription: [
    {
      emoji: "🔒",
      text: "Ваши данные защищены согласно требованиям GDPR.",
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
      text: "Virtus Core не продаёт персональные данные.",
    },
    {
      emoji: "✅",
      text: "Проект сохраняется внутри Virtus Core.",
    },
    {
      emoji: "🔄",
      text: "Vector продолжает сопровождать проект в рамках подписки.",
    },
  ],
};

export function parseOrderPurchaseType(value: string | null | undefined): OrderPurchaseType {
  return value === "subscription" ? "subscription" : "one_time";
}
