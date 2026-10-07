"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [thread, setThread] = useState<{
    senderLabel: string;
    recipientLabel: string;
    blocked: boolean;
  } | null>(null);
  const [me, setMe] = useState<"anon" | "recipient">("recipient");
  const [messages, setMessages] = useState<
    { id: string; side: string; body: string; createdAt: string }[]
  >([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const r = await fetch(`/api/chat/${id}`);
    if (r.status === 401) {
      router.replace(`/auth/login?next=/chat/${id}`);
      return;
    }
    const d = await r.json();
    if (!r.ok) {
      setError(d.error || "Error");
      return;
    }
    setThread(d.thread);
    setMessages(d.messages);
    setMe(d.me);
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function send() {
    const r = await fetch(`/api/chat/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const d = await r.json();
    if (!r.ok) {
      setError(d.error || "Failed");
      return;
    }
    setText("");
    await load();
  }

  async function report() {
    await fetch("/api/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        targetType: "gift",
        targetId: id,
        reason: "User reported anonymous chat",
      }),
    });
    alert("Report sent");
  }

  return (
    <main className="anim-in flex min-h-[70vh] flex-col">
      <header className="anon-card mb-4 p-4">
        <p className="text-sm font-semibold">
          {thread?.senderLabel} ↔ {thread?.recipientLabel}
        </p>
        <p className="text-xs anon-muted">No real names. You are {me === "anon" ? thread?.senderLabel : thread?.recipientLabel}</p>
        <div className="mt-3 flex gap-2">
          <button type="button" className="anon-btn anon-btn-ghost !py-1 text-xs" onClick={report}>
            🚩 Report
          </button>
        </div>
      </header>
      <div className="flex-1 space-y-2">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${
              m.side === me ? "ml-auto bg-violet-500/30" : "bg-white/5"
            }`}
          >
            {m.body}
          </div>
        ))}
      </div>
      {error && <p className="mt-2 text-sm text-rose-300">{error}</p>}
      {!thread?.blocked && (
        <div className="mt-4 flex gap-2">
          <input
            className="anon-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Message…"
          />
          <button type="button" className="anon-btn anon-btn-primary" onClick={send}>
            Send
          </button>
        </div>
      )}
    </main>
  );
}
