"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Message = { role: "user" | "assistant"; text: string };

const STARTERS = ["Что происходит?", "Что мне делать дальше?", "Какой прогресс проекта?"];

export function AssistantPanel({ embedded = false }: { embedded?: boolean }) {
  const [open, setOpen] = useState(true);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "Я помощник Genesis. Спросите о статусе, задачах или следующих шагах.",
    },
  ]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollDown = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollDown();
  }, [messages, scrollDown]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || busy) return;
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/assistant/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.answer }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Не могу связаться с Genesis. Запустите Launcher." },
      ]);
    } finally {
      setBusy(false);
    }
  }

  if (!open && !embedded) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 rounded-full border border-genesis-accent bg-genesis-panel px-5 py-3 text-sm font-medium shadow-lg hover:bg-genesis-accent/20"
      >
        💬 Помощник Genesis
      </button>
    );
  }

  return (
    <aside
      className={`flex w-full flex-col rounded-xl border border-genesis-border bg-genesis-panel ${
        embedded ? "min-h-[480px]" : "h-[calc(100vh-2rem)] lg:sticky lg:top-4 lg:max-h-[calc(100vh-3rem)] lg:w-80"
      }`}
    >
      <div className="flex items-center justify-between border-b border-genesis-border px-4 py-3">
        <div>
          <p className="text-sm font-semibold">Помощник Genesis</p>
          <p className="text-xs text-genesis-muted">не ChatGPT — знает вашу систему</p>
        </div>
        {!embedded && (
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="text-genesis-muted hover:text-white"
            aria-label="Свернуть"
          >
            ✕
          </button>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
        {messages.map((msg, i) => (
          <div
            key={`${msg.role}-${i}`}
            className={`rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
              msg.role === "user"
                ? "ml-6 bg-genesis-accent/30 text-right"
                : "mr-4 bg-genesis-bg"
            }`}
          >
            {msg.text}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-genesis-border px-3 py-2">
        <div className="mb-2 flex flex-wrap gap-1">
          {STARTERS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => send(s)}
              className="rounded-full border border-genesis-border px-2 py-0.5 text-xs text-genesis-muted hover:border-genesis-accent"
            >
              {s}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Спросите Genesis…"
            className="flex-1 rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm outline-none focus:border-genesis-accent"
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg bg-genesis-accent px-3 py-2 text-sm font-medium disabled:opacity-50"
          >
            →
          </button>
        </form>
      </div>
    </aside>
  );
}
