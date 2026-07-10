"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";
import {
  fetchProjectPlatform,
  type ArtifactFolder,
  type CustomerProject,
  type ProjectPlatformState,
} from "../lib/projectApi";
import { getVisitorId } from "../lib/visitorId";
import { ButtonLink, Card } from "./ui";

type Props = {
  onStartProject?: () => void;
};

const FOLDER_ICONS: Record<string, string> = {
  website: "🌐",
  business_plan: "📊",
  presentation: "📽",
  documents: "📄",
  images: "🖼",
  source: "💻",
  archive: "📦",
};

type MainView = "artifacts" | "history";

export function ProjectPlatformShell({ onStartProject }: Props) {
  const { t } = useTranslation("site");
  const { t: tChat } = useTranslation("chat");
  const [state, setState] = useState<ProjectPlatformState | null>(null);
  const [loading, setLoading] = useState(true);
  const [mainView, setMainView] = useState<MainView>("artifacts");
  const [activeVersion, setActiveVersion] = useState<number | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    const data = await fetchProjectPlatform(getVisitorId("public"));
    setState(data);
    if (data.project?.versions.length) {
      const latest = data.project.versions[data.project.versions.length - 1]?.version ?? null;
      setActiveVersion((prev) => prev ?? latest);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void reload();
    const onUpdate = () => void reload();
    window.addEventListener("genesis:project-updated", onUpdate);
    return () => window.removeEventListener("genesis:project-updated", onUpdate);
  }, [reload]);

  const project = state?.project;
  const showProject = Boolean(project && (state?.has_project || project.mode === "project"));

  const folders = useMemo(() => {
    if (!project?.artifact_folders?.length) return [];
    if (activeVersion == null) return project.artifact_folders;
    return project.artifact_folders
      .map((folder) => ({
        ...folder,
        items: folder.items.filter((item) => item.version === activeVersion),
        count: folder.items.filter((item) => item.version === activeVersion).length,
      }))
      .filter((folder) => folder.count > 0);
  }, [project, activeVersion]);

  if (loading && !state) {
    return (
      <div className="flex h-full min-h-0 items-center justify-center text-sm text-genesis-muted">
        Загрузка проекта…
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      {!showProject ? (
        <>
          <HubHeader title={t("hubTitle")} subtitle={t("hubSubtitle", { assistant: ASSISTANT_NAME })} />
          <ConversationEmptyState
            onStartProject={onStartProject}
            t={t}
            tChat={tChat}
            hint={state?.vector_hint}
          />
        </>
      ) : (
        project && (
          <>
            <ProjectIdentityCard project={project} />
            <ProjectProgressBar progress={project.progress} activity={project.activity} />
            <ProjectMainNav active={mainView} onSelect={setMainView} />
            {mainView === "history" ? (
              <ProjectTimelinePanel events={project.timeline} />
            ) : (
              <>
                {project.versions.length > 1 && (
                  <ProjectVersionPicker
                    versions={project.versions}
                    active={activeVersion}
                    onSelect={setActiveVersion}
                  />
                )}
                <ProjectArtifactsWorkspace folders={folders} />
              </>
            )}
          </>
        )
      )}

      <Card padding="md" className="mt-auto border-emerald-500/20 bg-emerald-950/20">
        <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400/90">
          {ASSISTANT_NAME} · Project Manager
        </p>
        <p className="mt-2 text-sm text-genesis-muted">
          {state?.vector_hint || t("hubCooHint")}
        </p>
        <button
          type="button"
          onClick={onStartProject}
          className="mt-3 text-sm font-medium text-genesis-accent hover:underline"
        >
          {t("hubOpenVector")} →
        </button>
      </Card>
    </div>
  );
}

function HubHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="shrink-0">
      <p className="text-[10px] font-bold tracking-[0.22em] text-genesis-accent uppercase">
        {BRAND_NAME}
      </p>
      <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">{title}</h1>
      <p className="mt-2 text-sm text-genesis-muted">{subtitle}</p>
    </div>
  );
}

function ProjectIdentityCard({ project }: { project: CustomerProject }) {
  const id = project.identity;
  const health = project.health;
  const nextAction = project.next_action;
  const healthToneClass: Record<string, string> = {
    green: "text-emerald-300",
    yellow: "text-amber-300",
    blue: "text-sky-300",
    red: "text-rose-300",
  };
  return (
    <Card glow padding="md" className="border-genesis-accent/25">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="text-[10px] font-bold tracking-[0.22em] text-genesis-accent uppercase">
          {BRAND_NAME} · Проект
        </p>
        {health && (
          <p
            className={`text-xs font-medium ${healthToneClass[health.tone] ?? "text-genesis-muted"}`}
          >
            {health.emoji} {health.label}
          </p>
        )}
      </div>
      <h1 className="mt-2 text-xl font-bold text-white sm:text-2xl">{id?.title || project.title}</h1>
      <p className="mt-2 text-sm leading-relaxed text-genesis-muted">
        {id?.description || project.description}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <MetaBadge label="Тип" value={id?.type_label || "Проект"} />
        <MetaBadge label="Рынок" value={id?.market || project.market || "Не указан"} />
        <MetaBadge label="Статус" value={id?.status || "В работе"} accent />
      </div>
      {nextAction && (
        <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-genesis-muted">
            Следующее действие
          </p>
          <p className="mt-1 text-sm font-medium text-white">✔ {nextAction.label}</p>
        </div>
      )}
      <p className="mt-3 text-xs text-genesis-muted/80">
        Последнее изменение: {id?.last_updated || "—"}
      </p>
    </Card>
  );
}

function MetaBadge({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs ${
        accent
          ? "bg-emerald-500/15 text-emerald-300"
          : "bg-white/5 text-genesis-muted"
      }`}
    >
      <span className="opacity-70">{label}:</span>
      <span className="font-medium text-white">{value}</span>
    </span>
  );
}

function ProjectProgressBar({
  progress,
  activity,
}: {
  progress: CustomerProject["progress"];
  activity?: CustomerProject["activity"];
}) {
  if (!progress?.stages?.length) return null;
  return (
    <Card padding="md" hover={false}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="genesis-label">Прогресс проекта</p>
        <span className="text-sm font-semibold text-genesis-accent">{progress.percent}%</span>
      </div>
      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-genesis-accent to-emerald-500 transition-all"
          style={{ width: `${progress.percent}%` }}
        />
      </div>
      <ol className="grid grid-cols-5 gap-1">
        {progress.stages.map((stage) => (
          <li key={stage.id} className="text-center">
            <div
              className={`mx-auto mb-1.5 h-2 w-2 rounded-full ${
                stage.state === "done"
                  ? "bg-emerald-400"
                  : stage.state === "current"
                    ? "bg-genesis-accent ring-2 ring-genesis-accent/40"
                    : "bg-white/15"
              }`}
            />
            <p
              className={`text-[10px] leading-tight sm:text-xs ${
                stage.state === "current" ? "font-semibold text-white" : "text-genesis-muted"
              }`}
            >
              {stage.label}
            </p>
          </li>
        ))}
      </ol>
      {activity && (
        <div className="mt-4 border-t border-white/8 pt-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-genesis-muted">
            Последняя активность
          </p>
          <p className="mt-1 text-sm text-white">{activity.summary}</p>
          <p className="mt-0.5 text-xs text-genesis-muted">{activity.when}</p>
        </div>
      )}
    </Card>
  );
}

function ProjectMainNav({
  active,
  onSelect,
}: {
  active: MainView;
  onSelect: (v: MainView) => void;
}) {
  const tabs: { id: MainView; label: string }[] = [
    { id: "artifacts", label: "Артефакты" },
    { id: "history", label: "История" },
  ];
  return (
    <div className="flex gap-1.5">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onSelect(tab.id)}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
            active === tab.id
              ? "bg-genesis-accent/25 text-white"
              : "bg-white/5 text-genesis-muted hover:text-white"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function ConversationEmptyState({
  onStartProject,
  t,
  tChat,
  hint,
}: {
  onStartProject?: () => void;
  t: (k: string) => string;
  tChat: (k: string) => string;
  hint?: string;
}) {
  return (
    <>
      <Card glow padding="lg" className="border-dashed border-genesis-accent/30 bg-genesis-panel/50">
        <p className="text-[10px] font-bold tracking-[0.22em] text-genesis-accent uppercase">
          Добро пожаловать
        </p>
        <p className="mt-2 text-base font-semibold text-white">
          Здесь будут храниться все проекты вашей цифровой компании
        </p>
        <p className="mt-2 text-sm leading-relaxed text-genesis-muted">
          {hint ||
            "Начните с первой идеи или поручите её Vector — сайт, бизнес-план, документы и любые результаты появятся здесь как живые проекты с версиями и артефактами."}
        </p>
        <p className="mt-3 text-xs text-genesis-muted/90">
          Conversation Mode: общайтесь свободно. Когда понадобится результат — {ASSISTANT_NAME}{" "}
          предложит создать проект.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onStartProject}
            className="rounded-xl bg-gradient-to-r from-genesis-accent to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-glow hover:opacity-90"
          >
            {t("hubNewProject")}
          </button>
          <ButtonLink href="/services" variant="secondary" size="sm">
            {t("hubViewServices")}
          </ButtonLink>
        </div>
      </Card>
      <QuickTasks onStartProject={onStartProject} t={t} />
    </>
  );
}

function QuickTasks({
  onStartProject,
  t,
}: {
  onStartProject?: () => void;
  t: (k: string) => string;
}) {
  const tasks = [
    { labelKey: "hubQuickSite", prompt: "Создай сайт для моего бизнеса" },
    { labelKey: "hubQuickPlan", prompt: "Помоги с бизнес-планом" },
    { labelKey: "hubQuickPresentation", prompt: "Подготовь презентацию для инвесторов" },
  ];
  return (
    <div>
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-genesis-muted">
        {t("hubQuickTitle")}
      </p>
      <div className="grid gap-2 sm:grid-cols-3">
        {tasks.map((task) => (
          <button
            key={task.labelKey}
            type="button"
            onClick={() => {
              onStartProject?.();
              window.dispatchEvent(
                new CustomEvent("genesis:assign-task", { detail: { prompt: task.prompt } }),
              );
            }}
            className="rounded-xl border border-genesis-border-subtle bg-genesis-panel/60 px-4 py-3 text-left text-sm text-white transition hover:border-genesis-accent/40"
          >
            {t(task.labelKey)}
          </button>
        ))}
      </div>
    </div>
  );
}

function ProjectTimelinePanel({ events }: { events: CustomerProject["timeline"] }) {
  if (!events.length) {
    return (
      <Card padding="md" hover={false}>
        <p className="text-sm text-genesis-muted">Журнал работы появится по мере прогресса.</p>
      </Card>
    );
  }
  return (
    <Card padding="md" hover={false}>
      <p className="genesis-label">Журнал проекта</p>
      <ol className="mt-3 space-y-3">
        {[...events].reverse().map((e) => (
          <li key={e.id} className="border-l-2 border-genesis-accent/40 pl-3">
            <p className="text-sm font-medium text-white">{e.label}</p>
            {e.detail && <p className="mt-0.5 text-xs text-genesis-muted">{e.detail}</p>}
          </li>
        ))}
      </ol>
    </Card>
  );
}

function ProjectVersionPicker({
  versions,
  active,
  onSelect,
}: {
  versions: CustomerProject["versions"];
  active: number | null;
  onSelect: (v: number) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-genesis-muted">
        Версия
      </span>
      {versions.map((v) => (
        <button
          key={v.version}
          type="button"
          onClick={() => onSelect(v.version)}
          className={`rounded-lg px-2.5 py-1 text-xs font-medium transition ${
            active === v.version
              ? "bg-genesis-accent/25 text-white"
              : "bg-white/5 text-genesis-muted hover:text-white"
          }`}
          title={v.summary}
        >
          {v.label}
        </button>
      ))}
    </div>
  );
}

function ProjectArtifactsWorkspace({ folders }: { folders: ArtifactFolder[] }) {
  if (!folders.length) {
    return (
      <Card padding="md" hover={false} className="border-dashed border-white/10">
        <p className="text-[10px] font-bold tracking-[0.22em] text-genesis-accent uppercase">
          Рабочая папка проекта
        </p>
        <p className="mt-2 text-sm text-genesis-muted">
          Здесь появятся результаты работы — Website, Documents, Source и другие материалы.
          Vector добавляет их после каждой версии.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <p className="genesis-label">Рабочая папка проекта</p>
      {folders.map((folder) => (
        <Card key={folder.id} padding="md" hover={false} className="border-white/8">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-lg" aria-hidden>
              {FOLDER_ICONS[folder.id] ?? "📁"}
            </span>
            <div>
              <p className="text-sm font-semibold text-white">{folder.label}</p>
              <p className="text-[10px] text-genesis-muted">
                {folder.count} {folder.count === 1 ? "результат" : "результата"}
              </p>
            </div>
          </div>
          <ul className="space-y-2">
            {folder.items.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between gap-3 rounded-lg bg-white/5 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm text-white">{item.label}</p>
                  <p className="text-[10px] text-genesis-muted">{item.version_label}</p>
                </div>
                {item.href ? (
                  <Link
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0 text-xs font-medium text-genesis-accent hover:underline"
                  >
                    Открыть
                  </Link>
                ) : (
                  <span className="text-[10px] text-genesis-muted">скоро</span>
                )}
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  );
}
