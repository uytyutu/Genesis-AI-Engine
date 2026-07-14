import { useEffect, useRef, useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useCustomerAuth } from "../context/CustomerAuthContext";
import { useNavigation } from "../context/NavigationContext";
import { askVectorPublic } from "../lib/customerApi";
import {
  loadChat,
  saveChat,
  type ChatMessage,
} from "../lib/chatStore";
import { MessageBody } from "../lib/markdown";
import { ASSISTANT_NAME, PUBLIC_WELCOME } from "../lib/publicBrand";
import { getPriorVisitorId } from "../lib/visitorId";

function ChatBubble({ message }: { message: ChatMessage }) {
  return (
    <div className={`chat__row chat__row--${message.role}`}>
      <div className={`chat__bubble chat__bubble--${message.role}`}>
        <div className="chat__meta">
          <span>{message.role === "user" ? "Вы" : ASSISTANT_NAME}</span>
          <time>{message.at}</time>
        </div>
        {message.role === "assistant" ? (
          <MessageBody text={message.text} />
        ) : (
          <p className="chat__plain">{message.text}</p>
        )}
      </div>
    </div>
  );
}

type Props = {
  onBusyChange?: (busy: boolean) => void;
};

const STARTERS = [
  "Хочу открыть кофейню — с чего начать?",
  "Помоги придумать идею для бизнеса",
  "Что мы уже сделали в моих проектах?",
];

export function ChatPage({ onBusyChange }: Props) {
  const { settings } = useAppSettings();
  const { session: customerSession } = useCustomerAuth();
  const { chatPrefill, clearChatPrefill } = useNavigation();
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = loadChat();
    if (saved.length > 0) return saved;
    return [
      {
        id: "welcome",
        role: "assistant",
        text: customerSession?.headline
          ? `Здравствуйте! Я — ${ASSISTANT_NAME}, ваш цифровой сотрудник.\n\nРасскажите идею или вопрос — обсудим свободно. Когда понадобится хранить материалы, я сам предложу оформить это как проект.\n\n${customerSession.headline}`
          : PUBLIC_WELCOME,
        at: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ];
  });
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const hasUserMessages = messages.some((m) => m.role === "user");

  useEffect(() => {
    saveChat(messages.filter((m) => m.id !== "welcome" || hasUserMessages));
  }, [messages, hasUserMessages]);

  useEffect(() => {
    if (chatPrefill) {
      setInput(chatPrefill);
      clearChatPrefill();
    }
  }, [chatPrefill, clearChatPrefill]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send(text?: string) {
    const question = (text ?? input).trim();
    if (!question || sending) return;

    const visitorId =
      customerSession?.platformVisitorId?.trim() || getPriorVisitorId().trim();
    if (!visitorId) {
      setError("Сессия не готова. Выйдите и войдите снова.");
      return;
    }

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: question,
      at: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);
    setError(null);
    onBusyChange?.(true);

    try {
      const res = await askVectorPublic(settings, {
        question,
        visitor_id: visitorId,
        locale: settings.locale,
      });
      const answer = res.answer?.trim();
      if (!answer) {
        throw new Error("Пустой ответ — проверьте, что Virtus Core запущен.");
      }
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: answer,
          at: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } catch (e) {
      const msg =
        e instanceof Error
          ? e.message
          : `${ASSISTANT_NAME} временно недоступен. Запустите Virtus Core и попробуйте снова.`;
      setError(msg);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: `Извините, сейчас не могу ответить.\n\n${msg}`,
          at: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } finally {
      setSending(false);
      onBusyChange?.(false);
    }
  }

  return (
    <div className="page page--chat page--chat-customer">
      <header className="page__header">
        <h1>{ASSISTANT_NAME}</h1>
        <p>Ваш цифровой сотрудник — спрашивайте как в обычном чате</p>
      </header>

      <div className="chat chat--customer">
        <div className="chat__thread" aria-live="polite">
          {messages.map((m) => (
            <ChatBubble key={m.id} message={m} />
          ))}
          {sending ? (
            <p className="chat__typing">{ASSISTANT_NAME} печатает…</p>
          ) : null}
          <div ref={endRef} />
        </div>

        {!hasUserMessages ? (
          <div className="chat-starters">
            {STARTERS.map((s) => (
              <button
                key={s}
                type="button"
                className="btn btn--ghost chat-starter"
                onClick={() => void send(s)}
                disabled={sending}
              >
                {s}
              </button>
            ))}
          </div>
        ) : null}

        {error ? <p className="banner banner--warn">{error}</p> : null}

        <form
          className="chat__composer chat__composer--simple"
          onSubmit={(e) => {
            e.preventDefault();
            void send();
          }}
        >
          <input ref={fileRef} type="file" multiple hidden />
          <button
            type="button"
            className="btn btn--ghost chat__icon-btn"
            title="Прикрепить файл"
            onClick={() => fileRef.current?.click()}
            disabled={sending}
          >
            📎
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Сообщение для ${ASSISTANT_NAME}…`}
            maxLength={2000}
            disabled={sending}
          />
          <button
            type="button"
            className="btn btn--ghost chat__icon-btn"
            title="Голосовой ввод — скоро"
            disabled
          >
            🎤
          </button>
          <button type="submit" className="btn btn--primary" disabled={sending || !input.trim()}>
            ➡
          </button>
        </form>
      </div>
    </div>
  );
}
