import type { ProjectPlatformState } from "./projectApi";

export type OrderLaunchContext = {
  company: string;
  projectLabel: string;
  businessLine: string;
  market: string;
  style: string;
  palette: string;
  versionLabel: string;
  approvedAt: string | null;
  previewHref: string | null;
  description: string;
  logoResolved: boolean;
};

function journeyValue(state: ProjectPlatformState, stepId: string): string {
  const item = state.project?.journey?.items.find((i) => i.id === stepId);
  if (!item?.value?.trim()) return "";
  if (item.status === "pending") return "";
  return item.value.trim();
}

function formatApprovedDate(iso: string | null | undefined): string | null {
  if (!iso?.trim()) return null;
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return null;
  }
}

export function buildOrderLaunchContext(
  state: ProjectPlatformState,
): OrderLaunchContext | null {
  if (!state.has_project || !state.project) return null;

  const project = state.project;
  const hasPreview = project.versions.some((v) =>
    v.artifacts.some((a) => a.kind === "preview" && a.href),
  );
  if (!hasPreview) return null;

  const company =
    journeyValue(state, "company") ||
    (project.identity.title !== "Мой проект" ? project.identity.title : "");
  if (!company) return null;

  const projectLabel = project.identity?.type_label?.trim() || "Проект";

  const preview = project.versions
    .flatMap((v) => v.artifacts)
    .find((a) => a.kind === "preview" && a.href);

  const approvalEvent = [...(project.timeline ?? [])]
    .reverse()
    .find((e) => e.type === "approval");

  const market = journeyValue(state, "country") || project.market || "";
  const style = journeyValue(state, "design") || "";
  const palette = journeyValue(state, "colors") || "";
  const versionLabel =
    journeyValue(state, "draft") ||
    project.versions[project.versions.length - 1]?.label ||
    "Версия 1";

  const logoItem = project.journey?.items.find((i) => i.id === "logo");
  const logoResolved = logoItem?.status === "done";

  const description = (project.description || project.identity.description || "")
    .split("\n")
    .find((line) => line.includes("солнеч") || line.includes("панел") || line.length > 24)
    ?.trim() || project.description?.trim() || "";

  return {
    company,
    projectLabel,
    businessLine: description.split(/[.!?\n]/)[0]?.trim() || "Сайт для бизнеса",
    market,
    style,
    palette,
    versionLabel,
    approvedAt: formatApprovedDate(
      approvalEvent?.at || project.identity.last_updated_at,
    ),
    previewHref: preview?.href ?? null,
    description: description || `${company} — сайт, согласованный вместе с Vector`,
    logoResolved,
  };
}
