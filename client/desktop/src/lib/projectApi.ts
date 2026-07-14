import type { AppSettings } from "./settings";
import { apiBase } from "./apiClient";

export type CustomerProject = {
  project_id: string;
  workspace_id: string;
  title: string;
  mode: string;
  lifecycle_phase: string;
  next_step_hint: string;
  description: string;
  market: string;
  identity?: {
    title: string;
    type_label: string;
    status: string;
    description: string;
    last_updated: string;
  };
  progress?: {
    percent: number;
    current_stage_label: string;
    stages: { id: string; label: string; state: string }[];
  };
  health?: { emoji: string; label: string };
  next_action?: { label: string };
  activity?: { summary: string; when: string };
  artifact_folders?: {
    id: string;
    label: string;
    count: number;
    items: { label: string; href: string | null }[];
  }[];
  sections?: { id: string; label_ru: string; artifact_count: number }[];
  timeline?: { label: string; at: string; detail?: string }[];
};

export type ProjectPlatformState = {
  has_project: boolean;
  project: CustomerProject | null;
  vector_hint: string;
};

export async function fetchCustomerProject(
  settings: AppSettings,
  visitorId: string,
): Promise<ProjectPlatformState> {
  const base = apiBase(settings);
  const res = await fetch(
    `${base}/api/public/project?visitor_id=${encodeURIComponent(visitorId)}&locale=ru`,
    { cache: "no-store" },
  );
  if (!res.ok) {
    throw new Error("Не удалось загрузить проекты. Проверьте подключение.");
  }
  const data = (await res.json()) as ProjectPlatformState & {
    project: CustomerProject | null;
  };
  return {
    has_project: Boolean(data.has_project && data.project),
    project: data.project,
    vector_hint: data.vector_hint || "",
  };
}
