"use client";

import { useState } from "react";
import { onGithubLinkClick } from "../lib/farmGithubGate";

/** Honest Execution Timeline — states, not fake checkmarks. */

export type TimelineTask = {
  status?: string;
  pipeline_state?: string;
  pr_url?: string;
  pr_id?: string | number | null;
  real_income?: boolean;
  merge_status?: string;
  execution_error?: string;
  execution_heal?: string;
  execution_checklist?: { id: string; title: string; done?: boolean }[];
  execution?: {
    stage?: string;
    ok?: boolean;
    branch?: string;
    workspace?: string;
    error?: string;
    error_detail?: string;
    patch_ready?: boolean;
    message_ru?: string;
    ready_for_ceo?: { message_ru?: string; route?: string; patch_ready?: boolean };
    stages?: Record<
      string,
      {
        ok?: boolean;
        skipped?: boolean;
        note_ru?: string;
        error_detail?: string;
        mode?: string;
        route?: string;
        brief_path?: string;
        draft?: boolean;
        body_path?: string;
        message_ru?: string;
        files_touched?: string[];
        executor?: string;
        can_generate_patch?: boolean;
        summary?: string;
        reason?: string;
      }
    >;
  };
};

/** Pipeline step visual state — never use "done" for work that did not happen. */
export type StepState =
  | "done"
  | "external"
  | "waiting"
  | "pending"
  | "paused"
  | "failed";

type Step = {
  id: string;
  label: string;
  state: StepState;
  /** Short status chip (user-facing) */
  statusText: string;
  detail?: string;
  /** Expand panel — shown when step is selected */
  explain?: string;
};

export type TimelineModel = {
  headline: string;
  sentToGithub: boolean;
  nextAction: string;
  branch:
    | "not_started"
    | "needs_external"
    | "research_patch"
    | "local_patch"
    | "submitted"
    | "failed";
  patchReady: boolean;
  steps: Step[];
};

function checklistDone(t: TimelineTask, id: string): boolean {
  return Boolean(t.execution_checklist?.find((s) => s.id === id)?.done);
}

function resolveRoute(t: TimelineTask): string | undefined {
  return (
    t.execution?.ready_for_ceo?.route ||
    (t.execution?.stages?.routing as { route?: string } | undefined)?.route ||
    t.execution?.stages?.implementation?.mode
  );
}

const EXTERNAL_PAUSE_EXPLAIN =
  "Impossible in auto mode. Engine could not produce a safe repository patch. This task must be Skipped — Virtus Core will not ask the CEO to open Cursor or write a diff by hand.";

const RESEARCH_FORK_EXPLAIN =
  "Auto factory: Research Agent → Codex/Groq → patch. If no patch: Skip forever → next TAKE. Human Cursor is not part of the CEO path.";

/**
 * Pure timeline model — safe to unit-test without React.
 */
export function buildExecutionTimeline(
  t: TimelineTask,
  githubTokenReady?: boolean,
): TimelineModel {
  const route = resolveRoute(t);
  const engineStage = String(t.execution?.stage || "");
  const pipeline = String(t.pipeline_state || "");
  const activelyRunning =
    ["QUEUED", "CLONING", "ANALYSING", "PATCHING", "TESTING", "COMMITTING"].includes(
      pipeline,
    ) ||
    ["queued", "running", "repo_intelligence", "planning", "implementation", "research", "validation", "commit"].includes(
      engineStage,
    ) ||
    t.status === "executing";

  const ranEngine =
    Boolean(t.execution) ||
    checklistDone(t, "repo_intel") ||
    t.status === "draft_pr" ||
    t.status === "pr_submitted" ||
    t.status === "executing" ||
    Boolean(t.pr_url);
  const hasPr = Boolean(t.pr_url);
  const submitted =
    hasPr ||
    [
      "pr_submitted",
      "maintainer_review",
      "merged",
      "reward_approved",
      "payment_available",
      "withdraw",
      "payout_confirmed",
      "completed",
    ].includes(String(t.status || ""));
  const refused = route === "refuse" || t.execution?.stage === "failed";
  const healOnly =
    Boolean(t.execution_heal) ||
    String(t.execution_error || "").startsWith("zombie_queued") ||
    t.execution_error === "factory_busy";
  const hardFail =
    refused ||
    t.execution?.stage === "failed" ||
    (Boolean(t.execution_error) && !healOnly);
  const impl = t.execution?.stages?.implementation;
  const research = t.execution?.stages?.research;
  const validation = t.execution?.stages?.validation;
  const needsExternalRoute =
    route === "needs_external" ||
    String(impl?.mode || "") === "needs_external" ||
    t.status === "needs_external";
  const filesTouched = (impl?.files_touched || []).length > 0;
  const implMode = String(impl?.mode || "");
  const researchExecutor = String(research?.executor || impl?.executor || "");

  // Real patch = files actually written (never trust mode=ok alone)
  const patchReady = Boolean(
    t.execution?.patch_ready || filesTouched || t.execution?.ready_for_ceo?.patch_ready,
  );
  // Never "paused" while engine is still running — one state machine
  const pausedExternal = needsExternalRoute && !patchReady && !activelyRunning;

  const cloned =
    checklistDone(t, "repo_intel") || Boolean(t.execution?.stages?.repo_intelligence?.ok);
  const planned =
    checklistDone(t, "planning") || Boolean(t.execution?.stages?.planning?.ok);
  const researchDone = Boolean(research?.ok) || checklistDone(t, "research");

  let branch: TimelineModel["branch"] = "not_started";
  if (hardFail) {
    branch = "failed";
  } else if (hasPr || submitted) {
    branch = "submitted";
  } else if (pausedExternal) {
    branch = "needs_external";
  } else if (patchReady && (implMode.startsWith("research_then_") || researchDone)) {
    branch = "research_patch";
  } else if (ranEngine) {
    branch = "local_patch";
  }

  const onlyQueued =
    activelyRunning &&
    !cloned &&
    !planned &&
    !patchReady &&
    (engineStage === "queued" || pipeline === "QUEUED" || !t.execution?.stages);

  const steps: Step[] = [
    {
      id: "approve",
      label: "Approve",
      state: checklistDone(t, "approve") || Boolean(t.status) ? "done" : "pending",
      statusText:
        checklistDone(t, "approve") || Boolean(t.status) ? "Done" : "Not started",
    },
    {
      id: "clone",
      label: "Clone",
      state: !ranEngine
        ? "pending"
        : cloned
          ? "done"
          : refused
            ? "failed"
            : onlyQueued || activelyRunning
              ? "waiting"
              : "pending",
      statusText: !ranEngine
        ? "Not started"
        : cloned
          ? "Done"
          : refused
            ? "Failed"
            : onlyQueued
              ? "Queued"
              : activelyRunning
                ? "In progress"
                : "Not started",
      detail: t.execution?.workspace
        ? `workspace: ${t.execution.workspace}`
        : undefined,
    },
    {
      id: "analyze",
      label: "Analysis",
      state: !ranEngine
        ? "pending"
        : planned || cloned
          ? "done"
          : activelyRunning && cloned
            ? "waiting"
            : "pending",
      statusText: !ranEngine
        ? "Not started"
        : planned || cloned
          ? "Done"
          : activelyRunning && cloned
            ? "In progress"
            : "Not started",
    },
    {
      id: "planning",
      label: "Planning",
      state: !ranEngine ? "pending" : planned ? "done" : "pending",
      statusText: !ranEngine ? "Not started" : planned ? "Done" : "Not started",
    },
  ];

  if (pausedExternal) {
    steps.push(
      {
        id: "implement",
        label: "Implementation",
        state: "external",
        statusText: "External research required",
        detail: `Fork: needs_external · executor=${researchExecutor || "none"}`,
        explain: EXTERNAL_PAUSE_EXPLAIN,
      },
      {
        id: "research",
        label: "Research Agent",
        state: researchDone ? "done" : research?.skipped ? "paused" : "waiting",
        statusText: researchDone
          ? "Brief prepared"
          : research?.skipped
            ? "Skipped (no API key)"
            : "Pending / running",
        detail:
          research?.brief_path ||
          impl?.brief_path ||
          "RESEARCH_BRIEF / EXTERNAL_TOOL_BRIEF",
        explain: RESEARCH_FORK_EXPLAIN,
      },
      {
        id: "tests",
        label: "Validation",
        state: "waiting",
        statusText: "Waiting for implementation",
        detail: "Skipped — no patch to test",
      },
      {
        id: "commit",
        label: "Commit",
        state: "paused",
        statusText: "Not created",
        detail: "No repository files were modified",
      },
      {
        id: "draft_pr",
        label: "Draft PR",
        state: "paused",
        statusText: "Not submitted",
        detail: "GitHub has not received any work",
      },
    );
  } else {
    steps.push(
      {
        id: "research",
        label: "Research Agent",
        state: !ranEngine
          ? "pending"
          : researchDone
            ? "done"
            : implMode.startsWith("research_then_")
              ? "done"
              : "pending",
        statusText: researchDone || implMode.startsWith("research_then_")
          ? `Done${researchExecutor ? ` · ${researchExecutor}` : ""}`
          : "Not required / not run",
        detail: research?.brief_path || research?.summary,
        // explain only when relevant — avoids false "Execution paused" panel
      },
      {
        id: "implement",
        label: "Implementation",
        state: !ranEngine
          ? "pending"
          : refused
            ? "failed"
            : patchReady
              ? "done"
              : activelyRunning && !onlyQueued
                ? "waiting"
                : onlyQueued
                  ? "pending"
                  : ranEngine
                    ? "waiting"
                    : "pending",
        statusText: !ranEngine
          ? "Not started"
          : refused
            ? "Failed"
            : patchReady
              ? "Patch ready"
              : onlyQueued
                ? "Queued"
                : activelyRunning
                  ? "In progress"
                  : "Not started",
        detail: impl?.note_ru || impl?.message_ru,
      },
      {
        id: "tests",
        label: "Validation",
        state: !ranEngine
          ? "pending"
          : checklistDone(t, "validation") || (validation?.ok && !validation?.skipped)
            ? "done"
            : "pending",
        statusText: !ranEngine
          ? "Not started"
          : checklistDone(t, "validation") || (validation?.ok && !validation?.skipped)
            ? "Passed"
            : "Not run",
      },
      {
        id: "commit",
        label: "Commit",
        state: !ranEngine
          ? "pending"
          : checklistDone(t, "pr_intelligence") || Boolean(t.execution?.branch)
            ? patchReady
              ? "done"
              : "paused"
            : "pending",
        statusText: !ranEngine
          ? "Not started"
          : patchReady && t.execution?.branch
            ? `Branch ${t.execution.branch}`
            : "Not created",
        detail: t.execution?.branch ? `branch ${t.execution.branch}` : undefined,
      },
      {
        id: "draft_pr",
        label: "Draft PR",
        state: hasPr
          ? "done"
          : submitted
            ? "waiting"
            : ranEngine && patchReady
              ? "paused"
              : "pending",
        statusText: hasPr
          ? "Open on GitHub"
          : ranEngine && patchReady
            ? "Not submitted"
            : "Not started",
        detail: hasPr
          ? String(t.pr_url)
          : ranEngine && patchReady
            ? githubTokenReady === false
              ? "Требуется подтверждение: GITHUB_TOKEN · затем Draft PR"
              : "📤 Publishing… ждёт подтверждения Draft PR"
            : undefined,
      },
    );
  }

  steps.push(
    {
      id: "review",
      label: "Maintainer merge",
      state:
        t.status === "merged" ||
        t.merge_status === "merged" ||
        [
          "reward_approved",
          "payment_available",
          "withdraw",
          "payout_confirmed",
          "completed",
        ].includes(String(t.status || ""))
          ? "done"
          : hasPr
            ? "waiting"
            : "paused",
      statusText:
        t.status === "merged" || t.merge_status === "merged"
          ? "Merged"
          : hasPr
            ? "Waiting"
            : "Waiting",
    },
    {
      id: "reward",
      label: "REAL revenue",
      state: t.real_income ? "done" : "paused",
      statusText: t.real_income ? "Confirmed" : "0 €",
      detail: t.real_income
        ? "REAL confirmed"
        : "Estimated bounty only — not earned until payout",
    },
  );

  let headline: string;
  let nextAction: string;

  if (!ranEngine) {
    headline = "Ожидает Execution Engine — работа ещё не начиналась";
    nextAction = "🧠 Thinking… Approve должен запустить Execution автоматически";
  } else if (branch === "failed") {
    headline = "Execution остановлен с ошибкой";
    nextAction = String(
      t.execution_error || t.execution?.error_detail || "Смотрите лог",
    );
  } else if (healOnly && !patchReady && !hasPr && !activelyRunning) {
    headline =
      "Очередь сброшена после перезапуска — Execution ещё не шёл";
    nextAction = "🧠 Thinking… агент перезапустит Execution сам";
  } else if (pausedExternal) {
    headline =
      "Impossible в авто-режиме — патча нет (задача должна уйти в Skip)";
    nextAction =
      "🔍 Researching… Engine снимет задачу сам и возьмёт следующую TAKE";
  } else if (hasPr) {
    headline = "Отправлено на GitHub — Draft PR открыт";
    nextAction = "👀 Waiting for maintainer… · Sync после merge";
  } else if (patchReady) {
    headline =
      branch === "research_patch"
        ? "Research Agent + Codex: патч готов — на GitHub ещё НЕ отправлено"
        : "Локальный патч готов — на GitHub ещё НЕ отправлено";
    nextAction = githubTokenReady
      ? "Требуется ваше подтверждение: отправить Draft PR"
      : "Требуется ваше подтверждение: добавить GITHUB_TOKEN, затем отправить Draft PR";
  } else if (onlyQueued) {
    headline = `Pipeline: QUEUED — Execution стартовал, ждёт Clone`;
    nextAction = "🔍 Researching… Clone → Analysis → Implementation";
  } else if (
    ["TESTING", "validation"].includes(pipeline) ||
    engineStage === "validation"
  ) {
    headline = `Pipeline: ${pipeline || "RUNNING"} — Validation`;
    nextAction = "🧪 Testing…";
  } else if (
    ["COMMITTING", "PATCHING"].includes(pipeline) ||
    ["implementation", "commit", "patching"].includes(engineStage)
  ) {
    headline = `Pipeline: ${pipeline || "RUNNING"} — Implementation`;
    nextAction =
      pipeline === "COMMITTING" || engineStage === "commit"
        ? "📤 Publishing…"
        : "💻 Coding…";
  } else if (
    String(t.status || "") === "payment_available" ||
    String(t.status || "") === "withdraw" ||
    String(t.status || "") === "payout_confirmed"
  ) {
    headline = "Payout path";
    nextAction = "💰 Waiting for payout…";
  } else {
    headline = `Pipeline: ${pipeline || "RUNNING"} — Execution в процессе`;
    nextAction = "💻 Coding…";
  }

  return {
    headline,
    sentToGithub: hasPr,
    nextAction,
    branch,
    patchReady,
    steps,
  };
}

function mark(state: StepState): string {
  if (state === "done") return "✓";
  if (state === "external") return "◐";
  if (state === "failed") return "⛔";
  if (state === "waiting") return "…";
  if (state === "paused") return "⏸";
  return "○";
}

function stepClass(state: StepState): string {
  if (state === "done") return "text-emerald-100/90";
  if (state === "external") return "text-amber-100";
  if (state === "failed") return "text-rose-200";
  if (state === "waiting") return "text-sky-100/85";
  if (state === "paused") return "text-white/55";
  return "text-genesis-muted";
}

export function FarmExecutionTimeline({
  task,
  githubTokenReady,
}: {
  task: TimelineTask;
  githubTokenReady?: boolean;
}) {
  const model = buildExecutionTimeline(task, githubTokenReady);
  const defaultOpen =
    model.steps.find((s) => s.state === "external")?.id ||
    model.steps.find((s) => s.explain)?.id ||
    null;
  const [openId, setOpenId] = useState<string | null>(defaultOpen);

  return (
    <div className="mt-3 rounded-xl border border-white/10 bg-black/25 px-3 py-2.5">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-sky-200/90">
        Execution Timeline
      </p>
      {model.branch === "needs_external" ? (
        <p className="mt-1 inline-flex rounded-md border border-amber-400/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-100">
          Process fork · needs_external (Research Agent / Codex — not an error)
        </p>
      ) : null}
      {model.branch === "research_patch" ? (
        <p className="mt-1 inline-flex rounded-md border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-100">
          Research Agent + Codex · patch ready · GitHub not yet
        </p>
      ) : null}
      <p className="mt-1 text-xs text-white">{model.headline}</p>
      <p className="mt-1 text-[11px] text-amber-100/85">
        Next: {model.nextAction}
      </p>
      <p className="mt-1 text-[11px] text-genesis-muted">
        Patch in repo:{" "}
        <span className={model.patchReady ? "text-emerald-200" : "text-rose-200"}>
          {model.patchReady ? "yes" : "no"}
        </span>
        {" · "}
        GitHub получил работу:{" "}
        <span className={model.sentToGithub ? "text-emerald-200" : "text-rose-200"}>
          {model.sentToGithub ? "да (есть Draft PR)" : "нет"}
        </span>
        {task.pr_url ? (
          <>
            {" · "}
            <button
              type="button"
              onClick={() => onGithubLinkClick(String(task.pr_url))}
              className="text-sky-300 hover:underline"
            >
              Open PR ↗
            </button>
          </>
        ) : null}
      </p>
      <ul className="mt-2 space-y-1 text-[11px]">
        {model.steps.map((s) => {
          const expandable = Boolean(s.explain);
          const open = openId === s.id;
          return (
            <li key={s.id} className={stepClass(s.state)}>
              <button
                type="button"
                className={`w-full text-left ${expandable ? "cursor-pointer hover:underline decoration-white/20" : "cursor-default"}`}
                onClick={() => {
                  if (!expandable) return;
                  setOpenId(open ? null : s.id);
                }}
                disabled={!expandable}
              >
                <span className="mr-1.5 font-mono">{mark(s.state)}</span>
                <span className="font-medium">{s.label}</span>
                <span className="ml-1.5 text-[10px] opacity-80">— {s.statusText}</span>
              </button>
              {s.detail ? (
                <span className="mt-0.5 block pl-5 text-[10px] opacity-75">{s.detail}</span>
              ) : null}
              {open && s.explain ? (
                <div className="mt-1 ml-5 rounded-md border border-amber-400/25 bg-amber-500/10 px-2 py-1.5 text-[10px] leading-relaxed text-amber-50/95">
                  <p className="font-semibold text-amber-100">
                    {s.state === "external" || s.state === "paused"
                      ? "Execution paused"
                      : "About this step"}
                  </p>
                  <p className="mt-0.5 whitespace-pre-wrap">{s.explain}</p>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
