import { useEffect, useRef, useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { askAssistant } from "../lib/endpoints";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

const CHAT_KEY = "genesis.client.chat.v1";

function loadChat(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(CHAT_KEY);
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

function saveChat(messages: ChatMessage[]) {
  localStorage.setItem(CHAT_KEY, JSON.stringify(messages.slice(-40)));
}

export function ChatPage() {
  const { settings } = useAppSettings();
  const [messages, setMessages] = useState<ChatMessage[]>(loadChat);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    saveChat(messages);
  }, [messages]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send() {
    const question = input.trim();
    if (!question || sending) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: question,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const res = await askAssistant(settings, question);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: res.answer,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Assistant unavailable");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="page page--chat">
      <header className="page__header">
        <h1>Assistant</h1>
        <p>Live connection to <code>/api/assistant/ask</code></p>
      </header>

      <div className="chat">
        <div className="chat__thread" aria-live="polite">
          {messages.length === 0 ? (
            <p className="chat__empty">
              Ask Genesis about your company, queue, or next step.
            </p>
          ) : (
            messages.map((m) => (
              <div key={m.id} className={`chat__bubble chat__bubble--${m.role}`}>
                {m.text}
              </div>
            ))
          )}
          {sending ? <p className="chat__typing">Genesis is thinking…</p> : null}
          <div ref={endRef} />
        </div>

        {error ? <p className="banner banner--warn">{error}</p> : null}

        <form
          className="chat__composer"
          onSubmit={(e) => {
            e.preventDefault();
            void send();
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Genesis…"
            maxLength={500}
            disabled={sending}
          />
          <button type="submit" className="btn btn--primary" disabled={sending}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
