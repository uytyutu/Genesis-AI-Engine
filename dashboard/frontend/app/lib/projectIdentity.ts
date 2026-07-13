/**
 * Product Identity — project is "claimed" when the human feels ownership.
 * Until then: empty company card, no backend journey on screen.
 */

export type ProjectClaimDraft = {
  companyName: string | null;
  industry: string | null;
  location: string | null;
  goal: string | null;
  statusLabel: string;
  claimedAt: number | null;
};

const CLAIM_KEY = "vc_project_claimed";
const DRAFT_KEY = "vc_project_claim_draft";

export const PROJECT_CLAIM_EVENT = "genesis:project-claimed";

const EMPTY_DRAFT: ProjectClaimDraft = {
  companyName: null,
  industry: null,
  location: null,
  goal: null,
  statusLabel: "Ждём рассказ о вашей компании.",
  claimedAt: null,
};

function readDraft(): ProjectClaimDraft {
  if (typeof window === "undefined") return { ...EMPTY_DRAFT };
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (!raw) return { ...EMPTY_DRAFT };
    return { ...EMPTY_DRAFT, ...(JSON.parse(raw) as Partial<ProjectClaimDraft>) };
  } catch {
    return { ...EMPTY_DRAFT };
  }
}

function writeDraft(draft: ProjectClaimDraft): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
}

export function isProjectClaimed(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return sessionStorage.getItem(CLAIM_KEY) === "1";
  } catch {
    return false;
  }
}

export function resetProjectClaim(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(CLAIM_KEY);
    sessionStorage.removeItem(DRAFT_KEY);
  } catch {
    /* private mode */
  }
  window.dispatchEvent(new CustomEvent(PROJECT_CLAIM_EVENT, { detail: null }));
}

export function getProjectClaimDraft(): ProjectClaimDraft {
  return readDraft();
}

function dispatchClaim(draft: ProjectClaimDraft): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(PROJECT_CLAIM_EVENT, { detail: draft }));
}

const INDUSTRY_PATTERNS: Array<{ re: RegExp; value: string }> = [
  { re: /(строитель|ремонт|бригад|bau|handwerk)/i, value: "Строительная компания" },
  { re: /(салон|красот|парикмахер)/i, value: "Салон красоты" },
  { re: /(кафе|ресторан|бар\b)/i, value: "Кафе / ресторан" },
  { re: /(стоматолог|клиник|медицин)/i, value: "Медицина" },
  { re: /(магазин|торгов|shop)/i, value: "Торговля" },
];

const LOCATION_PATTERNS: Array<{ re: RegExp; value: string }> = [
  { re: /(кёльн|колн|köln|cologne)/i, value: "Кёльн" },
  { re: /(берлин|berlin)/i, value: "Берлин" },
  { re: /(мюнхен|munich)/i, value: "Мюнхен" },
  { re: /(германи|deutschland|germany)/i, value: "Германия" },
  { re: /(росси|москв)/i, value: "Россия" },
];

function extractCompanyName(text: string): string | null {
  const t = text.trim();
  const named =
    t.match(/название\s*[-—:]\s*([^.!\n]{2,48})/i) ||
    t.match(/(?:компани[яи]\s+)([A-ZА-ЯЁ][\w\s\-äöüÄÖÜß]{2,40})/i) ||
    t.match(/\b([A-Z][a-z]+(?:Team|Line|GmbH|Pro)?\s+[A-ZÄÖÜ][a-zäöüß]+)\b/);
  if (named?.[1]) {
    const name = named[1].trim().replace(/\s+/g, " ");
    if (!/^(virtus|vector|core)$/i.test(name)) return name;
  }
  const bau = t.match(/\b(Bau[A-Z][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)\b/);
  if (bau?.[1]) return bau[1].trim();
  return null;
}

function extractIndustry(text: string): string | null {
  for (const row of INDUSTRY_PATTERNS) {
    if (row.re.test(text)) return row.value;
  }
  return null;
}

function extractLocation(text: string): string | null {
  for (const row of LOCATION_PATTERNS) {
    if (row.re.test(text)) return row.value;
  }
  return null;
}

function extractGoal(text: string): string | null {
  if (/(сайт|лендинг|website)/i.test(text)) {
    if (/(заявк|заказ|позвон|телефон)/i.test(text)) return "Заявки с сайта";
    if (/(находил|клиент|заказ)/i.test(text)) return "Больше клиентов";
    return "Сайт для компании";
  }
  if (/(excel|таблиц)/i.test(text) && /(клиент|заказ)/i.test(text)) {
    return "Уйти от Excel, больше заказов";
  }
  if (/(клиент|заказ)/i.test(text)) return "Больше клиентов";
  return null;
}

export function extractClaimFactsFromMessage(message: string): Partial<ProjectClaimDraft> {
  const text = (message || "").trim();
  if (!text) return {};
  return {
    companyName: extractCompanyName(text),
    industry: extractIndustry(text),
    location: extractLocation(text),
    goal: extractGoal(text),
  };
}

export function claimProjectFromMessage(message: string): ProjectClaimDraft {
  const text = (message || "").trim();
  const prev = readDraft();
  const facts = extractClaimFactsFromMessage(message);
  const companyName = facts.companyName ?? prev.companyName;
  const industry = facts.industry ?? prev.industry;
  const location = facts.location ?? prev.location;
  const goal = facts.goal ?? prev.goal;

  let statusLabel = "Ждём рассказ о вашей компании.";
  if (companyName) {
    statusLabel = "✓ Компания определена";
  } else if (goal || industry) {
    statusLabel = "Уточняем вашу компанию";
  } else if (/(привет|здравств|hello|hi\b|как дела|guten tag|hallo)/i.test(message)) {
    statusLabel = "✓ Vector на связи";
  } else if (text.length > 2) {
    statusLabel = "✓ Сообщение получено";
  }

  const draft: ProjectClaimDraft = {
    companyName,
    industry,
    location,
    goal,
    statusLabel,
    claimedAt: Date.now(),
  };

  if (typeof window !== "undefined") {
    try {
      sessionStorage.setItem(CLAIM_KEY, "1");
    } catch {
      /* private mode */
    }
  }
  writeDraft(draft);
  dispatchClaim(draft);
  return draft;
}

export function mergeClaimDraft(message: string): ProjectClaimDraft {
  if (!isProjectClaimed()) {
    return claimProjectFromMessage(message);
  }
  const prev = readDraft();
  const facts = extractClaimFactsFromMessage(message);
  const draft: ProjectClaimDraft = {
    companyName: facts.companyName ?? prev.companyName,
    industry: facts.industry ?? prev.industry,
    location: facts.location ?? prev.location,
    goal: facts.goal ?? prev.goal,
    statusLabel: (facts.companyName ?? prev.companyName)
      ? "✓ Компания определена"
      : /(привет|здравств|hello|hi\b|как дела|guten tag|hallo)/i.test(message)
        ? "✓ Vector на связи"
        : message.trim().length > 2
          ? "✓ Сообщение получено"
          : prev.statusLabel,
    claimedAt: prev.claimedAt ?? Date.now(),
  };
  writeDraft(draft);
  dispatchClaim(draft);
  return draft;
}
