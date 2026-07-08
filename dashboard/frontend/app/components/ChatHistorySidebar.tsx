"use client";

import { useMemo } from "react";
import {
  type ChatSessionMeta,
  type DateGroup,
  groupSessionsByDate,
} from "../lib/chatSessions";

const GROUP_LABELS: Record<DateGroup, string> = {
  pinned: "Закреплённые",
  today: "Сегодня",
  yesterday: "Вчера",
  week: "На этой неделе",
  older: "Раньше",
};

type Props = {
  sessions: ChatSessionMeta[];
  activeSessionId: string | null;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  onNewChat: () => void;
  onSelect: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
  onPin: (sessionId: string, pinned: boolean) => void;
};

export function ChatHistorySidebar({
  sessions,
  activeSessionId,
  sidebarOpen,
  onToggleSidebar,
  onNewChat,
  onSelect,
  onDelete,
  onPin,
}: Props) {
  const grouped = useMemo(() => groupSessionsByDate(sessions), [sessions]);

  const renderGroup = (key: DateGroup) => {
    const items = grouped[key];
    if (!items.length) return null;
    return (
      <div key={key} className="mb-3">
        <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-genesis-muted">
          {GROUP_LABELS[key]}
        </p>
        <ul className="space-y-0.5">
          {items.map((s) => {
            const active = s.session_id === activeSessionId;
            return (
              <li key={s.session_id} className="group relative">
                <button
                  type="button"
                  onClick={() => onSelect(s.session_id)}
                  className={`w-full rounded-lg px-2 py-2 text-left text-sm transition ${
                    active
                      ? "bg-genesis-accent/20 text-white"
                      : "text-genesis-text hover:bg-white/5"
                  }`}
                >
                  <span className="line-clamp-1 font-medium">{s.title || "Новый чат"}</span>
                  {s.preview ? (
                    <span className="line-clamp-1 text-[11px] text-genesis-muted">
                      {s.preview}
                    </span>
                  ) : null}
                </button>
                <div className="absolute right-1 top-1 hidden gap-0.5 group-hover:flex">
                  <button
                    type="button"
                    title={s.pinned ? "Открепить" : "Закрепить"}
                    onClick={(e) => {
                      e.stopPropagation();
                      onPin(s.session_id, !s.pinned);
                    }}
                    className="rounded px-1 text-[10px] text-genesis-muted hover:bg-white/10 hover:text-white"
                  >
                    {s.pinned ? "📌" : "📍"}
                  </button>
                  <button
                    type="button"
                    title="Удалить"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(s.session_id);
                    }}
                    className="rounded px-1 text-[10px] text-rose-300/80 hover:bg-rose-500/20"
                  >
                    ✕
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    );
  };

  return (
    <>
      <button
        type="button"
        onClick={onToggleSidebar}
        className="mb-2 flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm text-genesis-muted transition hover:bg-white/5 hover:text-white md:hidden"
        aria-expanded={sidebarOpen}
      >
        {sidebarOpen ? "Скрыть историю" : "История чатов"}
      </button>

      <aside
        className={`shrink-0 flex-col overflow-hidden rounded-2xl border border-white/10 bg-genesis-panel/50 transition-all duration-300 ${
          sidebarOpen
            ? "flex w-full md:w-56 lg:w-64"
            : "hidden md:flex md:w-56 lg:w-64"
        }`}
        aria-label="История чатов"
      >
        <div className="border-b border-white/5 p-3">
          <button
            type="button"
            onClick={onNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-genesis-accent/25 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-genesis-accent/35"
          >
            <span className="text-lg leading-none">+</span>
            Новый чат
          </button>
        </div>
        <nav className="min-h-0 flex-1 overflow-y-auto p-2">
          {sessions.length === 0 ? (
            <p className="px-2 py-4 text-center text-xs text-genesis-muted">
              Пока нет сохранённых чатов.
              <br />
              Начните новый разговор.
            </p>
          ) : (
            (["pinned", "today", "yesterday", "week", "older"] as DateGroup[]).map(
              renderGroup,
            )
          )}
        </nav>
      </aside>
    </>
  );
}
