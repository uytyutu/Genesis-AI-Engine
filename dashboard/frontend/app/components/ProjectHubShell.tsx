"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";
import { ButtonLink, Card } from "./ui";

type Props = {
  onStartProject?: () => void;
};

const QUICK_TASKS = [
  { labelKey: "hubQuickSite", prompt: "Создай сайт для моего бизнеса" },
  { labelKey: "hubQuickPlan", prompt: "Помоги с бизнес-планом" },
  { labelKey: "hubQuickPresentation", prompt: "Подготовь презентацию для инвесторов" },
] as const;

export function ProjectHubShell({ onStartProject }: Props) {
  const { t } = useTranslation("site");
  const { t: tChat } = useTranslation("chat");

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <div className="shrink-0">
        <p className="text-[10px] font-bold tracking-[0.22em] text-genesis-accent uppercase">
          {BRAND_NAME}
        </p>
        <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">{t("hubTitle")}</h1>
        <p className="mt-2 text-sm text-genesis-muted">
          {t("hubSubtitle", { assistant: ASSISTANT_NAME })}
        </p>
      </div>

      <Card
        glow
        padding="lg"
        className="border-dashed border-genesis-accent/30 bg-genesis-panel/50"
      >
        <p className="text-[10px] font-bold tracking-[0.22em] text-genesis-accent uppercase">
          {tChat("workspaceTitle")}
        </p>
        <p className="mt-2 text-base font-semibold text-white">{tChat("workspaceEmpty")}</p>
        <p className="mt-2 text-sm text-genesis-muted">{tChat("workspaceEmptyHint")}</p>
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

      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-genesis-muted">
          {t("hubQuickTitle")}
        </p>
        <div className="grid gap-2 sm:grid-cols-3">
          {QUICK_TASKS.map((task) => (
            <button
              key={task.labelKey}
              type="button"
              onClick={() => {
                onStartProject?.();
                window.dispatchEvent(
                  new CustomEvent("genesis:assign-task", { detail: { prompt: task.prompt } }),
                );
              }}
              className="rounded-xl border border-genesis-border-subtle bg-genesis-panel/60 px-4 py-3 text-left text-sm text-white transition hover:border-genesis-accent/40 hover:bg-genesis-elevated/80"
            >
              {t(task.labelKey)}
            </button>
          ))}
        </div>
      </div>

      <Card padding="md" className="mt-auto border-emerald-500/20 bg-emerald-950/20">
        <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400/90">
          {ASSISTANT_NAME} · COO
        </p>
        <p className="mt-2 text-sm font-medium text-white">{t("hubCooReady")}</p>
        <p className="mt-1 text-sm text-genesis-muted">{t("hubCooHint")}</p>
        <Link
          href="/site?view=vector"
          className="mt-3 inline-block text-sm font-medium text-genesis-accent hover:underline"
        >
          {t("hubOpenVector")} →
        </Link>
      </Card>
    </div>
  );
}
