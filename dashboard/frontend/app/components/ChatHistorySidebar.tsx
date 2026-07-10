"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import {
  type ChatSessionMeta,
  type DateGroup,
  groupSessionsByDate,
} from "../lib/chatSessions";
import { springs } from "../lib/motion";

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
  onCloseSidebar?: () => void;
  onNewChat: () => void;
  onSelect: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
  onPin: (sessionId: string, pinned: boolean) => void;
  /** Hide standalone mobile history bar — toggle lives in chat header */
  hideMobileToggle?: boolean;
  /** Drawer only — no persistent desktop column (public /site) */
  overlayOnly?: boolean;
};

export function ChatHistorySidebar({
  sessions,
  activeSessionId,
  sidebarOpen,
  onToggleSidebar,
  onCloseSidebar,
  onNewChat,
  onSelect,
  onDelete,
  onPin,
  hideMobileToggle = false,
  overlayOnly = false,
}: Props) {
  const grouped = useMemo(() => groupSessionsByDate(sessions), [sessions]);
  const reduce = useReducedMotion();
  const [portalReady, setPortalReady] = useState(false);
  const closeSidebar = onCloseSidebar ?? onToggleSidebar;

  useEffect(() => {
    setPortalReady(true);
  }, []);

  useEffect(() => {
    if (!overlayOnly || !sidebarOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [overlayOnly, sidebarOpen]);

  const handleNewChat = () => {
    onNewChat();
    if (overlayOnly) closeSidebar();
  };

  const handleSelect = (sessionId: string) => {
    onSelect(sessionId);
    if (overlayOnly) closeSidebar();
  };

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
                  onClick={() => handleSelect(s.session_id)}
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

  const overlayDrawer =
    overlayOnly && portalReady
      ? createPortal(
          <AnimatePresence>
            {sidebarOpen ? (
              <>
                <motion.button
                  key="chat-history-backdrop"
                  type="button"
                  aria-label="Закрыть историю чатов"
                  initial={reduce ? false : { opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={reduce ? undefined : { opacity: 0 }}
                  transition={springs.gentle}
                  className="fixed inset-0 z-[55] bg-black/60 backdrop-blur-[2px] md:hidden"
                  onClick={closeSidebar}
                />
                <motion.aside
                  key="chat-history-overlay"
                  initial={reduce ? false : { x: "-100%" }}
                  animate={{ x: 0 }}
                  exit={reduce ? undefined : { x: "-100%" }}
                  transition={springs.gentle}
                  className="fixed inset-y-0 left-0 z-[60] flex w-[min(85vw,18rem)] flex-col overflow-hidden border-r border-white/10 bg-genesis-panel shadow-2xl md:hidden"
                  aria-label="История чатов"
                >
                  <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
                    <p className="text-sm font-semibold text-white">История чатов</p>
                    <button
                      type="button"
                      onClick={closeSidebar}
                      className="flex h-8 w-8 items-center justify-center rounded-lg text-genesis-muted transition hover:bg-white/5 hover:text-white"
                      aria-label="Закрыть"
                    >
                      ✕
                    </button>
                  </div>
                  <SidebarNav
                    sessions={sessions}
                    activeSessionId={activeSessionId}
                    onNewChat={handleNewChat}
                    onSelect={handleSelect}
                    onDelete={onDelete}
                    onPin={onPin}
                    renderGroup={renderGroup}
                  />
                </motion.aside>
              </>
            ) : null}
          </AnimatePresence>,
          document.body,
        )
      : null;

  return (
    <>
      {!hideMobileToggle ? (
        <button
          type="button"
          onClick={onToggleSidebar}
          className="mb-2 flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm text-genesis-muted transition hover:bg-white/5 hover:text-white md:hidden"
          aria-expanded={sidebarOpen}
        >
          {sidebarOpen ? "Скрыть историю" : "История чатов"}
        </button>
      ) : null}

      {!overlayOnly ? (
        <AnimatePresence>
          {sidebarOpen ? (
            <motion.aside
              key="chat-history-mobile"
              initial={reduce ? false : { opacity: 0, height: 0, y: -8 }}
              animate={{ opacity: 1, height: "auto", y: 0 }}
              exit={reduce ? undefined : { opacity: 0, height: 0, y: -8 }}
              transition={springs.gentle}
              className="mb-2 flex w-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-genesis-panel/50 md:hidden"
              aria-label="История чатов"
            >
              <SidebarNav
                sessions={sessions}
                activeSessionId={activeSessionId}
                onNewChat={onNewChat}
                onSelect={onSelect}
                onDelete={onDelete}
                onPin={onPin}
                renderGroup={renderGroup}
              />
            </motion.aside>
          ) : null}
        </AnimatePresence>
      ) : (
        overlayDrawer
      )}

      <aside
        className={`${overlayOnly ? "hidden" : "hidden shrink-0 flex-col overflow-hidden rounded-2xl border border-white/10 bg-genesis-panel/50 md:flex md:w-56 lg:w-64"}`}
        aria-label="История чатов"
      >
        <SidebarNav
          sessions={sessions}
          activeSessionId={activeSessionId}
          onNewChat={onNewChat}
          onSelect={onSelect}
          onDelete={onDelete}
          onPin={onPin}
          renderGroup={renderGroup}
        />
      </aside>
    </>
  );
}

function SidebarNav({
  sessions,
  activeSessionId,
  onNewChat,
  onSelect,
  onDelete,
  onPin,
  renderGroup,
}: {
  sessions: ChatSessionMeta[];
  activeSessionId: string | null;
  onNewChat: () => void;
  onSelect: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
  onPin: (sessionId: string, pinned: boolean) => void;
  renderGroup: (key: DateGroup) => ReactNode;
}) {
  return (
    <>
      <div className="border-b border-white/5 p-3">
        <motion.button
          type="button"
          onClick={onNewChat}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          transition={springs.snappy}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-genesis-accent/25 px-3 py-2.5 text-sm font-semibold text-white hover:bg-genesis-accent/35"
        >
          <span className="text-lg leading-none">+</span>
          Новый чат
        </motion.button>
      </div>
      <nav className="min-h-0 flex-1 overflow-y-auto p-2">
        {sessions.length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-genesis-muted">
            Пока нет сохранённых чатов.
            <br />
            Начните новый разговор.
          </p>
        ) : (
          (["pinned", "today", "yesterday", "week", "older"] as DateGroup[]).map(renderGroup)
        )}
      </nav>
    </>
  );
}
