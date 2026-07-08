"use client";

import { useCallback, useEffect, useRef, type KeyboardEvent, type MouseEvent } from "react";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import { VoiceOrb } from "./VoiceOrb";

export type PendingAttachment = {
  id: string;
  filename: string;
  content_type: string;
  is_image: boolean;
  previewUrl: string | null;
};

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  busy?: boolean;
  attachments: PendingAttachment[];
  onPickFiles: (files: FileList | null) => void;
  onRemoveAttachment: (id: string) => void;
  onToggleVoice: () => void;
  onRetryVoice?: () => void;
  voiceListening: boolean;
  voiceThinking?: boolean;
  voiceSpeaking?: boolean;
  voiceHint?: string;
  micNotice?: string;
  onDismissMicNotice?: () => void;
  micPermissionModal?: boolean;
  onConfirmMicPermission?: () => void;
  onCancelMicPermission?: () => void;
  onOpenVoiceSettings?: () => void;
  voiceSettingsOpen?: boolean;
  placeholder?: string;
  floating?: boolean;
  inputId?: string;
};

function sanitizeMicNotice(notice?: string): string | undefined {
  if (!notice?.trim()) return undefined;
  if (/NotAllowedError|Permission denied|NotFoundError|NotReadableError/i.test(notice)) {
    return (
      "Чтобы говорить голосом, разрешите доступ к микрофону.\n\n" +
      "Нажмите 🔒 возле адресной строки → Разрешения → Микрофон → Разрешить."
    );
  }
  return notice;
}

function ClipIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M16.5 6.5v9a4.5 4.5 0 1 1-9 0v-10a3 3 0 1 1 6 0v9.5a1.5 1.5 0 1 1-3 0V7"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MicIcon({ active }: { active?: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect
        x="9"
        y="3"
        width="6"
        height="11"
        rx="3"
        stroke="currentColor"
        strokeWidth="1.75"
        fill={active ? "currentColor" : "none"}
      />
      <path
        d="M5 11a7 7 0 0 0 14 0M12 18v3"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
      />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M5 12h14M13 6l6 6-6 6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
        stroke="currentColor"
        strokeWidth="1.75"
      />
      <path
        d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function GenesisChatComposer({
  value,
  onChange,
  onSend,
  busy = false,
  attachments,
  onPickFiles,
  onRemoveAttachment,
  onToggleVoice,
  onRetryVoice,
  voiceListening,
  voiceThinking = false,
  voiceSpeaking = false,
  voiceHint,
  micNotice,
  onDismissMicNotice,
  micPermissionModal = false,
  onConfirmMicPermission,
  onCancelMicPermission,
  onOpenVoiceSettings,
  voiceSettingsOpen = false,
  placeholder = `Сообщение для ${ASSISTANT_NAME}…`,
  floating = false,
  inputId = "genesis-chat-input",
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, []);

  useEffect(() => {
    resize();
  }, [value, resize]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!busy && (value.trim() || attachments.length)) onSend();
    }
  }

  function handleMicClick(e: MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    e.stopPropagation();
    if (busy) return;
    onToggleVoice();
  }

  const safeMicNotice = sanitizeMicNotice(micNotice);

  if (micPermissionModal) {
    return (
      <div className="px-4 pb-4">
        <div className="rounded-3xl border border-genesis-accent/30 bg-genesis-panel/95 p-6 text-center shadow-glow backdrop-blur-xl">
          <VoiceOrb mode="idle" />
          <p className="mt-2 text-sm font-medium text-white">Голосовой разговор с {ASSISTANT_NAME}</p>
          <p className="mt-2 text-sm leading-relaxed text-genesis-muted">
            Нажмите кнопку ниже — браузер спросит разрешение один раз.
          </p>
          <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:justify-center">
            <button
              type="button"
              onClick={onConfirmMicPermission}
              className="rounded-full bg-genesis-accent px-6 py-3 text-sm font-semibold text-white transition hover:opacity-90"
            >
              Разрешить микрофон
            </button>
            <button
              type="button"
              onClick={onCancelMicPermission}
              className="rounded-full border border-genesis-border-subtle px-6 py-3 text-sm text-genesis-muted transition hover:text-white"
            >
              Позже
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${floating ? "mx-auto w-full max-w-3xl px-4 pt-2" : "px-4 pb-4"}`}>
      {safeMicNotice && (
        <div
          role="status"
          className="mb-2 rounded-xl border border-white/10 bg-genesis-panel/80 px-3 py-2.5 text-xs leading-relaxed text-genesis-muted"
        >
          <p className="whitespace-pre-wrap">{safeMicNotice}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {onRetryVoice ? (
              <button
                type="button"
                onClick={onRetryVoice}
                className="rounded-full bg-genesis-accent px-3 py-1.5 text-xs font-semibold text-white transition hover:opacity-90"
              >
                Попробовать снова
              </button>
            ) : null}
            {onDismissMicNotice ? (
              <button
                type="button"
                onClick={onDismissMicNotice}
                className="rounded-full border border-genesis-border-subtle px-3 py-1.5 text-xs text-genesis-muted transition hover:text-white"
              >
                Закрыть
              </button>
            ) : null}
          </div>
        </div>
      )}
      {voiceHint && voiceListening && (
        <p className="mb-2 text-center text-xs text-genesis-accent">{voiceHint}</p>
      )}
      {voiceListening && (
        <div className="mb-2 flex flex-col items-center rounded-xl border border-genesis-accent/25 bg-genesis-accent/5 px-3 py-3">
          <VoiceOrb mode="listening" />
        </div>
      )}
      {voiceSpeaking && !voiceListening && (
        <div className="mb-2 flex flex-col items-center rounded-xl border border-emerald-500/25 bg-emerald-500/5 px-3 py-3">
          <VoiceOrb mode="speaking" />
        </div>
      )}
      {voiceThinking && !voiceListening && !voiceSpeaking && (
        <div className="mb-2 flex flex-col items-center rounded-xl border border-indigo-500/25 bg-indigo-500/5 px-3 py-3">
          <VoiceOrb mode="thinking" />
        </div>
      )}
      {attachments.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {attachments.map((a) => (
            <div
              key={a.id}
              className="relative flex items-center gap-2 rounded-xl border border-genesis-border-subtle bg-genesis-panel/90 px-2 py-1.5 text-xs"
            >
              {a.previewUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={a.previewUrl} alt="" className="h-10 w-10 rounded-lg object-cover" />
              ) : (
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-genesis-bg text-genesis-muted">
                  📄
                </span>
              )}
              <span className="max-w-[120px] truncate text-genesis-text">{a.filename}</span>
              <button
                type="button"
                onClick={() => onRemoveAttachment(a.id)}
                className="ml-1 rounded-full px-1.5 text-genesis-muted hover:text-white"
                aria-label="Удалить файл"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 rounded-3xl border border-white/10 bg-genesis-panel/95 p-2 shadow-[0_8px_32px_rgba(0,0,0,0.45)] backdrop-blur-xl">
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          multiple
          accept="image/*,.pdf,.doc,.docx"
          onChange={(e) => {
            onPickFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={busy}
          className="mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-genesis-muted transition hover:bg-white/5 hover:text-white disabled:opacity-40"
          aria-label="Прикрепить файл"
        >
          <ClipIcon />
        </button>

        <textarea
          id={inputId}
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={busy}
          placeholder={placeholder}
          className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent py-2.5 text-base leading-relaxed text-white placeholder:text-genesis-muted/60 focus:outline-none"
        />

        <button
          type="button"
          onClick={() => onOpenVoiceSettings?.()}
          disabled={busy || !onOpenVoiceSettings}
          className={`mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition disabled:opacity-40 ${
            voiceSettingsOpen
              ? "bg-white/10 text-white"
              : "text-genesis-muted hover:bg-white/5 hover:text-white"
          }`}
          aria-label="Настройки голоса"
        >
          <SettingsIcon />
        </button>

        <button
          type="button"
          onClick={handleMicClick}
          disabled={busy}
          className={`relative z-10 mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition disabled:opacity-40 ${
            voiceListening
              ? "bg-genesis-accent/20 text-genesis-accent"
              : "text-genesis-muted hover:bg-genesis-accent/15 hover:text-genesis-accent"
          }`}
          aria-label={voiceListening ? "Остановить запись" : "Говорить голосом"}
        >
          <MicIcon active={voiceListening} />
        </button>

        <button
          type="button"
          onClick={onSend}
          disabled={busy || (!value.trim() && !attachments.length)}
          className="mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-genesis-accent text-white transition hover:opacity-90 disabled:opacity-40"
          aria-label="Отправить"
        >
          <SendIcon />
        </button>
      </div>
    </div>
  );
}
