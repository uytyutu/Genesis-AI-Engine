/**
 * PE-1 — instant project state + autonomous progress (independent of LLM).
 */

import { bootstrapProjectFromMessage, type ProjectPlatformState } from "./projectApi";
import { claimProjectFromMessage, isProjectClaimed, mergeClaimDraft } from "./projectIdentity";
import { getVisitorId } from "./visitorId";

export type ItemStatus = "pending" | "active" | "done";

export type ProjectStateItem = {
  id: string;
  label: string;
  status: ItemStatus;
  value?: string;
};

export type LiveProjectState = {
  active: boolean;
  title: string;
  serviceId: string;
  statusLabel: string;
  percent: number;
  items: ProjectStateItem[];
  vectorNow: string[];
  updatedAt: number;
};

const STORAGE_PREFIX = "vc_live_project_";

const CREATE_INTENT =
  /(создай|создать|сделай|сделать|нужен|нужна|хочу|под ключ|build|create|make)/i;

const INTENT_PATTERNS: Array<{ re: RegExp; serviceId: string; title: string }> = [
  { re: /(сайт|лендинг|landing|website|webseite)/i, serviceId: "website", title: "Создание сайта" },
  { re: /(бизнес[- ]?план|business\s*plan)/i, serviceId: "business_plan", title: "Бизнес-план" },
  { re: /(презентац|presentation|pitch)/i, serviceId: "presentation", title: "Презентация" },
  {
    re: /(анализ|разбор).{0,24}(документ|pdf|отчёт)/i,
    serviceId: "document_analysis",
    title: "Анализ документов",
  },
  { re: /(автоматизац|automation)/i, serviceId: "automation", title: "Автоматизация" },
  { re: /(чат[- ]?бот|chatbot|бот для)/i, serviceId: "chatbot", title: "Чат-бот" },
  { re: /(приложени|application|app\b)/i, serviceId: "application", title: "Приложение" },
  { re: /(crm|система клиент)/i, serviceId: "crm", title: "CRM" },
  { re: /(бренд|логотип|logo)/i, serviceId: "logo_design", title: "Брендинг" },
];

const JOURNEY_BY_SERVICE: Record<string, Array<{ id: string; label: string }>> = {
  website: [
    { id: "type", label: "Тип проекта" },
    { id: "goal", label: "Цель" },
    { id: "company", label: "Компания" },
    { id: "country", label: "Страна" },
    { id: "structure", label: "Структура" },
    { id: "design", label: "Дизайн" },
    { id: "colors", label: "Цвета" },
    { id: "logo", label: "Логотип" },
    { id: "content", label: "Контент" },
    { id: "draft", label: "Черновик" },
    { id: "revisions", label: "Правки" },
    { id: "launch", label: "Готов к запуску" },
  ],
  default: [
    { id: "type", label: "Тип проекта" },
    { id: "goal", label: "Цель" },
    { id: "brief", label: "Задача" },
    { id: "materials", label: "Материалы" },
    { id: "draft", label: "Черновик" },
    { id: "revisions", label: "Правки" },
    { id: "launch", label: "Готов к запуску" },
  ],
};

type AutoStage = {
  delayMs: number;
  statusLabel: string;
  vectorNow: string[];
  doneIds?: string[];
  activeId?: string;
  percent?: number;
};

const WEBSITE_AUTO_STAGES: AutoStage[] = [
  {
    delayMs: 0,
    statusLabel: "🟡 Анализ задачи",
    vectorNow: ["✓ создаёт проект", "⏳ определяет тип", "○ готовит структуру"],
    doneIds: ["type"],
    activeId: "goal",
    percent: 8,
  },
  {
    delayMs: 700,
    statusLabel: "🟡 Сборка структуры",
    vectorNow: ["✓ проект создан", "✓ тип определён", "⏳ готовит структуру"],
    doneIds: ["type", "goal"],
    activeId: "structure",
    percent: 18,
  },
  {
    delayMs: 1800,
    statusLabel: "🟡 Сборка структуры",
    vectorNow: ["✓ проект создан", "✓ тип определён", "✓ готовит структуру", "⏳ жду данные о компании"],
    doneIds: ["type", "goal", "structure"],
    activeId: "company",
    percent: 28,
  },
  {
    delayMs: 3500,
    statusLabel: "🟡 Ожидание информации о компании",
    vectorNow: [
      "✓ проект создан",
      "✓ структура готовится",
      "⏳ ожидаю описание компании",
    ],
    activeId: "company",
    percent: 32,
  },
  {
    delayMs: 6000,
    statusLabel: "🟡 Совместная работа",
    vectorNow: ["✓ проект создан", "✓ структура", "⏳ уточняем детали"],
    percent: 36,
  },
];

const DEFAULT_AUTO_STAGES: AutoStage[] = [
  {
    delayMs: 0,
    statusLabel: "🟡 Анализ задачи",
    vectorNow: ["✓ создаёт проект", "⏳ определяет задачу"],
    doneIds: ["type"],
    activeId: "goal",
    percent: 10,
  },
  {
    delayMs: 1500,
    statusLabel: "🟡 Подготовка",
    vectorNow: ["✓ проект создан", "⏳ собираю материалы"],
    doneIds: ["type", "goal"],
    activeId: "brief",
    percent: 22,
  },
  {
    delayMs: 4000,
    statusLabel: "🟡 Совместная работа",
    vectorNow: ["✓ проект создан", "⏳ уточняем детали"],
    percent: 28,
  },
];

const COUNTRY_PATTERNS: Array<{ re: RegExp; value: string }> = [
  { re: /германи|deutschland|germany|berlin|мюнхен|hamburg/i, value: "🇩🇪 Германия" },
  { re: /росси|russia|москв|петербург/i, value: "🇷🇺 Россия" },
  { re: /украин|ukraine|киев|kyiv/i, value: "🇺🇦 Украина" },
  { re: /польш|poland|warsaw/i, value: "🇵🇱 Польша" },
  { re: /австри|austria|vienna|вен/i, value: "🇦🇹 Австрия" },
  { re: /швейцар|switzerland|zürich|zurich/i, value: "🇨🇭 Швейцария" },
];

const DESIGN_PATTERNS: Array<{ re: RegExp; value: string }> = [
  { re: /тёмн|темн|dark|modern dark/i, value: "Modern Dark" },
  { re: /светл|light|минимал/i, value: "Light Minimal" },
  { re: /корпоратив|business|делов/i, value: "Business" },
];

export const PROJECT_STATE_EVENT = "genesis:project-state";

const autoTimers = new Map<string, number[]>();

function storageKey(visitorId: string): string {
  return `${STORAGE_PREFIX}${visitorId}`;
}

function loadState(visitorId: string): LiveProjectState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(storageKey(visitorId));
    if (!raw) return null;
    return JSON.parse(raw) as LiveProjectState;
  } catch {
    return null;
  }
}

function saveState(visitorId: string, state: LiveProjectState): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(storageKey(visitorId), JSON.stringify(state));
}

export function dispatchProjectState(state: LiveProjectState | null): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(PROJECT_STATE_EVENT, { detail: state }));
}

export function detectDeliverableIntent(text: string): {
  serviceId: string;
  title: string;
} | null {
  const t = (text || "").trim();
  if (t.length < 4) return null;
  const hasCreate = CREATE_INTENT.test(t);
  for (const row of INTENT_PATTERNS) {
    if (row.re.test(t) && (hasCreate || t.length > 24)) {
      return { serviceId: row.serviceId, title: row.title };
    }
  }
  if (hasCreate && /проект/i.test(t)) {
    return { serviceId: "website", title: "Новый проект" };
  }
  return null;
}

function inferTitle(message: string, fallback: string): string {
  const m = message.match(/сайт\s+для\s+(.{3,48})/i);
  if (m?.[1]) return `Сайт: ${m[1].trim()}`;
  const m2 = message.match(/для\s+(?:моей\s+)?компани/i);
  if (m2 && /сайт/i.test(message)) return "Новый сайт компании";
  if (message.length > 8 && message.length < 72) return message.trim();
  return fallback;
}

function journeyFor(serviceId: string): Array<{ id: string; label: string }> {
  return JOURNEY_BY_SERVICE[serviceId] ?? JOURNEY_BY_SERVICE.default;
}

function percentFromItems(items: ProjectStateItem[]): number {
  if (!items.length) return 0;
  const done = items.filter((i) => i.status === "done").length;
  const active = items.filter((i) => i.status === "active").length;
  return Math.min(99, Math.round(((done + active * 0.4) / items.length) * 100));
}

function setItem(
  items: ProjectStateItem[],
  id: string,
  patch: Partial<Pick<ProjectStateItem, "status" | "value">>,
): ProjectStateItem[] {
  let changed = false;
  const next = items.map((item) => {
    if (item.id !== id) return item;
    changed = true;
    return { ...item, ...patch };
  });
  return changed ? next : items;
}

function applyAutoStage(items: ProjectStateItem[], stage: AutoStage): ProjectStateItem[] {
  let next = items;
  for (const id of stage.doneIds ?? []) {
    next = setItem(next, id, { status: "done" });
  }
  if (stage.activeId) {
    next = setItem(next, stage.activeId, { status: "active" });
  }
  return next;
}

function extractFacts(message: string, items: ProjectStateItem[]): ProjectStateItem[] {
  let next = items;
  for (const row of COUNTRY_PATTERNS) {
    if (row.re.test(message)) {
      next = setItem(next, "country", { status: "done", value: row.value });
      break;
    }
  }
  for (const row of DESIGN_PATTERNS) {
    if (row.re.test(message)) {
      next = setItem(next, "design", { status: "done", value: row.value });
      break;
    }
  }
  const companyMatch =
    message.match(/(?:компани[яи]|фирм[аы])\s+([A-ZА-ЯЁ][\w\-]+(?:\s+[A-ZА-ЯЁ][\w\-äöüÄÖÜß]+)?)/i) ||
    message.match(/название\s*[-—:]\s*([^.!\n]{2,48})/i) ||
    message.match(/\b([A-Z][a-z]+Team(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)\b/) ||
    message.match(/\b([A-Z][a-z]+(?:Line|Tech|GmbH|Solar))\b/);
  if (companyMatch?.[1]) {
    const name = companyMatch[1].trim();
    if (!/^(virtus|vector|core)$/i.test(name)) {
      next = setItem(next, "company", { status: "done", value: name });
    }
  }
  if (/(?:заявк|консультац|позвон|запис|купить|заказ)/i.test(message)) {
    next = setItem(next, "goal", { status: "done", value: "Действие на сайте" });
  }
  if (/(?:цвет|палитр|зелён|зелен|син|красн|бел)/i.test(message)) {
    const colorLine = message.match(/цвет[аы]?\s*[:—-]\s*([^.!\n]{3,40})/i);
    next = setItem(next, "colors", {
      status: "done",
      value: colorLine?.[1]?.trim() || "Заданы",
    });
  }
  if (/(?:логотип|logo|без\s+логотип|нет\s+логотип)/i.test(message)) {
    next = setItem(next, "logo", {
      status: "done",
      value: /без\s+логотип|нет\s+логотип/i.test(message) ? "Без логотипа" : "Учтён",
    });
  }
  if (/(?:материал|фото|используй|описан|то\s+что)/i.test(message)) {
    next = setItem(next, "content", { status: "done", value: "Собраны" });
  }
  return next;
}

function bootstrapItems(serviceId: string): ProjectStateItem[] {
  return journeyFor(serviceId).map((row) => ({
    id: row.id,
    label: row.label,
    status: "pending" as ItemStatus,
  }));
}

function createBootstrapState(message: string, intent: { serviceId: string; title: string }): LiveProjectState {
  const items = bootstrapItems(intent.serviceId);
  return {
    active: true,
    title: inferTitle(message, intent.title),
    serviceId: intent.serviceId,
    statusLabel: "🟡 Анализ задачи",
    percent: 4,
    items,
    vectorNow: ["⏳ создаёт проект"],
    updatedAt: Date.now(),
  };
}

function touchExistingState(state: LiveProjectState, message: string): LiveProjectState {
  const items = extractFacts(message, state.items);
  const percent = Math.max(state.percent, percentFromItems(items));
  return {
    ...state,
    items,
    percent,
    statusLabel: percent >= 40 ? "🟡 Уточнение задачи" : state.statusLabel,
    updatedAt: Date.now(),
  };
}

function stagesFor(serviceId: string): AutoStage[] {
  return serviceId === "website" ? WEBSITE_AUTO_STAGES : DEFAULT_AUTO_STAGES;
}

function applyStage(visitorId: string, stage: AutoStage): void {
  const state = loadState(visitorId);
  if (!state?.active) return;
  const items = applyAutoStage(state.items, stage);
  const percent = Math.max(state.percent, stage.percent ?? percentFromItems(items));
  const next: LiveProjectState = {
    ...state,
    items,
    percent,
    statusLabel: stage.statusLabel,
    vectorNow: stage.vectorNow,
    updatedAt: Date.now(),
  };
  saveState(visitorId, next);
  dispatchProjectState(next);
}

/** Autonomous progress disabled — panel syncs from backend journey (source of truth). */
export function startAutonomousProgress(_visitorId: string, _serviceId: string): void {
  stopAutonomousProgress(_visitorId);
}

export function stopAutonomousProgress(visitorId: string): void {
  const timers = autoTimers.get(visitorId);
  if (!timers) return;
  for (const id of timers) window.clearTimeout(id);
  autoTimers.delete(visitorId);
}

export function applyBackendJourneyState(
  platform: ProjectPlatformState,
  visitorId?: string,
): LiveProjectState | null {
  if (!isProjectClaimed()) return null;
  const vid = visitorId ?? getVisitorId("public");
  const project = platform.project;
  if (!project?.journey?.items?.length) return null;

  const journey = project.journey;
  const existing = loadState(vid);
  const title =
    project.identity?.title?.trim() ||
    project.title?.trim() ||
    existing?.title ||
    "Проект";
  const companyItem = journey.items.find((row) => row.id === "company");
  const displayTitle =
    companyItem?.status === "done" && companyItem.value
      ? `Сайт: ${companyItem.value}`
      : title;

  const state: LiveProjectState = {
    active: platform.has_project || project.mode === "project",
    title: displayTitle,
    serviceId: project.identity?.type_id || existing?.serviceId || "website",
    statusLabel: journey.status_label || existing?.statusLabel || "🟡 В работе",
    percent: journey.percent ?? existing?.percent ?? 0,
    items: journey.items.map((row) => ({
      id: row.id,
      label: row.label,
      status: row.status,
      value: row.value,
    })),
    vectorNow: journey.vector_now?.length
      ? journey.vector_now
      : existing?.vectorNow ?? ["✓ проект в работе"],
    updatedAt: Date.now(),
  };

  if (!state.active) return null;
  saveState(vid, state);
  dispatchProjectState(state);
  return state;
}

export function onVectorReplied(visitorId: string): void {
  stopAutonomousProgress(visitorId);
}

/** Called on send — bootstrap backend only; panel never invents journey items. */
export function onUserMessageForProject(message: string, visitorId?: string): void {
  const vid = visitorId ?? getVisitorId("public");
  const text = (message || "").trim();
  if (!text) return;

  if (!isProjectClaimed()) {
    claimProjectFromMessage(text);
  } else {
    mergeClaimDraft(text);
  }

  void bootstrapProjectFromMessage(text, vid).then((platform) => {
    applyProjectStateAuthority(platform, vid);
  });
}

export function setProjectWaiting(visitorId: string, vectorNow: string[]): void {
  const state = loadState(visitorId);
  if (!state?.active) return;
  const next: LiveProjectState = {
    ...state,
    statusLabel: "🟡 Продолжаем работу",
    vectorNow,
    updatedAt: Date.now(),
  };
  saveState(visitorId, next);
  dispatchProjectState(next);
}

export function getLiveProjectState(visitorId?: string): LiveProjectState | null {
  if (!isProjectClaimed()) return null;
  return loadState(visitorId ?? getVisitorId("public"));
}

export function applyProjectStateAuthority(
  platform: ProjectPlatformState | null | undefined,
  visitorId?: string,
): LiveProjectState | null {
  if (!platform) return null;
  return applyBackendJourneyState(platform, visitorId);
}
