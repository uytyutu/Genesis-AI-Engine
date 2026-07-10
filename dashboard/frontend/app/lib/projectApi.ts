import { publicApiBase } from "./publicApiBase";
import { getVisitorId } from "./visitorId";

const API = publicApiBase();

export type ProjectArtifact = {
  id: string;
  kind: string;
  label: string;
  href: string | null;
  section: string;
  version: number;
};

export type ProjectVersion = {
  version: number;
  label: string;
  created_at: string;
  summary: string;
  artifacts: ProjectArtifact[];
};

export type TimelineEvent = {
  id: string;
  type: string;
  label: string;
  at: string;
  detail?: string;
};

export type ProjectSection = {
  id: string;
  label_ru: string;
  artifact_count: number;
  active?: boolean;
  status?: string;
};

export type ProjectIdentity = {
  title: string;
  type_label: string;
  type_id: string | null;
  artifact_label: string;
  market: string;
  status: string;
  last_updated: string;
  last_updated_at: string;
  description: string;
};

export type ProgressStage = {
  id: string;
  label: string;
  state: "done" | "current" | "upcoming";
};

export type ProjectProgress = {
  percent: number;
  current_stage_id: string;
  current_stage_label: string;
  stages: ProgressStage[];
};

export type ProjectHealth = {
  tone: "green" | "yellow" | "blue" | "red";
  emoji: string;
  label: string;
};

export type ProjectNextAction = {
  label: string;
  kind: string;
};

export type ProjectActivity = {
  summary: string;
  when: string;
};

export type ArtifactFolderItem = {
  id: string;
  kind: string;
  label: string;
  href: string | null;
  version: number;
  version_label: string;
};

export type ArtifactFolder = {
  id: string;
  label: string;
  count: number;
  items: ArtifactFolderItem[];
};

export type CustomerProject = {
  project_id: string;
  workspace_id: string;
  title: string;
  mode: "conversation" | "project";
  lifecycle_phase: string;
  active_section: string;
  next_step_hint: string;
  description: string;
  market: string;
  identity: ProjectIdentity;
  progress: ProjectProgress;
  health: ProjectHealth;
  next_action: ProjectNextAction;
  activity: ProjectActivity;
  artifact_folders: ArtifactFolder[];
  sections: ProjectSection[];
  timeline: TimelineEvent[];
  versions: ProjectVersion[];
};

export type ProjectPlatformState = {
  version: string;
  has_project: boolean;
  mode: "conversation" | "project";
  visitor_id: string;
  project: CustomerProject | null;
  vector_hint: string;
};

export async function fetchProjectPlatform(
  visitorId?: string
): Promise<ProjectPlatformState> {
  const vid = visitorId ?? getVisitorId("public");
  try {
    const res = await fetch(
      `${API}/api/public/project?visitor_id=${encodeURIComponent(vid)}`,
      { cache: "no-store" }
    );
    if (!res.ok) throw new Error("project_fetch_failed");
    return res.json();
  } catch {
    return {
      version: "project-platform-v1",
      has_project: false,
      mode: "conversation",
      visitor_id: vid,
      project: null,
      vector_hint: "",
    };
  }
}

export async function activateProject(
  serviceId: string,
  title: string,
  visitorId?: string
): Promise<ProjectPlatformState> {
  const vid = visitorId ?? getVisitorId("public");
  const res = await fetch(`${API}/api/public/project/activate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      visitor_id: vid,
      service_id: serviceId,
      title,
    }),
  });
  if (!res.ok) throw new Error("activate_failed");
  return res.json();
}
