import { useEffect, useRef, useState, type DragEvent } from "react";
import {
  classifyAttachment,
  validateAttachmentSize,
  type ChatAttachmentMeta,
} from "@genesis/chat/attachments";
import { useAppSettings } from "../context/AppSettingsContext";
import { useNavigation } from "../context/NavigationContext";
import { askAssistant } from "../lib/endpoints";
import {
  loadChat,
  loadPinnedPrompts,
  QUICK_COMMANDS,
  resolveQuickCommand,
  saveChat,
  savePinnedPrompts,
  searchChat,
  type ChatMessage,
} from "../lib/chatStore";
import { copyText, MessageBody } from "../lib/markdown";

function ChatBubble({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false);

  async function onCopy() {
    const ok = await copyText(message.text);
    if (ok) {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    }
  }

  return (
    <div className={`chat__row chat__row--${message.role}`}>
      <div className={`chat__bubble chat__bubble--${message.role}`}>
        <div className="chat__meta">
          <span>{message.role === "user" ? "You" : "Genesis"}</span>
          <time>{message.at}</time>
        </div>
        {message.role === "assistant" ? (
          <MessageBody text={message.text} />
        ) : (
          <p className="chat__plain">{message.text}</p>
        )}
        <button
          type="button"
          className="chat__copy"
          onClick={() => void onCopy()}
          aria-label="Copy message"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}

export function ChatPage() {
  const { settings } = useAppSettings();
  const { chatPrefill, clearChatPrefill } = useNavigation();
  const [messages, setMessages] = useState<ChatMessage[]>(loadChat);
  const [pinned, setPinned] = useState<string[]>(loadPinnedPrompts);
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dropHint, setDropHint] = useState<string | null>(null);
  const [attachments, setAttachments] = useState<ChatAttachmentMeta[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const visible = search.trim() ? searchChat(messages, search) : messages;

  useEffect(() => {
    saveChat(messages);
  }, [messages]);

  useEffect(() => {
    if (chatPrefill) {
      setInput(chatPrefill);
      clearChatPrefill();
    }
  }, [chatPrefill, clearChatPrefill]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending, visible.length]);

  async function send(text?: string) {
    const raw = (text ?? input).trim();
    const question = resolveQuickCommand(raw) ?? raw;
    if (!question || sending) return;

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

    try {
      const res = await askAssistant(settings, question);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: res.answer,
          at: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Assistant unavailable");
    } finally {
      setSending(false);
    }
  }

  function pinCurrentInput() {
    const q = input.trim();
    if (!q || pinned.includes(q)) return;
    const next = [q, ...pinned].slice(0, 12);
    setPinned(next);
    savePinnedPrompts(next);
  }

  function removePin(prompt: string) {
    const next = pinned.filter((p) => p !== prompt);
    setPinned(next);
    savePinnedPrompts(next);
  }

  function addFiles(fileList: FileList | File[]) {
    const next: ChatAttachmentMeta[] = [];
    for (const file of fileList) {
      const err = validateAttachmentSize(file.size);
      if (err) {
        setDropHint(err);
        continue;
      }
      next.push({
        id: crypto.randomUUID(),
        name: file.name,
        mime: file.type || "application/octet-stream",
        size: file.size,
        kind: classifyAttachment(file.type, file.name),
        status: "pending",
      });
    }
    if (next.length) setAttachments((prev) => [...prev, ...next].slice(0, 8));
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDropHint(null);
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  }

  return (
    <div
      className="page page--chat"
      onDragOver={(e) => {
        e.preventDefault();
        setDropHint("Отпустите файл… (upload — скоро)");
      }}
      onDragLeave={() => setDropHint(null)}
      onDrop={onDrop}
    >
      <header className="page__header page__header--row">
        <div>
          <h1>Chat</h1>
          <p>/focus · /status · /projects · /revenue</p>
        </div>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => {
            setMessages([]);
            localStorage.removeItem("genesis.client.chat.v2");
          }}
        >
          Clear
        </button>
      </header>

      <div className="chat-toolbar">
        <input
          className="chat-toolbar__search"
          placeholder="Поиск по истории…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {pinned.length > 0 ? (
        <div className="pinned-row">
          {pinned.map((p) => (
            <button
              key={p}
              type="button"
              className="pinned-chip"
              onClick={() => void send(p)}
              title="Unpin"
              onContextMenu={(e) => {
                e.preventDefault();
                removePin(p);
              }}
            >
              {p.length > 28 ? `${p.slice(0, 28)}…` : p}
            </button>
          ))}
        </div>
      ) : null}

      <div className="chat">
        <div className="chat__thread" aria-live="polite">
          {visible.length === 0 ? (
            <p className="chat__empty">
              Спросите о проектах, выручке или фокусе дня.
            </p>
          ) : (
            visible.map((m) => <ChatBubble key={m.id} message={m} />)
          )}
          {sending ? <p className="chat__typing">Genesis думает…</p> : null}
          <div ref={endRef} />
        </div>

        {dropHint ? <p className="banner banner--warn">{dropHint}</p> : null}
        {attachments.length > 0 ? (
          <div className="chat-attachments">
            {attachments.map((a) => (
              <span key={a.id} className="chat-attachment-chip">
                {a.name} ({a.kind})
              </span>
            ))}
          </div>
        ) : null}
        {error ? <p className="banner banner--warn">{error}</p> : null}

        <form
          className="chat__composer"
          onSubmit={(e) => {
            e.preventDefault();
            void send();
          }}
        >
          <input
            ref={fileRef}
            type="file"
            multiple
            hidden
            onChange={(e) => {
              if (e.target.files) addFiles(e.target.files);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => fileRef.current?.click()}
            title="Attach file"
          >
            📎
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Сообщение или /команда…"
            maxLength={500}
            disabled={sending}
            list="quick-cmds"
          />
          <datalist id="quick-cmds">
            {Object.keys(QUICK_COMMANDS).map((k) => (
              <option key={k} value={k} />
            ))}
          </datalist>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={pinCurrentInput}
            disabled={!input.trim()}
            title="Pin prompt (right-click chip to unpin)"
          >
            Pin
          </button>
          <button type="submit" className="btn btn--primary" disabled={sending}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
