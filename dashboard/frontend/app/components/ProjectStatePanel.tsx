"use client";

import { useCallback, useEffect, useState } from "react";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import {
  getLiveProjectState,
  PROJECT_STATE_EVENT,
  applyProjectStateAuthority,
  type LiveProjectState,
} from "../lib/projectStateEngine";
import {
  PROJECT_CLAIM_EVENT,
  getProjectClaimDraft,
  isProjectClaimed,
  type ProjectClaimDraft,
} from "../lib/projectIdentity";
import { fetchProjectPlatform } from "../lib/projectApi";
import { getVisitorId } from "../lib/visitorId";
import { Card } from "./ui";

type Props = {
  compact?: boolean;
};

function dash(value: string | null | undefined): string {
  return value?.trim() ? value.trim() : "—";
}

function UnclaimedCard({ compact }: { compact?: boolean }) {
  return (
    <Card
      padding={compact ? "md" : "lg"}
      hover={false}
      className="flex h-full min-h-0 flex-col border-dashed border-white/12 bg-genesis-panel/40"
    >
      <p className="text-[10px] font-bold tracking-[0.2em] text-genesis-accent uppercase">
        Ваша компания
      </p>
      <h2 className="mt-2 text-lg font-bold text-white sm:text-xl">Начинаем с нуля</h2>
      <p className="mt-2 text-sm leading-relaxed text-genesis-muted">
        Это ваш кабинет. Здесь будет расти цифровая компания — не чужой проект.
      </p>

      <div className="mt-4 space-y-2 rounded-xl border border-white/8 bg-white/5 px-3 py-3 text-sm">
        <div className="flex justify-between gap-3">
          <span className="text-genesis-muted">Название</span>
          <span className="text-right text-white">—</span>
        </div>
        <div className="flex justify-between gap-3">
          <span className="text-genesis-muted">Отрасль</span>
          <span className="text-right text-white">—</span>
        </div>
        <div className="flex justify-between gap-3">
          <span className="text-genesis-muted">Цель</span>
          <span className="text-right text-white">—</span>
        </div>
        <div className="mt-2 border-t border-white/8 pt-2 text-xs text-genesis-muted">
          Статус: ждём рассказ о вашей компании
        </div>
      </div>

      <p className="mt-4 text-sm text-genesis-muted">
        Напишите в чат — {ASSISTANT_NAME} запишет вашу компанию сюда.
      </p>
    </Card>
  );
}

function ClaimedIdentityCard({
  draft,
  compact,
}: {
  draft: ProjectClaimDraft;
  compact?: boolean;
}) {
  const title = draft.companyName || "Ваша компания";

  return (
    <Card
      glow
      padding={compact ? "md" : "lg"}
      hover={false}
      className="flex h-full min-h-0 flex-col border-genesis-accent/20"
    >
      <p className="text-[10px] font-bold tracking-[0.2em] text-genesis-accent uppercase">
        Ваша компания
      </p>
      <h2 className="mt-2 text-lg font-bold text-white sm:text-xl">{title}</h2>

      <div className="mt-4 space-y-2 rounded-xl border border-white/8 bg-white/5 px-3 py-3 text-sm">
        <div className="flex justify-between gap-3">
          <span className="text-genesis-muted">Отрасль</span>
          <span className="text-right text-white">{dash(draft.industry)}</span>
        </div>
        <div className="flex justify-between gap-3">
          <span className="text-genesis-muted">Город</span>
          <span className="text-right text-white">{dash(draft.location)}</span>
        </div>
        <div className="flex justify-between gap-3">
          <span className="text-genesis-muted">Цель</span>
          <span className="text-right text-white">{dash(draft.goal)}</span>
        </div>
        <div className="mt-2 border-t border-white/8 pt-2 text-xs font-medium text-emerald-300">
          {draft.statusLabel}
        </div>
      </div>

      <p className="mt-4 text-sm text-genesis-muted">
        {ASSISTANT_NAME} продолжит уточнять детали в чате.
      </p>
    </Card>
  );
}

export function ProjectStatePanel({ compact }: Props) {
  const [claimed, setClaimed] = useState(false);
  const [draft, setDraft] = useState<ProjectClaimDraft>(() => getProjectClaimDraft());
  const [live, setLive] = useState<LiveProjectState | null>(null);
  const [backendTitle, setBackendTitle] = useState<string | null>(null);

  const reloadBackend = useCallback(async () => {
    if (!isProjectClaimed()) return;
    const data = await fetchProjectPlatform(getVisitorId("public"));
    if (data.project?.title) {
      setBackendTitle(data.project.title);
    }
    applyProjectStateAuthority(data);
  }, []);

  useEffect(() => {
    setClaimed(isProjectClaimed());
    setDraft(getProjectClaimDraft());
    setLive(getLiveProjectState());
    if (isProjectClaimed()) {
      void reloadBackend();
    }

    const onLive = (e: Event) => {
      const detail = (e as CustomEvent<LiveProjectState | null>).detail;
      if (detail !== undefined) {
        setLive(detail);
        return;
      }
      setLive(getLiveProjectState());
    };
    const onClaim = (e: Event) => {
      const detail = (e as CustomEvent<ProjectClaimDraft | null>).detail;
      setClaimed(isProjectClaimed());
      if (detail) {
        setDraft(detail);
      } else {
        setDraft(getProjectClaimDraft());
      }
      void reloadBackend();
    };
    const onBackend = () => void reloadBackend();

    window.addEventListener(PROJECT_STATE_EVENT, onLive);
    window.addEventListener(PROJECT_CLAIM_EVENT, onClaim);
    window.addEventListener("genesis:project-updated", onBackend);
    return () => {
      window.removeEventListener(PROJECT_STATE_EVENT, onLive);
      window.removeEventListener(PROJECT_CLAIM_EVENT, onClaim);
      window.removeEventListener("genesis:project-updated", onBackend);
    };
  }, [reloadBackend]);

  if (!claimed) {
    return <UnclaimedCard compact={compact} />;
  }

  if (!live?.active) {
    return <ClaimedIdentityCard draft={draft} compact={compact} />;
  }

  const title =
    draft.companyName ||
    backendTitle ||
    live.title;

  const mergedItems = live.items.map((item) => {
    if (item.id === "company" && draft.companyName && item.status !== "done") {
      return { ...item, status: "done" as const, value: draft.companyName };
    }
    if (item.id === "goal" && draft.goal && !item.value) {
      return { ...item, status: item.status === "pending" ? ("done" as const) : item.status, value: draft.goal };
    }
    return item;
  });

  const barWidth = Math.max(4, live.percent);

  return (
    <Card
      glow
      padding={compact ? "md" : "lg"}
      hover={false}
      className="flex h-full min-h-0 flex-col border-genesis-accent/20"
    >
      <p className="text-[10px] font-bold tracking-[0.2em] text-genesis-accent uppercase">
        Ваша компания
      </p>
      <h2 className="mt-2 text-lg font-bold text-white sm:text-xl">{title}</h2>

      <div className="mt-3 flex items-center justify-between gap-2 text-xs">
        <span className="text-genesis-muted">Статус</span>
        <span className="font-medium text-white">{live.statusLabel}</span>
      </div>

      <div className="mt-3">
        <div className="mb-1 flex justify-between text-xs">
          <span className="text-genesis-muted">Прогресс</span>
          <span className="font-semibold text-genesis-accent">{live.percent}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-gradient-to-r from-genesis-accent to-emerald-500 transition-all duration-300"
            style={{ width: `${barWidth}%` }}
          />
        </div>
      </div>

      {live.vectorNow.length > 0 && (
        <div className="mt-4 rounded-xl border border-white/8 bg-white/5 px-3 py-2.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-genesis-muted">
            {ASSISTANT_NAME} сейчас
          </p>
          <ul className="mt-2 space-y-1">
            {live.vectorNow.map((line) => (
              <li key={line} className="text-sm text-white">
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      <ul className="mt-4 min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1">
        {mergedItems.map((item) => (
          <li
            key={item.id}
            className="flex items-start justify-between gap-2 rounded-lg bg-white/5 px-2.5 py-1.5 text-sm"
          >
            <span
              className={
                item.status === "done"
                  ? "text-emerald-300"
                  : item.status === "active"
                    ? "text-white font-medium"
                    : "text-genesis-muted"
              }
            >
              {item.status === "done" ? "✓" : item.status === "active" ? "⏳" : "○"} {item.label}
            </span>
            {item.value ? (
              <span className="shrink-0 text-right text-xs text-genesis-accent">{item.value}</span>
            ) : null}
          </li>
        ))}
      </ul>
    </Card>
  );
}
