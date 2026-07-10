"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge } from "./ui/Badge";
import {
  GenesisChatComposer,
  type PendingAttachment,
  type VoiceUiStatus,
} from "./GenesisChatComposer";
import {
  getSpeechRecognitionCtor,
  isMicContextAllowed,
  listAudioInputDevices,
  logVoiceDiagnostics,
  micPermissionState,
  MIC_CONTEXT_WARNING,
  voiceErrorMessage,
} from "../lib/voiceRuntime";
import { fetchTtsStatus, isInterruptPhrase, isSpeaking, speakGenesis, startInterruptListener, stopInterruptListener, stopSpeaking } from "../lib/ttsRuntime";
import {
  ASSISTANT_NAME,
  BRAND_NAME,
  PUBLIC_WELCOME,
} from "../lib/publicBrand";
import { VectorBrandSignature } from "./VectorBrandSignature";
import {
  loadVoiceSettings,
  type VoiceSettings,
} from "../lib/voiceSettings";
import { ChatHistorySidebar } from "./ChatHistorySidebar";
import { LanguageSwitcher } from "./LanguageSwitcher";
import {
  createSession,
  deleteSessionApi,
  fetchSessionDetail,
  fetchSessionList,
  loadSessionsStore,
  pinSessionApi,
  saveSessionsStore,
  type ChatSessionMeta,
} from "../lib/chatSessions";
import { VoiceSettingsPanel } from "./VoiceSettingsPanel";
import { CommunicationStylePicker } from "./CommunicationStylePicker";
import {
  loadCommunicationStyle,
  type CommunicationStyle,
} from "../lib/communicationStyle";
import { appendDictationText, loadMicMode, type MicMode } from "../lib/micMode";
import { useLocale } from "../context/LocaleContext";
import { useChatAutoScroll } from "../lib/useChatAutoScroll";
import { ChatMessageSpring } from "./motion/ChatMessageSpring";
import { SpringIn } from "./motion/SpringIn";
import { ExecutionResultPanel } from "./ExecutionResultPanel";
import {
  normalizePublicHref,
  publicApiBase,
  rewritePublicSiteUrls,
} from "../lib/publicApiBase";

const API = publicApiBase();
import { getVisitorId } from "../lib/visitorId";
const HI_BUILD_KEY = "genesis_hi_build";
const HI_BUILD_EXPECTED = "genesis-mind-v3.0";
const DEV_MODE_KEY = "genesis_developer_mode";

function devModeAvailable(): boolean {
  if (process.env.NEXT_PUBLIC_GENESIS_DEV_MODE === "1") return true;
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1";
}

type Message = {
  role: "user" | "assistant";
  text: string;
  generating?: boolean;
  stopped?: boolean;
  provider?: string | null;
  cta_href?: string | null;
  cta_label?: string | null;
  cta_actions?: Array<{ href: string; label: string; group?: string; available?: boolean }> | null;
  attachments?: PendingAttachment[];
  debug?: GenesisDebug | null;
};

type RuntimePipeline = {
  user_message?: string;
  steps?: Array<{ step?: string; status?: string; employee?: string; model?: string }>;
  thinking_brief?: string;
  employee_chosen?: string;
  employee_why?: string;
  employee_model?: string;
  raw_prompt?: { system?: string; messages?: Array<{ role?: string; content?: string }> };
  raw_response?: string;
  calibration?: { passed?: boolean; reasons?: string[] };
  final_response?: string;
  cloud_llm_used?: boolean;
  answer_source?: string;
  local_fallback_warning?: string | null;
  fallback_started_at?: string | null;
  employee_diagnostics?: Array<{
    employee_id?: string;
    callable?: boolean;
    code?: string;
    reason?: string;
  }>;
};

type GenesisDebug = {
  brain_version?: string;
  provider?: string;
  current_employee?: string;
  current_model?: string;
  current_provider?: string;
  cloud_llm_used?: boolean;
  local_fallback_warning?: string | null;
  answer_source?: string;
  runtime_pipeline?: RuntimePipeline;
  conversation_pipeline?: Array<{ step?: string; status?: string }>;
  executive_action?: string;
  executive_decision?: {
    action?: string;
    confidence?: number;
    optional_question?: string | null;
  };
  thinking_brief?: Record<string, unknown>;
  thinking_brief_text?: string;
  calibration?: {
    llm_draft_preview?: string;
    needs_rewrite?: boolean;
    used_brief_speech_fallback?: boolean;
    verdict?: { passed?: boolean; reasons?: string[] };
  };
  workforce_reality?: {
    chosen_employee?: string;
    chosen_score?: number | null;
    chosen_latency_sec?: number;
    why_chosen?: string;
    second_pass?: boolean;
    escalation_count?: number;
    emotional_mood?: string;
    thinking_implicit_need?: string;
    final_calibration?: { passed?: boolean; reasons?: string[] };
    not_chosen?: Array<{ employee_id?: string; score?: number; why?: string }>;
    attempts?: Array<{
      employee_id?: string;
      employee_score?: number;
      latency_sec?: number;
      outcome?: string;
      calibration?: { passed?: boolean; reasons?: string[] };
    }>;
  };
  emotional_mood?: string;
  intent?: string | null;
};

type ChatApiResponse = {
  answer?: string;
  provider?: string | null;
  cta_href?: string | null;
  cta_label?: string | null;
  cta_actions?: Array<{ href: string; label: string; group?: string; available?: boolean }> | null;
  debug?: GenesisDebug | null;
  context?: { workspace_id?: string; execution?: unknown } | null;
  session_id?: string | null;
};

const STARTERS_VISIBLE = [
  { label: "💇 Сайт салона", message: "Хочу сайт для салона красоты" },
  { label: "🍽️ Сайт кафе", message: "Мне нужен сайт для кафе" },
  { label: "📋 Заказать сайт", message: "Хочу заказать лендинг под ключ" },
];

const STARTERS_MORE = [
  { label: "🏪 Интернет-магазин", message: "Мне нужен интернет-магазин" },
  { label: "🚗 Автосервис", message: "Мне нужен сайт для автосервиса" },
  { label: "✈️ Telegram-бот", message: "Мне нужен Telegram-бот для бизнеса" },
  { label: "🤖 AI на сайте", message: "Хочу AI-консультанта на сайте" },
];

const FALLBACK_WELCOME_PUBLIC = PUBLIC_WELCOME;

const FALLBACK_WELCOME_OWNER = PUBLIC_WELCOME;

type Props = {
  onConversationActive?: (active: boolean) => void;
  /** public = /site visitors; owner = Mission Control / CEO chat */
  scope?: "public" | "owner";
  /** Customer hub — Vector panel beside projects, not full-screen chat */
  hubMode?: boolean;
};

export function GenesisConcierge({ onConversationActive, scope = "public", hubMode = false }: Props) {
  const { t } = useTranslation(["chat", "errors", "common"]);
  const { uiLocale, assistantLocale } = useLocale();
  const isPublic = scope === "public";
  const isPublicHub = isPublic && hubMode;
  const fallbackWelcome = isPublic ? FALLBACK_WELCOME_PUBLIC : FALLBACK_WELCOME_OWNER;
  const assistantLabel = ASSISTANT_NAME;
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [welcomeText, setWelcomeText] = useState(fallbackWelcome);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: fallbackWelcome },
  ]);
  const [chatCollapsed, setChatCollapsed] = useState(isPublic);
  const [pendingFiles, setPendingFiles] = useState<PendingAttachment[]>([]);
  const [attachmentsUploading, setAttachmentsUploading] = useState(0);
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceThinking, setVoiceThinking] = useState(false);
  const [voiceSpeaking, setVoiceSpeaking] = useState(false);
  const [voiceHint, setVoiceHint] = useState<string | undefined>();
  const [micNotice, setMicNotice] = useState<string | undefined>();
  const [micPermissionModal, setMicPermissionModal] = useState(false);
  const [showMoreStarters, setShowMoreStarters] = useState(false);
  const [composerFocused, setComposerFocused] = useState(false);
  const [voiceSettingsOpen, setVoiceSettingsOpen] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>(() => loadVoiceSettings());
  const [communicationStyle, setCommunicationStyle] = useState<CommunicationStyle>(() =>
    loadCommunicationStyle(),
  );
  const [micMode, setMicMode] = useState<MicMode>(() => loadMicMode());
  const [ttsCloudAvailable, setTtsCloudAvailable] = useState(false);
  const [ttsPreferred, setTtsPreferred] = useState<string>("browser");
  const [developerMode, setDeveloperMode] = useState(false);
  const [openDebugIndex, setOpenDebugIndex] = useState<number | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionList, setSessionList] = useState<ChatSessionMeta[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [voiceStoppedFlash, setVoiceStoppedFlash] = useState(false);
  const [attachHint, setAttachHint] = useState<string | undefined>(undefined);
  const devAvailable = devModeAvailable();
  const visitorId = getVisitorId(scope);

  const voiceSettingsRef = useRef(voiceSettings);
  const communicationStyleRef = useRef(communicationStyle);
  const micModeRef = useRef(micMode);
  const dictationActiveRef = useRef(false);
  const prevMicModeRef = useRef(micMode);

  const messagesRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const lastInputWasVoiceRef = useRef(false);
  const voiceContinuousRef = useRef(false);
  const startVoiceRef = useRef<(() => Promise<void>) | null>(null);
  const hydratedRef = useRef(false);
  const chatAbortRef = useRef<AbortController | null>(null);
  const abortRequestedRef = useRef(false);
  const voiceStoppedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    voiceSettingsRef.current = voiceSettings;
  }, [voiceSettings]);
  useEffect(() => {
    communicationStyleRef.current = communicationStyle;
  }, [communicationStyle]);
  useEffect(() => {
    micModeRef.current = micMode;
  }, [micMode]);

  useEffect(() => {
    if (!devAvailable) return;
    try {
      setDeveloperMode(localStorage.getItem(DEV_MODE_KEY) === "1");
    } catch {
      /* private mode */
    }
  }, [devAvailable]);

  const toggleDeveloperMode = useCallback(() => {
    setDeveloperMode((on) => {
      const next = !on;
      try {
        localStorage.setItem(DEV_MODE_KEY, next ? "1" : "0");
      } catch {
        /* private mode */
      }
      if (!next) setOpenDebugIndex(null);
      return next;
    });
  }, []);

  useEffect(() => {
    void fetchTtsStatus().then((st) => {
      if (!st) return;
      setTtsCloudAvailable(Boolean(st.cloud_available));
      if (st.preferred_provider) setTtsPreferred(st.preferred_provider);
    });
  }, []);

  const hasConversation = messages.some((m) => m.role === "user");
  const showThread = isPublic ? true : hasConversation && !chatCollapsed;
  const publicImmersive = isPublic && hasConversation && !hubMode;

  const { showJumpButton, handleScroll, jumpToLatest, pinToBottom } = useChatAutoScroll(
    messagesRef,
    [messages, busy, voiceSpeaking, voiceThinking, showThread],
    showThread,
  );

  useEffect(() => {
    onConversationActive?.(isPublic ? hasConversation : showThread);
  }, [isPublic, hasConversation, showThread, onConversationActive]);

  useEffect(() => {
    if (!isPublic) return;
    const id = requestAnimationFrame(() => {
      pinToBottom();
      document.getElementById("genesis-chat-input")?.scrollIntoView({ block: "end", behavior: "auto" });
    });
    return () => cancelAnimationFrame(id);
  }, [isPublic, pinToBottom]);

  useEffect(() => {
    fetch(`${API}/api/public/genesis-ai/status`)
      .then((r) => r.json())
      .then((st: {
        hi_build?: string;
        brain_version?: string;
        llm_configured?: boolean;
      }) => {
        console.info("[Genesis runtime]", {
          frontend_build: HI_BUILD_EXPECTED,
          backend_hi_build: st?.hi_build,
          brain_version: st?.brain_version,
          match: st?.hi_build === HI_BUILD_EXPECTED,
        });
      })
      .catch(() => undefined);
    fetch(`${API}/api/public/genesis-ai/greeting?visitor_id=${encodeURIComponent(visitorId)}`)
      .then((r) => r.json())
      .then((d: { greeting?: string }) => {
        const g = d?.greeting?.trim();
        if (!g) return;
        const compact = g.replace(/\s+/g, " ").trim();
        setWelcomeText(compact);
        setMessages((prev) => {
          if (prev.some((m) => m.role === "user")) return prev;
          if (prev.length === 1 && prev[0]?.role === "assistant") {
            return [{ ...prev[0], text: compact }];
          }
          return prev;
        });
      })
      .catch(() => undefined);
    fetch(`${API}/api/public/genesis-ai/attachments/policy?visitor_id=${encodeURIComponent(visitorId)}`)
      .then((r) => r.json())
      .then((p: { analyze?: { available_kinds?: string[] } }) => {
        const kinds = p?.analyze?.available_kinds ?? [];
        setAttachHint(kinds.includes("pdf") ? t("attachHint") : t("attachHintLegacy"));
      })
      .catch(() => undefined);
  }, [visitorId, t]);

  const resetToWelcome = useCallback(
    (greeting?: string) => {
      const text = greeting?.trim() || welcomeText || fallbackWelcome;
      setMessages([{ role: "assistant", text }]);
      setChatCollapsed(true);
      setActiveSessionId(null);
      const store = loadSessionsStore(scope);
      store.activeSessionId = null;
      saveSessionsStore(scope, store);
    },
    [scope, welcomeText],
  );

  const handlePublicHome = useCallback(() => {
    setSidebarOpen(false);
    resetToWelcome();
    onConversationActive?.(false);
    window.dispatchEvent(new Event("genesis:home"));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [resetToWelcome, onConversationActive]);

  const handlePublicMenuHome = useCallback(() => {
    setSidebarOpen(false);
    handlePublicHome();
  }, [handlePublicHome]);

  const refreshSessionList = useCallback(async () => {
    const rows = await fetchSessionList(visitorId);
    setSessionList(rows);
  }, [visitorId]);

  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;
    try {
      const build = localStorage.getItem(HI_BUILD_KEY);
      if (build !== HI_BUILD_EXPECTED) {
        localStorage.setItem(HI_BUILD_KEY, HI_BUILD_EXPECTED);
      }
    } catch {
      /* ignore */
    }
    void refreshSessionList();
    resetToWelcome();
  }, [refreshSessionList, resetToWelcome]);

  const persistLocalMessages = useCallback(
    (sessionId: string | null, msgs: Message[]) => {
      if (!sessionId) return;
      const store = loadSessionsStore(scope);
      store.localMessages[sessionId] = msgs.map((m) => ({
        role: m.role,
        text: m.text,
        cta_href: m.cta_href,
        cta_label: m.cta_label,
      }));
      store.activeSessionId = sessionId;
      saveSessionsStore(scope, store);
    },
    [scope],
  );

  const handleNewChat = useCallback(async () => {
    const created = await createSession(visitorId);
    if (!created) {
      resetToWelcome();
      return;
    }
    setActiveSessionId(created.session_id);
    setSessionList((prev) => [created, ...prev.filter((s) => s.session_id !== created.session_id)]);
    setMessages([{ role: "assistant", text: welcomeText || fallbackWelcome }]);
    setChatCollapsed(true);
    const store = loadSessionsStore(scope);
    store.activeSessionId = created.session_id;
    store.localMessages[created.session_id] = [];
    saveSessionsStore(scope, store);
  }, [visitorId, welcomeText, scope, resetToWelcome]);

  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      setActiveSessionId(sessionId);
      setChatCollapsed(false);
      const cached = loadSessionsStore(scope).localMessages[sessionId];
      if (cached?.length) {
        setMessages(cached as Message[]);
        return;
      }
      const detail = await fetchSessionDetail(sessionId, visitorId);
      if (!detail?.messages.length) {
        setMessages([{ role: "assistant", text: welcomeText || fallbackWelcome }]);
        return;
      }
      setMessages(detail.messages as Message[]);
      persistLocalMessages(sessionId, detail.messages as Message[]);
    },
    [visitorId, welcomeText, scope, persistLocalMessages],
  );

  const handleDeleteSession = useCallback(
    async (sessionId: string) => {
      await deleteSessionApi(sessionId, visitorId);
      setSessionList((prev) => prev.filter((s) => s.session_id !== sessionId));
      const store = loadSessionsStore(scope);
      delete store.localMessages[sessionId];
      saveSessionsStore(scope, store);
      if (activeSessionId === sessionId) resetToWelcome();
    },
    [visitorId, scope, activeSessionId, resetToWelcome],
  );

  const handlePinSession = useCallback(
    async (sessionId: string, pinned: boolean) => {
      await pinSessionApi(sessionId, visitorId, pinned);
      void refreshSessionList();
    },
    [visitorId, refreshSessionList],
  );

  useEffect(() => {
    return () => {
      if (voiceStoppedTimerRef.current) clearTimeout(voiceStoppedTimerRef.current);
      chatAbortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    const home = () => {
      setChatCollapsed(true);
      document.getElementById("genesis-chat")?.scrollIntoView({ behavior: "smooth" });
    };
    window.addEventListener("genesis:home", home);
    return () => window.removeEventListener("genesis:home", home);
  }, []);

  const uploadFiles = useCallback(async (files: FileList | null) => {
    if (!files?.length) return;
    setAttachmentsUploading((n) => n + 1);
    const next: PendingAttachment[] = [];
    const batchSize = files.length;
    try {
      for (const file of Array.from(files)) {
        const form = new FormData();
        form.append("file", file);
        try {
          const qs = new URLSearchParams({
            visitor_id: visitorId,
            files_in_message: String(batchSize),
          });
          const res = await fetch(`${API}/api/public/genesis-ai/attachments?${qs}`, {
            method: "POST",
            body: form,
          });
          if (!res.ok) continue;
          const data = (await res.json()) as Partial<PendingAttachment> & {
            id?: string;
            stored_only?: boolean;
          };
          if (!data?.id) continue;
          const previewUrl = data.is_image ? URL.createObjectURL(file) : null;
          next.push({
            id: data.id,
            filename: data.filename ?? file.name,
            content_type: data.content_type ?? file.type,
            is_image: Boolean(data.is_image),
            previewUrl,
            stored_only: data.stored_only !== false,
          });
        } catch {
          /* backend offline — skip */
        }
      }
      if (next.length) setPendingFiles((prev) => [...prev, ...next]);
    } finally {
      setAttachmentsUploading((n) => Math.max(0, n - 1));
    }
  }, [visitorId]);

  const removeAttachment = useCallback((id: string) => {
    setPendingFiles((prev) => {
      const item = prev.find((p) => p.id === id);
      if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl);
      return prev.filter((p) => p.id !== id);
    });
  }, []);

  const interruptSpeechIfNeeded = useCallback(() => {
    if (!voiceSpeaking && !isSpeaking()) return;
    stopSpeaking();
    stopInterruptListener();
    setVoiceSpeaking(false);
    setVoiceThinking(false);
    if (voiceStoppedTimerRef.current) clearTimeout(voiceStoppedTimerRef.current);
    setVoiceStoppedFlash(true);
    voiceStoppedTimerRef.current = setTimeout(() => setVoiceStoppedFlash(false), 2000);
  }, [voiceSpeaking]);

  const stopGeneration = useCallback(() => {
    if (!chatAbortRef.current) return;
    abortRequestedRef.current = true;
    chatAbortRef.current.abort();
    chatAbortRef.current = null;
  }, []);

  const handleStopActive = useCallback(() => {
    interruptSpeechIfNeeded();
    stopGeneration();
  }, [interruptSpeechIfNeeded, stopGeneration]);

  const voiceUiStatus: VoiceUiStatus = voiceStoppedFlash
    ? "stopped"
    : voiceListening
      ? "listening"
      : voiceSpeaking
        ? "speaking"
        : voiceThinking || (busy && lastInputWasVoiceRef.current)
          ? "thinking"
          : "ready";

  const sendMessage = useCallback(
    async (text: string, files: PendingAttachment[] = [], fromVoice = false) => {
      const q = text.trim();
      if ((!q && !files.length) || busy) return;
      if (attachmentsUploading > 0) {
        setAttachHint(t("attachUploading"));
        return;
      }

      if (isInterruptPhrase(q) && (voiceSpeaking || isSpeaking())) {
        interruptSpeechIfNeeded();
        return;
      }

      if (files.length && !files.every((f) => f.id)) {
        setAttachHint(t("attachUploading"));
        return;
      }

      if (fromVoice) lastInputWasVoiceRef.current = true;
      setChatCollapsed(false);

      const displayText =
        q || (files.length === 1 ? `📎 ${files[0]?.filename ?? "файл"}` : `📎 ${files.length} файла`);

      const sentFiles = files.map((f) => ({ ...f }));

      const history = messages
        .filter((m) => !m.generating && (m.role === "user" || m.role === "assistant"))
        .slice(1)
        .slice(-12)
        .map((m) => ({ role: m.role, content: m.text ?? "" }));

      const nextUserMsg: Message = {
        role: "user",
        text: displayText,
        attachments: sentFiles.length ? sentFiles : undefined,
      };
      setMessages((prev) => [
        ...prev,
        nextUserMsg,
        { role: "assistant", text: "", generating: true },
      ]);
      setInput("");
      setPendingFiles([]);
      setBusy(true);
      pinToBottom();
      if (fromVoice) setVoiceThinking(true);

      let sessionId = activeSessionId;
      if (!sessionId) {
        const created = await createSession(visitorId);
        if (created) {
          sessionId = created.session_id;
          setActiveSessionId(sessionId);
          setSessionList((prev) => [
            created,
            ...prev.filter((s) => s.session_id !== created.session_id),
          ]);
        }
      }

      chatAbortRef.current?.abort();
      const controller = new AbortController();
      chatAbortRef.current = controller;
      abortRequestedRef.current = false;
      const requestTimeout = window.setTimeout(() => controller.abort(), 90_000);

      try {
        const endpoint = `${API}/api/public/genesis-ai${developerMode ? "?debug=true" : ""}`;
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            question: q || t("filesOnlyPrompt"),
            history,
            visitor_id: visitorId,
            session_id: sessionId,
            ui_locale: uiLocale,
            assistant_locale: assistantLocale,
            communication_style: communicationStyleRef.current,
            context: scope === "owner" ? { personality_mode: "ceo" } : undefined,
            attachment_ids: files.map((f) => f.id).filter(Boolean),
          }),
        });

        let data: ChatApiResponse = {};
        try {
          data = (await res.json()) as ChatApiResponse;
        } catch {
          data = {};
        }

        if (!res.ok) {
          throw new Error("bad response");
        }

        const answer =
          rewritePublicSiteUrls(
            data?.answer?.trim() || t("emptyAnswer", { ns: "errors" }),
          );

        setMessages((prev) => {
          const base = prev[prev.length - 1]?.generating ? prev.slice(0, -1) : prev;
          const next = [
            ...base,
            {
              role: "assistant" as const,
              text: answer,
              provider: data?.provider ?? null,
              cta_href: normalizePublicHref(data?.cta_href),
              cta_label: data?.cta_label ?? null,
              cta_actions: (data?.cta_actions ?? null)?.map((a) => ({
                href: normalizePublicHref(a.href) ?? a.href,
                label: a.label,
              })) ?? null,
              debug: developerMode ? (data?.debug ?? null) : undefined,
            },
          ];
          const sid = (data as { session_id?: string })?.session_id || sessionId;
          if (sid) persistLocalMessages(sid, next);
          return next;
        });
        void refreshSessionList();

        if (data?.provider === "execution" || data?.context?.workspace_id) {
          window.dispatchEvent(new Event("genesis:project-updated"));
        }

        if (lastInputWasVoiceRef.current || voiceContinuousRef.current) {
          const vs = voiceSettingsRef.current;
          const cleanupInterrupt = startInterruptListener((phrase) => {
            console.info("[Genesis voice] interrupted:", phrase);
            setVoiceSpeaking(false);
            setVoiceThinking(false);
          });
          void speakGenesis(answer, vs, {
            onStart: () => setVoiceSpeaking(true),
            onEnd: () => {
              cleanupInterrupt();
              setVoiceSpeaking(false);
              setVoiceThinking(false);
              if (voiceContinuousRef.current && vs.autoListen && !vs.pushToTalk) {
                void startVoiceRef.current?.();
              }
            },
            onProvider: (p) => {
              console.info("[Genesis voice] TTS provider:", p);
            },
          });
          lastInputWasVoiceRef.current = false;
        }
      } catch (err) {
        if (abortRequestedRef.current) {
          abortRequestedRef.current = false;
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role !== "assistant" || !last.generating) return prev;
            const partial = last.text?.trim();
            const stopped = t("generationStopped");
            const text = partial ? `${partial}\n\n${stopped}` : stopped;
            const next = [...prev.slice(0, -1), { ...last, text, generating: false, stopped: true }];
            if (sessionId) persistLocalMessages(sessionId, next);
            return next;
          });
          return;
        }
        const timedOut = err instanceof DOMException && err.name === "AbortError";
        setMessages((prev) => {
          const base = prev[prev.length - 1]?.generating ? prev.slice(0, -1) : prev;
          return [
            ...base,
            {
              role: "assistant",
              text: timedOut
                ? "Ответ занял слишком много времени. Попробуйте короче — или нажмите ещё раз."
                : t("offline", { ns: "errors", brand: BRAND_NAME }),
            },
          ];
        });
      } finally {
        window.clearTimeout(requestTimeout);
        chatAbortRef.current = null;
        setBusy(false);
        setVoiceThinking(false);
      }
    },
    [
      busy,
      messages,
      developerMode,
      activeSessionId,
      visitorId,
      scope,
      persistLocalMessages,
      refreshSessionList,
      voiceSpeaking,
      interruptSpeechIfNeeded,
      uiLocale,
      assistantLocale,
      communicationStyle,
      pinToBottom,
      t,
      attachmentsUploading,
    ],
  );

  const MIC_GRANTED_KEY = "genesis_mic_granted";

  const releaseMicStream = useCallback(() => {
    mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
    mediaStreamRef.current = null;
  }, []);

  const stopVoice = useCallback(() => {
    dictationActiveRef.current = false;
    try {
      recognitionRef.current?.stop();
    } catch {
      /* ignore */
    }
    recognitionRef.current = null;
    releaseMicStream();
    setVoiceListening(false);
    setVoiceHint(undefined);
  }, [releaseMicStream]);

  useEffect(() => {
    if (prevMicModeRef.current !== micMode) {
      stopVoice();
      prevMicModeRef.current = micMode;
    }
  }, [micMode, stopVoice]);

  const failMic = useCallback(
    (message: string, err?: unknown) => {
      voiceContinuousRef.current = false;
      if (err !== undefined) {
        console.error("[Genesis] voice error:", err);
      }
      try {
        recognitionRef.current?.stop();
      } catch {
        /* ignore */
      }
      recognitionRef.current = null;
      releaseMicStream();
      setVoiceListening(false);
      setVoiceHint(undefined);
      setMicNotice(message);
    },
    [releaseMicStream],
  );

  const startVoice = useCallback(async () => {
    setMicNotice(undefined);

    logVoiceDiagnostics("startVoice click", {
      hostname: typeof window !== "undefined" ? window.location.hostname : "",
      protocol: typeof window !== "undefined" ? window.location.protocol : "",
      href: typeof window !== "undefined" ? window.location.href : "",
    });

    if (!isMicContextAllowed()) {
      console.error("[Genesis] mic blocked: insecure context", window.location.href);
      failMic(MIC_CONTEXT_WARNING);
      return;
    }

    const SR = getSpeechRecognitionCtor();
    if (!SR) {
      console.error("[Genesis] SpeechRecognition API unavailable in this browser");
      failMic("Голосовой ввод недоступен в этом браузере. Используйте Chrome или Edge.");
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      failMic("Браузер не поддерживает доступ к микрофону.");
      return;
    }

    const devicesBefore = await listAudioInputDevices();
    logVoiceDiagnostics("enumerateDevices (before grant)", { devices: devicesBefore });

    const isDictation = micModeRef.current === "dictation";
    setVoiceHint(isDictation ? "Диктовка…" : "Слушаю…");

    try {
      logVoiceDiagnostics("getUserMedia request", { audio: true });
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      try {
        sessionStorage.setItem(MIC_GRANTED_KEY, "1");
      } catch {
        /* private mode */
      }
      const devicesAfter = await listAudioInputDevices();
      logVoiceDiagnostics("getUserMedia OK", {
        tracks: stream.getAudioTracks().map((t) => ({
          label: t.label,
          enabled: t.enabled,
          muted: t.muted,
        })),
        devices: devicesAfter,
      });
    } catch (err) {
      logVoiceDiagnostics("getUserMedia FAILED", { err });
      failMic(voiceErrorMessage(err), err);
      return;
    }

    try {
      const rec = new SR();
      rec.lang = "ru-RU";
      rec.interimResults = isDictation;
      rec.continuous = isDictation;
      rec.maxAlternatives = 1;
      if (isDictation) {
        dictationActiveRef.current = true;
      }
      rec.onstart = () => {
        console.info("[Genesis] speech recognition started", { mode: micModeRef.current });
        setVoiceListening(true);
        setVoiceHint(
          isDictation ? "Диктовка… говорите, текст появится в поле" : "Слушаю… говорите свободно",
        );
      };
      rec.onresult = (event: SpeechRecognitionEvent) => {
        if (micModeRef.current === "dictation") {
          let finalText = "";
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const piece = event.results[i]?.[0]?.transcript ?? "";
            if (event.results[i]?.isFinal) {
              finalText += piece;
            }
          }
          finalText = finalText.trim();
          console.info("[Genesis] dictation result:", finalText);
          if (finalText) {
            setInput((prev) => appendDictationText(prev, finalText));
          }
          return;
        }
        const transcript = event.results?.[0]?.[0]?.transcript?.trim();
        console.info("[Genesis] speech result:", transcript);
        if (transcript && isInterruptPhrase(transcript) && (voiceSpeaking || isSpeaking())) {
          interruptSpeechIfNeeded();
          stopVoice();
          return;
        }
        stopVoice();
        if (transcript) void sendMessage(transcript, [], true);
      };
      rec.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error("[Genesis] speech error:", event.error);
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          failMic(voiceErrorMessage({ name: "NotAllowedError" }), event);
          return;
        }
        if (event.error === "no-speech") {
          if (micModeRef.current === "dictation" && dictationActiveRef.current) {
            setVoiceHint("Пауза… продолжайте говорить или нажмите микрофон, чтобы остановить.");
            return;
          }
          setVoiceListening(false);
          setVoiceHint("Не расслышал — нажмите микрофон и говорите чуть громче.");
          return;
        }
        if (micModeRef.current === "dictation" && event.error === "aborted") {
          return;
        }
        setVoiceListening(false);
        setVoiceHint(undefined);
        failMic("Не получилось распознать речь. Попробуйте ещё раз.");
      };
      rec.onend = () => {
        console.info("[Genesis] speech recognition ended", { mode: micModeRef.current });
        if (micModeRef.current === "dictation" && dictationActiveRef.current) {
          try {
            rec.start();
          } catch {
            setVoiceListening(false);
            setVoiceHint(undefined);
          }
          return;
        }
        setVoiceListening(false);
      };
      recognitionRef.current = rec;
      rec.start();
    } catch (err) {
      failMic("Не удалось запустить распознавание речи.", err);
    }
  }, [failMic, sendMessage, stopVoice, interruptSpeechIfNeeded, voiceSpeaking]);

  startVoiceRef.current = startVoice;

  const toggleVoice = useCallback(async () => {
    if (voiceListening) {
      voiceContinuousRef.current = false;
      stopVoice();
      return;
    }
    if (micModeRef.current === "chat") {
      interruptSpeechIfNeeded();
    }
    voiceContinuousRef.current =
      micModeRef.current === "chat" && !voiceSettingsRef.current.pushToTalk;
    setMicNotice(undefined);
    const perm = await micPermissionState();
    logVoiceDiagnostics("permission state", { perm });
    if (perm === "granted") {
      void startVoice();
      return;
    }
    if (perm === "denied") {
      failMic(
        "Доступ к микрофону закрыт.\n\n" +
          "Нажмите 🔒 возле адресной строки → Разрешения → Микрофон → Разрешить.\n\n" +
          "Затем нажмите «Попробовать снова».",
      );
      return;
    }
    setMicPermissionModal(true);
  }, [voiceListening, stopVoice, startVoice, failMic, interruptSpeechIfNeeded]);

  const confirmMicPermission = useCallback(() => {
    setMicPermissionModal(false);
    voiceContinuousRef.current = !voiceSettingsRef.current.pushToTalk;
    void startVoice();
  }, [startVoice]);

  const speakLastAnswer = useCallback(() => {
    const last = [...messages].reverse().find(
      (m) => m.role === "assistant" && m.text?.trim() && !m.generating,
    );
    if (!last?.text) return;
    interruptSpeechIfNeeded();
    const cleanup = startInterruptListener(() => {
      setVoiceSpeaking(false);
    });
    void speakGenesis(last.text, voiceSettingsRef.current, {
      onStart: () => setVoiceSpeaking(true),
      onEnd: () => {
        cleanup();
        setVoiceSpeaking(false);
      },
    });
  }, [messages, interruptSpeechIfNeeded]);

  useEffect(() => {
    const focus = () => {
      document.getElementById("genesis-chat-input")?.focus();
    };
    const voice = () => {
      /* Must stay tied to user gesture — do not dispatch genesis:start-voice on mount */
      void toggleVoice();
    };
    const onAssign = (event: Event) => {
      const prompt = (event as CustomEvent<{ prompt?: string }>).detail?.prompt?.trim();
      focus();
      if (prompt) void sendMessage(prompt);
    };
    window.addEventListener("genesis:focus-chat", focus);
    window.addEventListener("genesis:start-voice", voice);
    window.addEventListener("genesis:assign-task", onAssign);
    return () => {
      window.removeEventListener("genesis:focus-chat", focus);
      window.removeEventListener("genesis:start-voice", voice);
      window.removeEventListener("genesis:assign-task", onAssign);
    };
  }, [toggleVoice, sendMessage]);

  const composer = (
    <>
      <VoiceSettingsPanel
        open={voiceSettingsOpen}
        onClose={() => setVoiceSettingsOpen(false)}
        settings={voiceSettings}
        onChange={setVoiceSettings}
        cloudAvailable={ttsCloudAvailable}
        preferredProvider={ttsPreferred}
      />
      {!isPublic ? (
        <div className={composerFocused ? "max-sm:hidden" : undefined}>
          <CommunicationStylePicker
            value={communicationStyle}
            onChange={setCommunicationStyle}
          />
        </div>
      ) : null}
      <GenesisChatComposer
        value={input}
        onChange={setInput}
        onSend={() => void sendMessage(input, pendingFiles)}
        busy={busy}
        generating={busy}
        attachments={pendingFiles ?? []}
        onPickFiles={(files) => void uploadFiles(files)}
        onRemoveAttachment={removeAttachment}
        onToggleVoice={() => void toggleVoice()}
        onStopActive={handleStopActive}
        onRetryVoice={() => {
          setMicNotice(undefined);
          void startVoice();
        }}
        voiceListening={voiceListening}
        voiceThinking={voiceThinking || (busy && lastInputWasVoiceRef.current)}
        voiceSpeaking={voiceSpeaking}
        voiceStatus={voiceUiStatus}
        micPermissionModal={micPermissionModal}
        onConfirmMicPermission={confirmMicPermission}
        onCancelMicPermission={() => setMicPermissionModal(false)}
        voiceHint={voiceHint}
        micNotice={micNotice}
        onDismissMicNotice={() => setMicNotice(undefined)}
        onOpenVoiceSettings={() => setVoiceSettingsOpen((o) => !o)}
        voiceSettingsOpen={voiceSettingsOpen}
        micMode={micMode}
        onMicModeChange={setMicMode}
        attachHint={attachHint}
        inputId="genesis-chat-input"
        onFocusChange={setComposerFocused}
        minimalMobile={isPublic && !hubMode}
        onSpeakAnswer={speakLastAnswer}
      />
    </>
  );

  const thread = messages ?? [];

  return (
    <div className={`flex flex-col gap-2 md:flex-row md:items-stretch ${isPublic && !hubMode ? "h-full" : isPublicHub ? "h-full min-h-0" : ""}`}>
      <ChatHistorySidebar
        sessions={sessionList}
        activeSessionId={activeSessionId}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        onCloseSidebar={() => setSidebarOpen(false)}
        onNewChat={() => void handleNewChat()}
        onSelect={(id) => void handleSelectSession(id)}
        onDelete={(id) => void handleDeleteSession(id)}
        onPin={(id, pinned) => void handlePinSession(id, pinned)}
        hideMobileToggle={isPublic}
        overlayOnly={isPublic}
        onGoHome={isPublic ? handlePublicMenuHome : undefined}
      />
    <section
      id="genesis-chat"
      className={`flex min-w-0 flex-1 flex-col overflow-hidden rounded-3xl border border-genesis-accent/25 bg-gradient-to-b from-indigo-950/40 via-genesis-panel to-genesis-bg shadow-glow transition-all duration-300 ${
        isPublicHub
          ? "h-full min-h-[min(70dvh,40rem)] max-sm:rounded-2xl"
          : isPublic
          ? publicImmersive
            ? `h-[100dvh] max-sm:rounded-none max-sm:border-x-0 max-sm:shadow-none${sidebarOpen ? " max-sm:pointer-events-none" : ""}`
            : "min-h-[min(72dvh,36rem)] max-h-[min(85dvh,40rem)] max-sm:rounded-2xl max-sm:border-x-0"
          : showThread
            ? composerFocused
              ? "min-h-[min(92dvh,52rem)] max-h-[min(96dvh,56rem)]"
              : "min-h-[min(72vh,40rem)] max-h-[min(85vh,48rem)]"
            : ""
      }`}
      aria-label={`${ASSISTANT_NAME} — поручения`}
    >
      <header
        className={`flex shrink-0 items-center justify-between border-b border-white/5 transition-all duration-300 ${
          isPublic
            ? "px-3 py-2 sm:px-6"
            : showThread
              ? composerFocused
                ? "px-3 py-2 sm:px-6"
                : "px-4 py-3 sm:px-6"
              : "px-5 py-4 sm:px-8"
        }`}
      >
        {showThread && !isPublic ? (
          <button
            type="button"
            onClick={() => setChatCollapsed(true)}
            className={`rounded-lg px-2 py-1 text-sm text-genesis-muted transition hover:bg-white/5 hover:text-white ${
              composerFocused ? "max-sm:hidden" : ""
            }`}
          >
            {t("back")}
          </button>
        ) : !isPublic ? (
          <button
            type="button"
            onClick={() => void handleNewChat()}
            className="rounded-lg px-2 py-1 text-sm text-genesis-muted transition hover:bg-white/5 hover:text-white"
          >
            + {t("newChat")}
          </button>
        ) : (
          <div className="flex min-w-0 flex-1 items-center gap-1 sm:gap-1.5">
            <button
              type="button"
              onClick={() => setSidebarOpen((o) => !o)}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-genesis-muted transition hover:bg-white/5 hover:text-white sm:hidden"
              aria-label="Меню"
              aria-expanded={sidebarOpen}
            >
              ☰
            </button>
          </div>
        )}
        {isPublic || !showThread ? (
          <div className="flex min-w-0 flex-col items-center">
            <VectorBrandSignature
              variant="compact"
              className={composerFocused ? "max-sm:scale-90 max-sm:origin-center" : undefined}
              onClick={isPublic && hasConversation ? handlePublicHome : undefined}
              homeLabel={t("backHome")}
            />
          </div>
        ) : (
          <Badge variant="accent" className="tracking-[0.25em]">
            {ASSISTANT_NAME}
          </Badge>
        )}
        <div className="flex items-center gap-2">
          {isPublic ? (
            <button
              type="button"
              onClick={() => void handleNewChat()}
              className="flex h-10 w-10 items-center justify-center rounded-lg text-lg text-genesis-muted transition hover:bg-white/5 hover:text-white sm:hidden"
              aria-label={t("newChat")}
            >
              +
            </button>
          ) : null}
          {!isPublic && <LanguageSwitcher />}
          {devAvailable && !isPublic ? (
            <button
              type="button"
              onClick={toggleDeveloperMode}
              title="Dev Mode — Thinking Brief (только разработка)"
              className={`rounded-lg px-2 py-1 text-[10px] font-semibold uppercase tracking-wider transition ${
                developerMode
                  ? "bg-amber-500/20 text-amber-300 ring-1 ring-amber-400/40"
                  : "text-genesis-muted hover:bg-white/5 hover:text-white"
              }`}
            >
              Dev {developerMode ? "ON" : "OFF"}
            </button>
          ) : (
            <span className="w-14" />
          )}
        </div>
      </header>

      {!showThread && !isPublic && (
        <div className="shrink-0 px-5 py-4 sm:px-8">
          <SpringIn className="rounded-2xl border border-white/5 bg-genesis-panel/50 px-5 py-5 text-[15px] leading-relaxed whitespace-pre-wrap text-genesis-text backdrop-blur-sm">
            <VectorBrandSignature variant="full" className="mb-2" />
            {welcomeText}
          </SpringIn>
        </div>
      )}

      {isPublic && !hasConversation && !hubMode && (
        <div className="shrink-0 border-b border-white/5 px-4 py-4 sm:px-6">
          <div className="mx-auto w-full max-w-3xl rounded-2xl border border-dashed border-genesis-accent/25 bg-genesis-panel/40 px-4 py-4 sm:px-5 sm:py-5">
            <p className="text-[10px] font-bold tracking-[0.22em] text-genesis-accent uppercase">
              {t("workspaceTitle")}
            </p>
            <p className="mt-2 text-sm font-medium text-white">{t("workspaceEmpty")}</p>
            <p className="mt-1 text-sm text-genesis-muted">{t("workspaceEmptyHint")}</p>
          </div>
        </div>
      )}

      <div className={`relative min-h-0 flex-1 ${showThread ? "" : "max-h-0"}`}>
        <div
          ref={messagesRef}
          onScroll={handleScroll}
          className={`h-full min-h-0 overflow-y-auto overscroll-contain px-4 transition-all duration-300 sm:px-6 ${
            showThread ? "py-3 pb-4 opacity-100 sm:py-4" : "max-h-0 py-0 opacity-0"
          }`}
        >
          <ul className="mx-auto w-full max-w-3xl space-y-3 sm:space-y-4">
          {thread.map((m, i) => {
            const isWelcomeBubble = i === 0 && m.role === "assistant" && !hasConversation;
            return (
            <ChatMessageSpring
              key={`${m.role}-${i}`}
              role={m.role}
              contentKey={m.generating ? `gen-${i}` : `${i}-${m.text?.length ?? 0}`}
            >
              <div
                className={`whitespace-pre-wrap ${
                  isWelcomeBubble
                    ? "px-1 py-1 text-[15px] leading-snug text-genesis-muted"
                    : `rounded-3xl px-4 py-3 text-[15px] leading-relaxed ${
                        m.role === "user"
                          ? "bg-genesis-accent/20 text-white"
                          : "border border-white/5 bg-genesis-panel/60 text-genesis-text backdrop-blur-sm"
                      }`
                }`}
              >
                {m.role === "assistant" && !isWelcomeBubble && (
                  <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-genesis-accent">
                    {assistantLabel}
                  </p>
                )}
                {m.generating && !m.text?.trim() ? (
                  <span className="inline-flex items-center gap-1 text-genesis-muted">
                    <span className="animate-pulse">●</span>
                    <span className="animate-pulse [animation-delay:150ms]">●</span>
                    <span className="animate-pulse [animation-delay:300ms]">●</span>
                  </span>
                ) : m.role === "assistant" && m.provider === "execution" ? (
                  <ExecutionResultPanel
                    text={m.text}
                    ctas={
                      m.cta_actions && m.cta_actions.length > 0
                        ? m.cta_actions
                        : m.cta_href && m.cta_label
                          ? [{ href: m.cta_href, label: m.cta_label }]
                          : []
                    }
                    onQuickAction={(msg) => void sendMessage(msg)}
                  />
                ) : (
                  m.text
                )}
                {(m.attachments ?? []).map((a) =>
                  a?.previewUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      key={a.id}
                      src={a.previewUrl}
                      alt={a.filename ?? ""}
                      className="mt-2 max-h-40 rounded-xl border border-white/10 object-cover"
                    />
                  ) : null,
                )}
                {m.role === "assistant" && m.provider !== "execution"
                  ? (m.cta_actions && m.cta_actions.length > 0
                      ? m.cta_actions
                      : m.cta_href && m.cta_label
                        ? [{ href: m.cta_href, label: m.cta_label }]
                        : []
                    ).map((cta) => (
                      <Link
                        key={`${cta.href}-${cta.label}`}
                        href={cta.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-3 mr-2 inline-block rounded-xl bg-gradient-to-r from-genesis-accent to-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:opacity-90"
                      >
                        {cta.label}
                      </Link>
                    ))
                  : null}
                {m.role === "assistant" && developerMode && m.debug && i > 0 ? (
                  <div className="mt-3 border-t border-white/10 pt-2">
                    <button
                      type="button"
                      onClick={() => setOpenDebugIndex(openDebugIndex === i ? null : i)}
                      className="text-left text-xs font-medium text-amber-300/90 hover:text-amber-200 hover:underline"
                    >
                      {openDebugIndex === i
                        ? "Скрыть Thinking Brief"
                        : `Почему ${ASSISTANT_NAME} ответил именно так?`}
                    </button>
                    {openDebugIndex === i ? (
                      <div className="mt-2 max-h-96 overflow-y-auto rounded-xl border border-amber-500/20 bg-black/30 p-3 text-[11px] leading-relaxed text-amber-100/90">
                        {m.debug.local_fallback_warning ? (
                          <p className="mb-3 rounded-lg border border-rose-500/50 bg-rose-950/40 px-3 py-2 font-semibold text-rose-300">
                            {m.debug.local_fallback_warning}
                            {m.debug.answer_source
                              ? ` (source: ${m.debug.answer_source})`
                              : ""}
                          </p>
                        ) : null}
                        {m.debug.current_employee ? (
                          <p className="mb-2 text-[10px] text-emerald-200/90">
                            Employee: {m.debug.current_employee}
                            {m.debug.current_model ? ` · model: ${m.debug.current_model}` : ""}
                            {m.debug.current_provider
                              ? ` · provider: ${m.debug.current_provider}`
                              : ""}
                          </p>
                        ) : null}
                        {m.debug.conversation_pipeline?.length ? (
                          <div className="mb-3 flex flex-wrap gap-1">
                            {m.debug.conversation_pipeline.map((s) => (
                              <span
                                key={s.step}
                                className="rounded bg-white/10 px-1.5 py-0.5 text-[9px] uppercase tracking-wide"
                              >
                                {s.step} → {s.status}
                              </span>
                            ))}
                          </div>
                        ) : null}
                        {m.debug.runtime_pipeline ? (
                          <div className="mb-3 space-y-2 border-b border-white/10 pb-2">
                            <p className="font-semibold text-amber-200">Runtime Pipeline</p>
                            <p className="text-[10px] text-amber-100/70">
                              Employee: {m.debug.runtime_pipeline.employee_chosen} —{" "}
                              {m.debug.runtime_pipeline.employee_why}
                            </p>
                            {m.debug.runtime_pipeline.employee_diagnostics?.map((d) => (
                              <p key={d.employee_id} className="text-[9px] text-amber-100/60">
                                {d.callable ? "✓" : "✗"} {d.employee_id}: {d.code} — {d.reason}
                              </p>
                            ))}
                            {m.debug.runtime_pipeline.fallback_started_at ? (
                              <p className="text-[9px] text-rose-300/90">
                                Fallback at: {m.debug.runtime_pipeline.fallback_started_at}
                              </p>
                            ) : null}
                            {m.debug.runtime_pipeline.raw_response ? (
                              <details className="text-[9px]">
                                <summary className="cursor-pointer text-amber-300/80">
                                  Raw LLM response
                                </summary>
                                <pre className="mt-1 whitespace-pre-wrap text-amber-50/70">
                                  {m.debug.runtime_pipeline.raw_response.slice(0, 1200)}
                                </pre>
                              </details>
                            ) : null}
                          </div>
                        ) : null}
                        {m.debug.executive_decision ? (
                          <p className="mb-2 text-genesis-muted">
                            Executive: {m.debug.executive_decision.action} (
                            {(m.debug.executive_decision.confidence ?? 0).toFixed(2)})
                            {m.debug.calibration?.needs_rewrite
                              ? " · calibration переписал ответ"
                              : ""}
                            {m.debug.provider ? ` · ${m.debug.provider}` : ""}
                          </p>
                        ) : null}
                        <pre className="whitespace-pre-wrap font-mono text-[10px] text-amber-50/80">
                          {m.debug.thinking_brief_text ??
                            JSON.stringify(m.debug.thinking_brief, null, 2)}
                        </pre>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </ChatMessageSpring>
            );
          })}
          {busy && (
            <li className="flex justify-start">
              <div className="rounded-3xl border border-white/5 bg-genesis-panel/60 px-4 py-3 text-sm text-genesis-muted">
                {ASSISTANT_NAME} работает…
              </div>
            </li>
          )}
        </ul>
        </div>
        {showJumpButton && showThread ? (
          <button
            type="button"
            onClick={jumpToLatest}
            className="absolute bottom-4 left-1/2 z-10 -translate-x-1/2 rounded-full border border-white/10 bg-genesis-panel/95 px-4 py-2 text-xs font-medium text-genesis-text shadow-[0_8px_32px_rgba(0,0,0,0.45)] backdrop-blur-xl transition hover:border-genesis-accent/35 hover:text-white"
            aria-label={t("jumpToLatest")}
          >
            ⬇️ {t("jumpToLatest")}
          </button>
        ) : null}
      </div>

      {!hasConversation && showThread && !isPublicHub && (
        <div className="shrink-0 overflow-x-auto px-3 pb-1 sm:px-6">
          <div className="flex w-max max-w-full gap-2 sm:flex-wrap">
          {STARTERS_VISIBLE.map((s) => (
            <button
              key={s.label}
              type="button"
              disabled={busy}
              onClick={() => void sendMessage(s.message)}
              className="shrink-0 rounded-full border border-genesis-border-subtle bg-genesis-bg/50 px-3 py-1.5 text-xs text-genesis-muted transition hover:border-genesis-accent/40 hover:text-white disabled:opacity-40 sm:px-4 sm:py-2"
            >
              {s.label}
            </button>
          ))}
          {!showMoreStarters ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => setShowMoreStarters(true)}
              className="shrink-0 rounded-full border border-dashed border-genesis-border-subtle px-3 py-1.5 text-xs text-genesis-muted transition hover:border-genesis-accent/40 hover:text-white disabled:opacity-40 sm:px-4 sm:py-2"
            >
              Ещё
            </button>
          ) : (
            STARTERS_MORE.map((s) => (
              <button
                key={s.label}
                type="button"
                disabled={busy}
                onClick={() => void sendMessage(s.message)}
                className="shrink-0 rounded-full border border-genesis-border-subtle bg-genesis-bg/50 px-3 py-1.5 text-xs text-genesis-muted transition hover:border-genesis-accent/40 hover:text-white disabled:opacity-40 sm:px-4 sm:py-2"
              >
                {s.label}
              </button>
            ))
          )}
          </div>
        </div>
      )}

      <footer
        className="shrink-0 border-t border-white/5 px-1 pb-1 pt-2 sm:px-2"
      >
        {composer}
      </footer>
    </section>
    </div>
  );
}
