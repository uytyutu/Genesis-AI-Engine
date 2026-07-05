import type { AppSettings } from "./settings";
import { apiJson } from "./apiClient";
import type { SystemStatus } from "./api";
import { effectiveChatLocale } from "@genesis/i18n/detect";

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

export type ModuleStatus = {
  id: string;
  label: string;
  status: string;
};

export type OwnerNotification = {
  at: string;
  title: string;
  message: string;
  order_id: string | null;
  read: boolean;
};

export type ActivityEvent = {
  at: string;
  message: string;
  task_id: string | null;
};

export type ProductCheck = {
  label?: string;
  name?: string;
  ok?: boolean;
  passed?: boolean;
};

export type FactoryProduct = {
  product_id: string;
  product_type: string;
  business_name: string;
  description: string;
  status: string;
  status_label: string;
  quality_percent: number;
  checks: ProductCheck[];
  owner_approved: boolean;
  owner_approved_at: string | null;
  published: boolean;
  published_at: string | null;
  public_url: string | null;
  delivered_to_client: boolean;
  delivered_at: string | null;
  revision: number;
  created_at: string;
  updated_at: string;
  preview_url: string;
};

export type AssistantResponse = {
  answer: string;
  source: string;
};

export type CursorTaskStep = {
  id: string;
  label: string;
  done: boolean;
  active: boolean;
};

export type CursorTask = {
  task_id: string;
  state: string;
  state_label: string;
  progress_percent: number | null;
  progress_label?: string | null;
  steps: CursorTaskStep[];
  cursor_opened?: boolean;
  cursor_message?: string | null;
  verify_summary?: string | null;
  task_note?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CursorStatus = {
  mode: string;
  bridge_ready: boolean;
  label: string;
  status_icon: string;
  status_label: string;
  hint: string;
  cursor_cli_available?: boolean;
  active_task_id?: string | null;
};

export type CursorHistoryItem = {
  at: string | null;
  kind: string | null;
  task_note: string | null;
  chars: number | null;
};

export type AiHubPlanStep = {
  id: string;
  title: string;
  capability: string;
  provider_id?: string | null;
  tool_id?: string | null;
  requires_approve: boolean;
  status: string;
};

export type AiHubTask = {
  id: string;
  input_text: string;
  input_type: string;
  locale: string;
  project_id: string;
  phase: string;
  plan: AiHubPlanStep[];
  plan_summary: string;
  approved_at?: string | null;
  cursor_task_id?: string | null;
  error?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  cursor_task?: CursorTask | null;
};

export type DevProject = {
  id: string;
  name: string;
  kind: string;
  path_label: string;
  available: boolean;
};

export type DevWorkspaceSnapshot = {
  projects: DevProject[];
  suggestions: {
    id: string;
    title: string;
    detail: string;
    action: string;
    task_id?: string | null;
    project_id?: string | null;
  }[];
  build_history: {
    at: string | null;
    task_id: string | null;
    label: string | null;
    state: string | null;
    state_label: string | null;
    verify_summary: string | null;
  }[];
};

export type DevFileEntry = {
  path: string;
  name: string;
  is_dir: boolean;
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

export async function fetchModules(
  settings: AppSettings,
): Promise<ModuleStatus[]> {
  const data = await apiJson<{ modules: ModuleStatus[] }>(
    settings,
    "/api/modules",
  );
  return data.modules;
}

export async function fetchNotifications(
  settings: AppSettings,
): Promise<OwnerNotification[]> {
  const data = await apiJson<{ notifications: OwnerNotification[] }>(
    settings,
    "/api/owner/notifications",
  );
  return data.notifications;
}

export async function fetchActivity(
  settings: AppSettings,
  limit = 12,
): Promise<ActivityEvent[]> {
  const data = await apiJson<{ events: ActivityEvent[] }>(
    settings,
    `/api/activity?limit=${limit}`,
  );
  return data.events;
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

export async function fetchProject(
  settings: AppSettings,
  productId: string,
): Promise<FactoryProduct> {
  return apiJson<FactoryProduct>(
    settings,
    `/api/factory/products/${productId}`,
  );
}

export async function askAssistant(
  settings: AppSettings,
  question: string,
): Promise<AssistantResponse> {
  const locale = effectiveChatLocale(settings.locale, question);
  return apiJson<AssistantResponse>(settings, "/api/assistant/ask", {
    method: "POST",
    body: JSON.stringify({ question, locale }),
  });
}

export async function fetchCursorStatus(
  settings: AppSettings,
): Promise<CursorStatus> {
  return apiJson<CursorStatus>(settings, "/api/cursor/status");
}

export async function fetchCursorTasks(
  settings: AppSettings,
): Promise<CursorTask[]> {
  const data = await apiJson<{ tasks: CursorTask[] }>(
    settings,
    "/api/cursor/tasks",
  );
  return data.tasks;
}

export async function fetchCursorHistory(
  settings: AppSettings,
): Promise<CursorHistoryItem[]> {
  const data = await apiJson<{ items: CursorHistoryItem[] }>(
    settings,
    "/api/cursor/history",
  );
  return data.items;
}

export async function cursorVerify(
  settings: AppSettings,
): Promise<{ ok: boolean; message: string; task?: CursorTask }> {
  return apiJson(settings, "/api/cursor/task/verify", { method: "POST" });
}

export async function createAiHubTask(
  settings: AppSettings,
  input_text: string,
  project_id?: string,
): Promise<AiHubTask> {
  const data = await apiJson<{ task: AiHubTask }>(
    settings,
    "/api/ai-hub/tasks",
    {
      method: "POST",
      body: JSON.stringify({
        input_text,
        locale: settings.locale,
        project_id,
        input_type: "text",
      }),
    },
  );
  return data.task;
}

export async function fetchAiHubTasks(
  settings: AppSettings,
): Promise<AiHubTask[]> {
  const data = await apiJson<{ tasks: AiHubTask[] }>(
    settings,
    "/api/ai-hub/tasks",
  );
  return data.tasks;
}

export async function fetchAiHubActive(
  settings: AppSettings,
): Promise<AiHubTask | null> {
  const data = await apiJson<{ task: AiHubTask | null }>(
    settings,
    "/api/ai-hub/tasks/active",
  );
  return data.task;
}

export async function approveAiHubTask(
  settings: AppSettings,
  taskId: string,
): Promise<AiHubTask> {
  const data = await apiJson<{ task: AiHubTask }>(
    settings,
    `/api/ai-hub/tasks/${taskId}/approve`,
    { method: "POST", body: JSON.stringify({ auto_open: true }) },
  );
  return data.task;
}

export async function verifyAiHubTask(
  settings: AppSettings,
  taskId: string,
): Promise<{ ok: boolean; message: string; hub_task?: AiHubTask }> {
  return apiJson(settings, `/api/ai-hub/tasks/${taskId}/verify`, {
    method: "POST",
  });
}

export async function fetchDevWorkspace(
  settings: AppSettings,
): Promise<DevWorkspaceSnapshot> {
  return apiJson<DevWorkspaceSnapshot>(settings, "/api/dev/workspace");
}

export async function fetchDevProjectFiles(
  settings: AppSettings,
  projectId: string,
): Promise<DevFileEntry[]> {
  return apiJson<DevFileEntry[]>(
    settings,
    `/api/dev/projects/${projectId}/files`,
  );
}
