import type { AppSettings } from "./settings";
import { apiBase } from "./apiClient";
import type { WelcomeState } from "./customerSession";

export type AuthResponse = {
  token: string;
  name: string;
  email: string;
  headline?: string;
  platform_visitor_id?: string | null;
  welcome?: WelcomeState | null;
  company?: { name?: string; project?: unknown };
};

function mapClientError(detail: string): string {
  const map: Record<string, string> = {
    invalid_email: "Проверьте адрес email.",
    email_already_registered: "Этот email уже зарегистрирован. Войдите.",
    invalid_credentials: "Неверный email или пароль.",
    password_too_short: "Пароль — минимум 8 символов.",
    name_required: "Укажите, как к вам обращаться.",
    client_auth_required: "Войдите снова.",
  };
  return map[detail] || "Что-то пошло не так. Попробуйте ещё раз.";
}

async function clientFetch<T>(
  settings: AppSettings,
  path: string,
  init?: RequestInit,
  token?: string,
): Promise<T> {
  const headers: HeadersInit = {
    Accept: "application/json",
    ...(init?.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...init?.headers,
  };
  const res = await fetch(`${apiBase(settings)}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = (await res.json()) as { detail?: string };
      if (err.detail) detail = err.detail;
    } catch {
      /* ignore */
    }
    throw new Error(
      detail.startsWith("HTTP")
        ? "Нет связи с сервером. Проверьте интернет."
        : mapClientError(detail),
    );
  }
  return (await res.json()) as T;
}

export async function registerCustomer(
  settings: AppSettings,
  body: {
    name: string;
    email: string;
    password: string;
    visitor_id?: string;
  },
): Promise<AuthResponse> {
  return clientFetch<AuthResponse>(settings, "/api/client/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function loginCustomer(
  settings: AppSettings,
  body: { email: string; password: string },
): Promise<AuthResponse> {
  return clientFetch<AuthResponse>(settings, "/api/client/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchCustomerMe(
  settings: AppSettings,
  token: string,
): Promise<Record<string, unknown>> {
  return clientFetch(settings, "/api/client/me", { method: "GET" }, token);
}

export async function fetchWelcome(
  settings: AppSettings,
  token: string,
): Promise<WelcomeState> {
  return clientFetch<WelcomeState>(settings, "/api/client/welcome", { method: "GET" }, token);
}

export async function advanceWelcome(
  settings: AppSettings,
  token: string,
): Promise<WelcomeState> {
  return clientFetch<WelcomeState>(
    settings,
    "/api/client/welcome/advance",
    { method: "POST", body: "{}" },
    token,
  );
}

export async function answerWelcome(
  settings: AppSettings,
  token: string,
  body: { answer: string; skip?: boolean },
): Promise<WelcomeState> {
  return clientFetch<WelcomeState>(
    settings,
    "/api/client/welcome/answer",
    { method: "POST", body: JSON.stringify(body) },
    token,
  );
}

export async function askVectorPublic(
  settings: AppSettings,
  body: {
    question: string;
    visitor_id: string;
    locale?: string;
  },
): Promise<{ answer: string }> {
  const data = await clientFetch<{ answer?: string }>(
    settings,
    "/api/public/genesis-ai",
    {
      method: "POST",
      body: JSON.stringify({
        question: body.question,
        visitor_id: body.visitor_id,
        locale: body.locale ?? "ru",
      }),
    },
  );
  return { answer: data.answer || "" };
}
