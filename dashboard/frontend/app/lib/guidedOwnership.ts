/**
 * B-001 Slice 4 — First Ownership: preview feels like the visitor's business.
 */

import { GUIDED_GOALS, type GuidedCommerceState, type GuidedGoalId, type LogoChoice } from "./guidedCommerce";

export const GUIDED_PRODUCT_PROMISE =
  "Справа — черновик, который собрал Vector. После оплаты вы получаете права на тот же результат.";

export type ProvenanceLine = {
  id: string;
  answer: string;
  becomes: string;
  done: boolean;
};

export function logoChoiceLabel(choice: LogoChoice): string {
  if (choice === "yes") return "ваш логотип";
  if (choice === "auto") return "автологотип из названия";
  if (choice === "no") return "без логотипа пока";
  return "";
}

export function buildPreviewProvenance(state: GuidedCommerceState): ProvenanceLine[] {
  const name = state.companyName.trim();
  const goalLabel = state.goalId
    ? (GUIDED_GOALS.find((g) => g.id === state.goalId)?.label ?? "")
    : "";
  const industry = getIndustryProfile(state.goalId);
  const lines: ProvenanceLine[] = [];

  if (state.goalId) {
    lines.push({
      id: "goal",
      answer: `Цель: «${goalLabel}»`,
      becomes: `тип бизнеса — ${industry.categoryLabel.toLowerCase()}`,
      done: true,
    });
  }
  if (name) {
    lines.push({
      id: "name",
      answer: `Название: «${name}»`,
      becomes: "вывеска, домен и шапка сайта",
      done: true,
    });
    lines.push({
      id: "colors",
      answer: `Название: «${name}»`,
      becomes: "цвета бренда и кнопка записи",
      done: true,
    });
  }
  if (state.logoChoice) {
    lines.push({
      id: "logo",
      answer: `Логотип: ${logoChoiceLabel(state.logoChoice)}`,
      becomes: "логотип на фасаде, визитке и в телефоне",
      done: true,
    });
  }
  if (state.goalId && name) {
    lines.push({
      id: "services",
      answer: `Тип: ${industry.categoryLabel}`,
      becomes: state.productId
        ? "тексты и услуги в черновике справа"
        : `услуги: ${industry.services.map((s) => s.label).join(", ")}`,
      done: Boolean(state.productId),
    });
  }

  return lines;
}

export type IndustryProfile = {
  id: string;
  categoryLabel: string;
  tagline: string;
  services: Array<{ icon: string; label: string }>;
  hours: string;
  phone: string;
  city: string;
  heroFrom: string;
  heroTo: string;
  accent: string;
};

const BEAUTY: IndustryProfile = {
  id: "beauty",
  categoryLabel: "Салон красоты",
  tagline: "Уход, стиль и забота о вас",
  services: [
    { icon: "✂️", label: "Стрижка" },
    { icon: "💅", label: "Маникюр" },
    { icon: "💇", label: "Окрашивание" },
    { icon: "✨", label: "Укладка" },
  ],
  hours: "Пн–Сб 9:00–19:00",
  phone: "+49 30 123 4567",
  city: "Berlin",
  heroFrom: "#3d2c29",
  heroTo: "#8b5a6b",
  accent: "#e8b4b8",
};

const CAFE: IndustryProfile = {
  id: "cafe",
  categoryLabel: "Кофейня",
  tagline: "Свежий кофе и уют каждый день",
  services: [
    { icon: "☕", label: "Кофе" },
    { icon: "🥐", label: "Выпечка" },
    { icon: "🥤", label: "Напитки" },
    { icon: "🍰", label: "Десерты" },
  ],
  hours: "Ежедневно 7:00–20:00",
  phone: "+49 30 987 6543",
  city: "München",
  heroFrom: "#2c2419",
  heroTo: "#6b4e3d",
  accent: "#d4a574",
};

const AUTO: IndustryProfile = {
  id: "auto",
  categoryLabel: "Автосервис",
  tagline: "Надёжный ремонт и обслуживание",
  services: [
    { icon: "🔧", label: "Диагностика" },
    { icon: "🛞", label: "Шины" },
    { icon: "⚙️", label: "ТО" },
    { icon: "🚗", label: "Кузов" },
  ],
  hours: "Пн–Пт 8:00–18:00",
  phone: "+49 89 555 0101",
  city: "Hamburg",
  heroFrom: "#1a2332",
  heroTo: "#3d4f5f",
  accent: "#7eb8da",
};

const PRO: IndustryProfile = {
  id: "pro",
  categoryLabel: "Ваш бизнес",
  tagline: "Профессиональные услуги для клиентов",
  services: [
    { icon: "⭐", label: "Услуга 1" },
    { icon: "📋", label: "Услуга 2" },
    { icon: "🤝", label: "Консультация" },
    { icon: "📞", label: "Связь" },
  ],
  hours: "Пн–Пт 9:00–18:00",
  phone: "+49 30 000 0000",
  city: "Deutschland",
  heroFrom: "#1e293b",
  heroTo: "#334155",
  accent: "#94a3b8",
};

const BY_GOAL: Record<GuidedGoalId, IndustryProfile> = {
  sell_online: BEAUTY,
  get_clients: BEAUTY,
  accept_payments: CAFE,
  automate: PRO,
  fix_problem: AUTO,
  improve_site: PRO,
};

export function getIndustryProfile(goalId: GuidedGoalId | null): IndustryProfile {
  if (!goalId) return PRO;
  return BY_GOAL[goalId] ?? PRO;
}

export function slugDomain(name: string): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9äöüß]+/gi, "")
    .slice(0, 24);
  return slug ? `${slug}.de` : "ваш-сайт.de";
}
