import { useEffect, useMemo, useRef, useState } from "react";
import type { NavId } from "./Sidebar";
import { loadChat, searchChat } from "../lib/chatStore";
import { useI18n } from "../i18n/I18nProvider";
import { ASSISTANT_NAME } from "../lib/publicBrand";

export type CommandItem = {
  id: string;
  label: string;
  hint?: string;
  keywords?: string;
  action: () => void;
};

type CommandPaletteProps = {
  open: boolean;
  onClose: () => void;
  onNavigate: (id: NavId) => void;
  onDisconnect: () => void;
  onRefresh: () => void;
  onOpenChat: (prefill?: string) => void;
};

export function CommandPalette({
  open,
  onClose,
  onNavigate,
  onDisconnect,
  onRefresh,
  onOpenChat,
}: CommandPaletteProps) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const chatHits = useMemo(() => {
    const q = query.trim();
    if (q.length < 2) return [];
    return searchChat(loadChat(), q).slice(0, 5);
  }, [query]);

  const commands = useMemo<CommandItem[]>(
    () => [
      {
        id: "home",
        label: t("palette.openHome"),
        hint: t("nav.home.hint"),
        keywords: "dashboard welcome",
        action: () => onNavigate("home"),
      },
      {
        id: "chat",
        label: t("palette.openChat"),
        hint: t("nav.chat.hint"),
        keywords: "assistant",
        action: () => onOpenChat(),
      },
      {
        id: "chat-focus",
        label: t("palette.askFocus"),
        hint: "Quick command",
        keywords: "focus priority",
        action: () => onOpenChat("/focus"),
      },
      {
        id: "studio",
        label: t("palette.openStudio"),
        hint: t("nav.studio.hint"),
        keywords: "development cursor handoff",
        action: () => onNavigate("studio"),
      },
      {
        id: "projects",
        label: t("palette.openProjects"),
        hint: t("nav.projects.hint"),
        keywords: "factory",
        action: () => onNavigate("projects"),
      },
      {
        id: "settings",
        label: t("palette.openSettings"),
        hint: t("nav.settings.hint"),
        keywords: "preferences",
        action: () => onNavigate("settings"),
      },
      {
        id: "refresh",
        label: t("palette.refresh"),
        hint: t("nav.home.hint"),
        keywords: "reconnect railway restart",
        action: () => {
          onRefresh();
          onNavigate("home");
        },
      },
      {
        id: "disconnect",
        label: t("palette.disconnect"),
        hint: t("session.disconnect"),
        keywords: "logout",
        action: onDisconnect,
      },
      ...chatHits.map((m, i) => ({
        id: `chat-hit-${i}`,
        label: m.text.slice(0, 60),
        hint: `Chat · ${m.at}`,
        keywords: m.text,
        action: () => onOpenChat(m.text),
      })),
    ],
    [onNavigate, onDisconnect, onRefresh, onOpenChat, chatHits, t],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter(
      (c) =>
        c.label.toLowerCase().includes(q) ||
        c.hint?.toLowerCase().includes(q) ||
        c.keywords?.toLowerCase().includes(q),
    );
  }, [commands, query]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setActive(0);
    requestAnimationFrame(() => inputRef.current?.focus());
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive((i) => Math.min(i + 1, Math.max(filtered.length - 1, 0)));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive((i) => Math.max(i - 1, 0));
      }
      if (e.key === "Enter" && filtered[active]) {
        e.preventDefault();
        filtered[active].action();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, filtered, active, onClose]);

  if (!open) return null;

  return (
    <div className="palette-backdrop" onClick={onClose} role="presentation">
      <div
        className="palette"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          className="palette__input"
          placeholder={t("palette.placeholder")}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setActive(0);
          }}
        />
        <ul className="palette__list" role="listbox">
          {filtered.length === 0 ? (
            <li className="palette__empty">Ничего не найдено</li>
          ) : (
            filtered.map((cmd, i) => (
              <li key={cmd.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={i === active}
                  className={`palette__item${i === active ? " is-active" : ""}`}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => {
                    cmd.action();
                    onClose();
                  }}
                >
                  <span className="palette__label">{cmd.label}</span>
                  {cmd.hint ? (
                    <span className="palette__hint">{cmd.hint}</span>
                  ) : null}
                </button>
              </li>
            ))
          )}
        </ul>
        <p className="palette__footer">
          <kbd>Ctrl</kbd>+<kbd>K</kbd> · сердце {ASSISTANT_NAME}
        </p>
      </div>
    </div>
  );
}

export function useCommandPaletteShortcut(onOpen: () => void) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpen();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onOpen]);
}
