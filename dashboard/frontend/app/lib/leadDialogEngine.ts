/**
 * Lead capture dialog engine — unstructured visitor chat → hot lead (Model 3).
 * Same pattern as guidedDialogEngine, different output artifact.
 */

import { publicApiBase } from "./publicApiBase";
import { getVisitorId } from "./visitorId";

const API = publicApiBase();
const STORAGE_KEY = "vc_lead_capture_v1";
export const LEAD_CAPTURE_EVENT = "genesis:lead-capture";

export type LeadNiche = "autoservice" | "laptop_repair" | "plumber" | "generic";

export type LeadCaptureState = {
  niche: LeadNiche;
  customerName: string;
  problem: string;
  urgency: string;
  location: string;
  phone: string;
  email: string;
  score: number;
  hot: boolean;
  leadId: string | null;
  lastFollowUp: string | null;
};

const NICHE_LABEL: Record<LeadNiche, string> = {
  autoservice: "Автосервис",
  laptop_repair: "Ремонт ноутбуков",
  plumber: "Сантехник",
  generic: "Услуга",
};

const FOLLOW_UP: Record<string, string> = {
  problem: "Расскажите, что случилось — я оформлю заявку под вашу ситуацию.",
  location: "В каком городе или районе вам нужна помощь?",
  contact: "Оставьте телефон или email — передам мастеру, когда заявка будет готова.",
  urgency: "Насколько срочно — сегодня, завтра или можно подождать?",
};

const EMAIL_RE = /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i;
const PHONE_RE = /(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}(?:[\s-]?\d{2,4})?/;

function clean(text: string, max = 160): string {
  const t = text.replace(/\s+/g, " ").trim();
  return t.length <= max ? t : `${t.slice(0, max - 1)}…`;
}

function extractProblem(text: string): string | null {
  const m =
    text.match(/(?:проблема|сломал\w*|не\s+работ\w*|нужен?\s+[^.!\n]{4,80})/i) ||
    text.match(/(?:ремонт|почин\w*|замен\w*|диагност\w*)[^.!\n]{0,60}/i);
  if (m) return clean(m[0], 120);
  if (text.length > 24 && /(срочно|помог|нужно|хочу)/i.test(text)) return clean(text, 120);
  return null;
}

function extractUrgency(text: string): string | null {
  if (/(срочно|сегодня|завтра|asap|urgent)/i.test(text)) {
    const m = text.match(/(срочно[^.!\n]{0,40}|сегодня[^.!\n]{0,40}|завтра[^.!\n]{0,40})/i);
    return m ? clean(m[0], 60) : "Срочно";
  }
  return null;
}

function extractLocation(text: string): string | null {
  const m =
    text.match(/(?:я\s+в|нахожусь\s+в|город[:\s]+|в\s+г\.?\s*)([A-Za-zА-Яа-яЁё\s-]{2,40})/i) ||
    text.match(/\b(?:в|in)\s+([A-ZА-ЯЁ][a-zа-яё-]{2,24})\b/i);
  if (!m) return null;
  const loc = m[1].trim();
  if (/^(нужен|хочу|срочно|привет)$/i.test(loc)) return null;
  return clean(loc, 60);
}

function extractName(text: string): string | null {
  const m = text.match(/(?:меня\s+зовут|я\s+[-—]\s*|my\s+name\s+is)\s*([A-Za-zА-Яа-яЁё\s-]{2,40})/i);
  return m ? clean(m[1], 40) : null;
}

export function normalizeLeadNiche(raw: string | null | undefined): LeadNiche {
  const key = (raw || "generic").trim().toLowerCase();
  if (key === "autoservice" || key === "auto" || key === "autowerkstatt") return "autoservice";
  if (key === "laptop" || key === "laptop_repair" || key === "pc") return "laptop_repair";
  if (key === "plumber" || key === "santeh" || key === "sanitary") return "plumber";
  return "generic";
}

export function leadNicheLabel(niche: LeadNiche): string {
  return NICHE_LABEL[niche] ?? NICHE_LABEL.generic;
}

export function extractLeadFacts(message: string) {
  const text = (message || "").trim();
  if (!text) return {};
  const email = text.match(EMAIL_RE)?.[0] ?? null;
  const phone = text.match(PHONE_RE)?.[0] ?? null;
  return {
    customerName: extractName(text),
    problem: extractProblem(text),
    urgency: extractUrgency(text),
    location: extractLocation(text),
    phone,
    email,
  };
}

const EMPTY: LeadCaptureState = {
  niche: "generic",
  customerName: "",
  problem: "",
  urgency: "",
  location: "",
  phone: "",
  email: "",
  score: 0,
  hot: false,
  leadId: null,
  lastFollowUp: null,
};

function mergeField(prev: string, next: string | null | undefined): string {
  const n = (next ?? "").trim();
  if (!n) return prev;
  if (!prev.trim()) return n;
  if (prev.includes(n)) return prev;
  return `${prev.trim()}. ${n}`;
}

export function loadLeadCapture(niche: LeadNiche = "generic"): LeadCaptureState {
  if (typeof window === "undefined") return { ...EMPTY, niche };
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...EMPTY, niche };
    const parsed = JSON.parse(raw) as Partial<LeadCaptureState>;
    return { ...EMPTY, ...parsed, niche: parsed.niche ?? niche };
  } catch {
    return { ...EMPTY, niche };
  }
}

export function saveLeadCapture(state: LeadCaptureState): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  window.dispatchEvent(new CustomEvent(LEAD_CAPTURE_EVENT, { detail: state }));
}

export function leadGaps(state: LeadCaptureState): string[] {
  const gaps: string[] = [];
  if (!state.problem.trim()) gaps.push("problem");
  if (!state.location.trim()) gaps.push("location");
  if (!state.phone.trim() && !state.email.trim()) gaps.push("contact");
  if (state.problem.trim() && !state.urgency.trim()) gaps.push("urgency");
  return gaps;
}

export function scoreLead(state: LeadCaptureState): number {
  let score = 0;
  if (state.problem.trim()) score += 30;
  if (state.location.trim()) score += 20;
  if (state.phone.trim()) score += 25;
  else if (state.email.trim()) score += 20;
  if (state.urgency.trim()) score += 15;
  if (state.customerName.trim()) score += 10;
  return Math.min(100, score);
}

export function isHotLead(state: LeadCaptureState): boolean {
  return Boolean(
    state.problem.trim() &&
      state.location.trim() &&
      (state.phone.trim() || state.email.trim()),
  );
}

export function pickLeadFollowUp(state: LeadCaptureState): string | null {
  const gaps = leadGaps(state);
  if (!gaps.length) return null;
  return FOLLOW_UP[gaps[0]] ?? null;
}

export function applyLeadFacts(
  facts: ReturnType<typeof extractLeadFacts>,
  niche: LeadNiche,
): LeadCaptureState {
  const prev = loadLeadCapture(niche);
  const next: LeadCaptureState = {
    ...prev,
    niche,
    customerName: facts.customerName?.trim() || prev.customerName,
    problem: mergeField(prev.problem, facts.problem),
    urgency: facts.urgency?.trim() || prev.urgency,
    location: facts.location?.trim() || prev.location,
    phone: facts.phone?.trim() || prev.phone,
    email: facts.email?.trim() || prev.email,
  };
  next.score = scoreLead(next);
  next.hot = isHotLead(next);
  saveLeadCapture(next);
  return next;
}

export function ingestLeadDialogMessage(message: string, niche: LeadNiche): LeadCaptureState {
  return applyLeadFacts(extractLeadFacts(message), niche);
}

export function assistantAlreadyClarifies(answer: string): boolean {
  return /[?？]/.test(answer) || /(уточн|расскаж|телефон|email|город|срочно|проблем)/i.test(answer);
}

export function enrichAnswerWithLeadFollowUp(answer: string, state: LeadCaptureState): string {
  const followUp = pickLeadFollowUp(state);
  if (!followUp || assistantAlreadyClarifies(answer)) return answer;
  const trimmed = answer.trim();
  if (!trimmed) return followUp;
  return `${trimmed}\n\n${followUp}`;
}

export function buildLeadCaptureContext(state: LeadCaptureState) {
  return {
    mode: "lead_capture",
    niche: state.niche,
    niche_label: leadNicheLabel(state.niche),
    known: {
      customer_name: state.customerName || null,
      problem: state.problem || null,
      urgency: state.urgency || null,
      location: state.location || null,
      phone: state.phone || null,
      email: state.email || null,
    },
    missing: leadGaps(state),
    follow_up: pickLeadFollowUp(state),
    score: state.score,
    hot: state.hot,
  };
}

export function leadKnownSummary(state: LeadCaptureState): string[] {
  const lines: string[] = [];
  if (state.customerName.trim()) lines.push(`Имя: ${state.customerName.trim()}`);
  if (state.problem.trim()) lines.push(`Проблема: ${state.problem.trim()}`);
  if (state.location.trim()) lines.push(`Локация: ${state.location.trim()}`);
  if (state.urgency.trim()) lines.push(`Срочность: ${state.urgency.trim()}`);
  if (state.phone.trim()) lines.push(`Телефон: ${state.phone.trim()}`);
  if (state.email.trim()) lines.push(`Email: ${state.email.trim()}`);
  return lines;
}

export async function submitLeadIntake(
  state: LeadCaptureState,
  transcript: string,
): Promise<LeadCaptureState> {
  const res = await fetch(`${API}/api/public/leads/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      niche: state.niche,
      known: {
        customer_name: state.customerName,
        problem: state.problem,
        urgency: state.urgency,
        location: state.location,
        phone: state.phone,
        email: state.email,
      },
      visitor_id: getVisitorId("public"),
      transcript,
    }),
  });
  const body = await res.json();
  if (!res.ok) return state;
  const next = {
    ...state,
    hot: Boolean(body.hot),
    score: Number(body.score ?? state.score),
    leadId: (body.lead_id as string | null) ?? state.leadId,
  };
  saveLeadCapture(next);
  return next;
}
