/**
 * Русские подписи Treasury (UI only).
 */
import type { DustClass } from "./secureWeb3Engine";

export const DUST_CLASS_RU: Record<DustClass, string> = {
  profitable: "Выгодный",
  marginal: "Пограничный",
  dust: "Пыль",
  anomaly: "Аномалия",
};

export const DUST_TIP_RU: Record<DustClass, string> = {
  profitable:
    "Баланс больше текущей комиссии сети. После перевода на Vault останется положительный остаток.",
  marginal:
    "Вывод возможен, но запас тонкий (до ~2× газа). Лучше дождаться окна с низким газом.",
  dust:
    "Баланс ≤ стоимости газа. Одиночный вывод уйдёт в минус — не трогайте, пока газ не упадёт.",
  anomaly:
    "Крошечный остаток далеко ниже газа. Экономически бессмысленно перемещать отдельно.",
};

export function dustClassLabel(c: DustClass | string): string {
  return DUST_CLASS_RU[c as DustClass] ?? String(c);
}

export function gasWindowRu(window: string): string {
  switch (window) {
    case "low":
      return "НИЗКИЙ";
    case "normal":
      return "НОРМА";
    case "elevated":
      return "ПОВЫШЕННЫЙ";
    case "high":
      return "ВЫСОКИЙ";
    default:
      return window.toUpperCase();
  }
}

export function rankReasonRu(reason: string): string {
  const map: Record<string, string> = {
    "signable · profitable after gas": "подключён · выгодно после газа",
    "signable · below gas threshold": "подключён · ниже порога газа",
    "anomaly residual": "аномальный остаток",
    "read-only dust": "только чтение · пыль",
    "read-only · high balance": "только чтение · крупный баланс",
    balanced: "сбалансировано",
  };
  return map[reason] ?? reason;
}
