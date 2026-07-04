import type { AppSettings } from "./settings";
import { apiJson } from "./apiClient";
import type { SystemStatus } from "./api";

export type { SystemStatus };

export type OwnerEvent = {
  icon: string;
  message: string;
};

export type OwnerDashboard = {
  owner_name: string;
  greeting: string;
  system_running: boolean;
  all_services_ok: boolean;
  tasks_completed_today: number;
  errors_today: number;
  uptime_label: string;
  last_launch_label: string;
  daily_goal: string;
  queue_completed: number;
  queue_failed: number;
  queue_pending: number;
  products_count: number;
  products_created_today: number;
  revenue_today_eur: number;
  revenue_month_eur: number;
  system_load_percent: number;
  recent_events: OwnerEvent[];
  tip: string;
  services_summary: string[];
};

export type FactoryProduct = {
  product_id: string;
  product_type: string;
  business_name: string;
  description: string;
  status: string;
  status_label: string;
  quality_percent: number;
  owner_approved: boolean;
  published: boolean;
  public_url: string | null;
};

export type AssistantResponse = {
  answer: string;
  source: string;
};

export async function fetchSystemStatus(
  settings: AppSettings,
): Promise<SystemStatus> {
  return apiJson<SystemStatus>(settings, "/api/status");
}

export async function fetchOwnerDashboard(
  settings: AppSettings,
): Promise<OwnerDashboard> {
  return apiJson<OwnerDashboard>(settings, "/api/owner/dashboard");
}

export async function fetchProjects(
  settings: AppSettings,
): Promise<FactoryProduct[]> {
  const data = await apiJson<{ products: FactoryProduct[] }>(
    settings,
    "/api/factory/products",
  );
  return data.products;
}

export async function askAssistant(
  settings: AppSettings,
  question: string,
): Promise<AssistantResponse> {
  return apiJson<AssistantResponse>(settings, "/api/assistant/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
