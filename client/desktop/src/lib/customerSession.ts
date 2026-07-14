const SESSION_KEY = "genesis.client.customer.v1";

export type WelcomePhase =
  | "greeting"
  | "wizard"
  | "personalized"
  | "complete";

export type QuickAction = {
  id: string;
  label: string;
  service_id?: string;
};

export type WelcomeState = {
  phase: WelcomePhase;
  headline?: string | null;
  message?: string | null;
  wizard_question?: string | null;
  wizard_step?: number | null;
  wizard_total?: number | null;
  can_skip?: boolean;
  quick_actions?: QuickAction[];
  complete?: boolean;
};

export type CustomerSession = {
  token: string;
  name: string;
  email: string;
  platformVisitorId: string;
  welcomeComplete: boolean;
  welcomePhase: WelcomePhase;
  headline: string;
  quickActions?: QuickAction[];
};

export function loadCustomerSession(): CustomerSession | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as CustomerSession;
    if (!data?.token || !data?.name) return null;
    return data;
  } catch {
    return null;
  }
}

export function saveCustomerSession(session: CustomerSession): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearCustomerSession(): void {
  localStorage.removeItem(SESSION_KEY);
}

export function sessionFromAuthResponse(data: {
  token: string;
  name: string;
  email: string;
  headline?: string;
  platform_visitor_id?: string | null;
  welcome?: WelcomeState | null;
}): CustomerSession {
  const welcome = data.welcome;
  const phase = welcome?.phase ?? "greeting";
  const platformVisitorId = data.platform_visitor_id || "";
  return {
    token: data.token,
    name: data.name,
    email: data.email,
    platformVisitorId,
    welcomeComplete: phase === "complete",
    welcomePhase: phase,
    headline: data.headline || "Ваша цифровая компания готова.",
  };
}

export function applyWelcomeToSession(
  session: CustomerSession,
  welcome: WelcomeState,
): CustomerSession {
  const next: CustomerSession = {
    ...session,
    welcomePhase: welcome.phase,
    welcomeComplete: welcome.complete === true || welcome.phase === "complete",
    quickActions: welcome.quick_actions ?? session.quickActions,
  };
  saveCustomerSession(next);
  return next;
}
