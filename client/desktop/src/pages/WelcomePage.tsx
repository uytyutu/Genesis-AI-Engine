import { useEffect, useState } from "react";
import { useCustomerAuth } from "../context/CustomerAuthContext";
import { useNavigation } from "../context/NavigationContext";
import { GenesisMark } from "../components/GenesisMark";
import { ASSISTANT_NAME } from "../lib/publicBrand";

export function WelcomePage() {
  const { session, welcome, busy, error, startWelcome, answerWizard } =
    useCustomerAuth();
  const { openChat } = useNavigation();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<
    { role: "assistant" | "user"; text: string }[]
  >([]);

  useEffect(() => {
    if (!welcome?.message || welcome.phase !== "greeting") return;
    setMessages([{ role: "assistant", text: welcome.message }]);
  }, [welcome?.message, welcome?.phase]);

  useEffect(() => {
    if (!welcome?.wizard_question || welcome.phase !== "wizard") return;
    const q = welcome.wizard_question;
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last?.text === q) return prev;
      return [...prev, { role: "assistant" as const, text: q }];
    });
  }, [welcome?.wizard_question, welcome?.phase]);

  useEffect(() => {
    if (welcome?.phase === "personalized" && welcome.message) {
      const msg = welcome.message;
      setMessages((prev) => [
        ...prev,
        { role: "assistant" as const, text: msg },
      ]);
    }
  }, [welcome?.phase, welcome?.message]);

  async function onContinue() {
    if (welcome?.phase === "greeting") {
      await startWelcome();
      return;
    }
    if (welcome?.phase === "wizard") {
      if (!input.trim()) return;
      const text = input.trim();
      setMessages((prev) => [...prev, { role: "user", text }]);
      setInput("");
      await answerWizard(text);
      return;
    }
    if (welcome?.phase === "personalized" || welcome?.complete) {
      openChat();
    }
  }

  async function onSkip() {
    await answerWizard("", true);
  }

  const firstName = session?.name?.split(" ")[0] ?? "";

  return (
    <div className="welcome">
      <header className="welcome__head">
        <GenesisMark className="welcome__mark" />
        <div>
          <p className="welcome__eyebrow">Добро пожаловать в Virtus Core</p>
          <h1>{session?.headline ?? "Ваша цифровая компания готова."}</h1>
          {firstName ? <p className="welcome__sub">Здравствуйте, {firstName}.</p> : null}
        </div>
      </header>

      <div className="welcome__chat">
        {messages.map((m, i) => (
          <div
            key={`${m.role}-${i}`}
            className={`welcome__bubble welcome__bubble--${m.role}`}
          >
            <span className="welcome__who">
              {m.role === "assistant" ? ASSISTANT_NAME : "Вы"}
            </span>
            <p>{m.text}</p>
          </div>
        ))}
      </div>

      {welcome?.phase === "personalized" && welcome.quick_actions?.length ? (
        <div className="welcome__actions">
          <p className="welcome__actions-title">С чего начнём?</p>
          <div className="welcome__actions-grid">
            {welcome.quick_actions.map((a) => (
              <button
                key={a.id}
                type="button"
                className="btn btn--ghost welcome__action"
                onClick={() => openChat(a.label)}
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {error ? <p className="connect__error">{error}</p> : null}

      <footer className="welcome__footer">
        {welcome?.phase === "greeting" ? (
          <button
            type="button"
            className="btn btn--primary"
            disabled={busy}
            onClick={() => void onContinue()}
          >
            Начать
          </button>
        ) : null}

        {welcome?.phase === "wizard" ? (
          <>
            <input
              className="welcome__input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ваш ответ…"
              onKeyDown={(e) => {
                if (e.key === "Enter") void onContinue();
              }}
            />
            <div className="welcome__footer-row">
              <button
                type="button"
                className="btn btn--ghost"
                disabled={busy}
                onClick={() => void onSkip()}
              >
                Позже
              </button>
              <button
                type="button"
                className="btn btn--primary"
                disabled={busy || !input.trim()}
                onClick={() => void onContinue()}
              >
                Ответить
              </button>
            </div>
          </>
        ) : null}

        {welcome?.phase === "personalized" || welcome?.complete ? (
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => openChat()}
          >
            Открыть чат с {ASSISTANT_NAME}
          </button>
        ) : null}
      </footer>
    </div>
  );
}
