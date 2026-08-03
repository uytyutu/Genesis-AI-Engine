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
  /** Public /site — return to landing welcome */
  onGoHome?: () => void;
  /** Storefront Vector chat — aurora chrome */
  storefrontStyle?: boolean;
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
  onGoHome,
  storefrontStyle = false,
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
                  className={`w-full rounded-lg py-2 text-left text-sm transition ${
                    storefrontStyle ? "pr-9 pl-2" : "px-2"
                  } ${
                    active
                      ? storefrontStyle
                        ? "bg-sky-500/20 text-white"
                        : "bg-genesis-accent/20 text-white"
                      : "text-genesis-text hover:bg-white/5"
                  }`}
                >
                  <span className="line-clamp-1 font-medium">
                    {s.title || (storefrontStyle ? "Новый чат" : "Новое поручение")}
                  </span>
                  {s.preview ? (
                    <span className="line-clamp-1 text-[11px] text-genesis-muted">
                      {s.preview}
                    </span>
                  ) : null}
                </button>
                <div
                  className={`absolute right-1 top-1 gap-0.5 ${
                    storefrontStyle ? "flex" : "hidden group-hover:flex"
                  }`}
                >
                  {!storefrontStyle ? (
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
                  ) : null}
                  <button
                    type="button"
                    title="Удалить"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(s.session_id);
                    }}
                    className="flex h-6 w-6 items-center justify-center rounded-md text-sm text-rose-300/90 hover:bg-rose-500/20 hover:text-rose-200"
                  >
                    ×
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
                  aria-label="Закрыть историю"
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
                  className={`fixed inset-y-0 left-0 z-[60] flex w-[min(85vw,18rem)] flex-col overflow-hidden border-r border-white/10 shadow-2xl md:hidden ${
                    storefrontStyle ? "bg-[#0c0c14]/98 backdrop-blur-xl" : "bg-genesis-panel"
                  }`}
                  aria-label="История чатов"
                >
                  <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
                    <p className="text-sm font-semibold text-white">
                      {storefrontStyle ? "История" : "Меню"}
                    </p>
                    <button
                      type="button"
                      onClick={closeSidebar}
                      className="flex h-8 w-8 items-center justify-center rounded-lg text-genesis-muted transition hover:bg-white/5 hover:text-white"
                      aria-label="Закрыть меню"
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
                    onGoHome={storefrontStyle ? undefined : onGoHome}
                    storefrontStyle={storefrontStyle}
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
          {sidebarOpen ? "Скрыть историю" : "История"}
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
              aria-label="История поручений"
            >
              <SidebarNav
                sessions={sessions}
                activeSessionId={activeSessionId}
                onNewChat={onNewChat}
                onSelect={onSelect}
                onDelete={onDelete}
                onPin={onPin}
                storefrontStyle={storefrontStyle}
                renderGroup={renderGroup}
              />
            </motion.aside>
          ) : null}
        </AnimatePresence>
      ) : (
        overlayDrawer
      )}

      <aside
        className={`${
          overlayOnly && !storefrontStyle
            ? "hidden"
            : "hidden shrink-0 flex-col overflow-hidden border-r border-white/10 md:flex md:w-52 lg:w-56"
        } ${storefrontStyle ? "bg-black/25" : "rounded-2xl border border-white/10 bg-genesis-panel/50"}`}
        aria-label="История чатов"
      >
        <SidebarNav
          sessions={sessions}
          activeSessionId={activeSessionId}
          onNewChat={onNewChat}
          onSelect={onSelect}
          onDelete={onDelete}
          onPin={onPin}
          onGoHome={storefrontStyle ? undefined : onGoHome}
          storefrontStyle={storefrontStyle}
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
  onGoHome,
  storefrontStyle = false,
  renderGroup,
}: {
  sessions: ChatSessionMeta[];
  activeSessionId: string | null;
  onNewChat: () => void;
  onSelect: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
  onPin: (sessionId: string, pinned: boolean) => void;
  onGoHome?: () => void;
  storefrontStyle?: boolean;
  renderGroup: (key: DateGroup) => ReactNode;
}) {
  const emptyHint = storefrontStyle
    ? "Пока нет чатов.\nОпишите нишу — Vector подскажет пакет."
    : "Пока нет сохранённых поручений.\nПоручите Vector первую задачу.";
  return (
    <>
      {onGoHome ? (
        <div className="space-y-1 border-b border-white/5 p-2">
          <button
            type="button"
            onClick={onGoHome}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-white transition hover:bg-white/5"
          >
            <span aria-hidden>🏠</span>
            На главную
          </button>
          <button
            type="button"
            onClick={onNewChat}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm text-genesis-text transition hover:bg-white/5"
          >
            <span aria-hidden>💬</span>
            Новое поручение
          </button>
        </div>
      ) : null}
      <div className={`border-b border-white/5 p-3 ${onGoHome ? "hidden" : ""}`}>
        <motion.button
          type="button"
          onClick={onNewChat}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          transition={springs.snappy}
          className={`flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold text-white ${
            storefrontStyle
              ? "bg-sky-500/30 hover:bg-sky-500/40"
              : "bg-genesis-accent/25 hover:bg-genesis-accent/35"
          }`}
        >
          <span className="text-lg leading-none">+</span>
          {storefrontStyle ? "Новый чат" : "Новое поручение"}
        </motion.button>
      </div>
      {onGoHome ? (
        <p className="px-3 pt-2 text-[10px] font-semibold uppercase tracking-wider text-genesis-muted">
          История
        </p>
      ) : null}
      <nav className="min-h-0 flex-1 overflow-y-auto p-2">
        {sessions.length === 0 ? (
          <p className="whitespace-pre-line px-2 py-4 text-center text-xs text-genesis-muted">
            {emptyHint}
          </p>
        ) : (
          (["pinned", "today", "yesterday", "week", "older"] as DateGroup[]).map(renderGroup)
        )}
      </nav>
    </>
  );
}
