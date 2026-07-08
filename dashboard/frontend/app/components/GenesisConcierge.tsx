"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Badge } from "./ui/Badge";
import {
  GenesisChatComposer,
  type PendingAttachment,
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
  loadVoiceSettings,
  type VoiceSettings,
} from "../lib/voiceSettings";
import { ChatHistorySidebar } from "./ChatHistorySidebar";
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

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const VISITOR_KEY = "genesis_visitor_id";
const OWNER_VISITOR_KEY = "genesis_owner_visitor_id";
const HI_BUILD_KEY = "genesis_hi_build";
const HI_BUILD_EXPECTED = "genesis-mind-v3.0";
const DEV_MODE_KEY = "genesis_developer_mode";

function devModeAvailable(): boolean {
  if (process.env.NEXT_PUBLIC_GENESIS_DEV_MODE === "1") return true;
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1";
}

function getVisitorId(scope: "public" | "owner"): string {
  if (typeof window === "undefined") return "anonymous";
  const key = scope === "owner" ? OWNER_VISITOR_KEY : VISITOR_KEY;
  try {
    let id = localStorage.getItem(key);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(key, id);
    }
    return id;
  } catch {
    return "anonymous";
  }
}

type Message = {
  role: "user" | "assistant";
  text: string;
  cta_href?: string | null;
  cta_label?: string | null;
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
  cta_href?: string | null;
  cta_label?: string | null;
  debug?: GenesisDebug | null;
};

const STARTERS_VISIBLE = [
  { label: "💇 Сайт салона", message: "Хочу сайт для салона красоты" },
  { label: "🍽️ Сайт кафе", message: "Мне нужен сайт для кафе" },
  { label: "✨ Genesis Studio", message: "Хочу попробовать Genesis Studio" },
];

const STARTERS_MORE = [
  { label: "🏪 Интернет-магазин", message: "Мне нужен интернет-магазин" },
  { label: "🚗 Автосервис", message: "Мне нужен сайт для автосервиса" },
  { label: "✈️ Telegram-бот", message: "Мне нужен Telegram-бот для бизнеса" },
  { label: "🤖 AI на сайте", message: "Хочу AI-консультанта на сайте" },
];

const FALLBACK_WELCOME =
  "Добро пожаловать в Genesis.\n\n" +
  "Можем поговорить, обсудить идею, науку, бизнес — или создать сайт и автоматизацию.\n\n" +
  "С чего начнём?";

type Props = {
  onConversationActive?: (active: boolean) => void;
  /** public = /site visitors; owner = Mission Control / CEO chat */
  scope?: "public" | "owner";
};

export function GenesisConcierge({ onConversationActive, scope = "public" }: Props) {
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [welcomeText, setWelcomeText] = useState(FALLBACK_WELCOME);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: FALLBACK_WELCOME },
  ]);
  const [chatCollapsed, setChatCollapsed] = useState(true);
  const [pendingFiles, setPendingFiles] = useState<PendingAttachment[]>([]);
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceThinking, setVoiceThinking] = useState(false);
  const [voiceSpeaking, setVoiceSpeaking] = useState(false);
  const [voiceHint, setVoiceHint] = useState<string | undefined>();
  const [micNotice, setMicNotice] = useState<string | undefined>();
  const [micPermissionModal, setMicPermissionModal] = useState(false);
  const [showMoreStarters, setShowMoreStarters] = useState(false);
  const [voiceSettingsOpen, setVoiceSettingsOpen] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>(() => loadVoiceSettings());
  const [ttsCloudAvailable, setTtsCloudAvailable] = useState(false);
  const [ttsPreferred, setTtsPreferred] = useState<string>("browser");
  const [developerMode, setDeveloperMode] = useState(false);
  const [openDebugIndex, setOpenDebugIndex] = useState<number | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionList, setSessionList] = useState<ChatSessionMeta[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const devAvailable = devModeAvailable();
  const visitorId = getVisitorId(scope);

  const voiceSettingsRef = useRef(voiceSettings);

  const messagesRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const lastInputWasVoiceRef = useRef(false);
  const voiceContinuousRef = useRef(false);
  const startVoiceRef = useRef<(() => Promise<void>) | null>(null);
  const hydratedRef = useRef(false);

  useEffect(() => {
    voiceSettingsRef.current = voiceSettings;
  }, [voiceSettings]);

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
  const showThread = hasConversation && !chatCollapsed;

  const scrollToBottom = useCallback(() => {
    const el = messagesRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, []);

  useEffect(() => {
    onConversationActive?.(showThread);
  }, [showThread, onConversationActive]);

  useEffect(() => {
    if (!showThread) return;
    const id = requestAnimationFrame(scrollToBottom);
    return () => cancelAnimationFrame(id);
  }, [messages, busy, showThread, scrollToBottom]);

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
        if (g) setWelcomeText(g);
      })
      .catch(() => undefined);
  }, [visitorId]);

  const resetToWelcome = useCallback(
    (greeting?: string) => {
      const text = greeting?.trim() || welcomeText || FALLBACK_WELCOME;
      setMessages([{ role: "assistant", text }]);
      setChatCollapsed(true);
      setActiveSessionId(null);
      const store = loadSessionsStore(scope);
      store.activeSessionId = null;
      saveSessionsStore(scope, store);
    },
    [scope, welcomeText],
  );

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
    setMessages([{ role: "assistant", text: welcomeText || FALLBACK_WELCOME }]);
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
        setMessages([{ role: "assistant", text: welcomeText || FALLBACK_WELCOME }]);
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
    const home = () => {
      setChatCollapsed(true);
      document.getElementById("genesis-chat")?.scrollIntoView({ behavior: "smooth" });
    };
    window.addEventListener("genesis:home", home);
    return () => window.removeEventListener("genesis:home", home);
  }, []);

  const uploadFiles = useCallback(async (files: FileList | null) => {
    if (!files?.length) return;
    const next: PendingAttachment[] = [];
    for (const file of Array.from(files)) {
      const form = new FormData();
      form.append("file", file);
      try {
        const res = await fetch(`${API}/api/public/genesis-ai/attachments`, {
          method: "POST",
          body: form,
        });
        if (!res.ok) continue;
        const data = (await res.json()) as Partial<PendingAttachment> & { id?: string };
        if (!data?.id) continue;
        const previewUrl = data.is_image ? URL.createObjectURL(file) : null;
        next.push({
          id: data.id,
          filename: data.filename ?? file.name,
          content_type: data.content_type ?? file.type,
          is_image: Boolean(data.is_image),
          previewUrl,
        });
      } catch {
        /* backend offline — skip */
      }
    }
    if (next.length) setPendingFiles((prev) => [...prev, ...next]);
  }, []);

  const removeAttachment = useCallback((id: string) => {
    setPendingFiles((prev) => {
      const item = prev.find((p) => p.id === id);
      if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl);
      return prev.filter((p) => p.id !== id);
    });
  }, []);

  const sendMessage = useCallback(
    async (text: string, files: PendingAttachment[] = [], fromVoice = false) => {
      const q = text.trim();
      if ((!q && !files.length) || busy) return;

      if (isInterruptPhrase(q) && (voiceSpeaking || isSpeaking())) {
        interruptSpeechIfNeeded();
        return;
      }

      if (fromVoice) lastInputWasVoiceRef.current = true;
      setChatCollapsed(false);

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

      const displayText =
        q || (files.length === 1 ? `📎 ${files[0]?.filename ?? "файл"}` : `📎 ${files.length} файла`);

      const sentFiles = files.map((f) => ({ ...f }));

      const history = messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .slice(1)
        .slice(-12)
        .map((m) => ({ role: m.role, content: m.text ?? "" }));

      const nextUserMsg: Message = {
        role: "user",
        text: displayText,
        attachments: sentFiles.length ? sentFiles : undefined,
      };
      setMessages((prev) => [...prev, nextUserMsg]);
      setInput("");
      setPendingFiles([]);
      setBusy(true);
      if (fromVoice) setVoiceThinking(true);

      try {
        const endpoint = `${API}/api/public/genesis-ai${developerMode ? "?debug=true" : ""}`;
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: q || "Клиент прикрепил файлы — помогите понять задачу.",
            history,
            visitor_id: visitorId,
            session_id: sessionId,
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
          data?.answer?.trim() ||
          "Сейчас не получилось сформировать ответ. Попробуйте переформулировать — я здесь.";

        setMessages((prev) => {
          const next = [
            ...prev,
            {
              role: "assistant" as const,
              text: answer,
              cta_href: data?.cta_href ?? null,
              cta_label: data?.cta_label ?? null,
              debug: developerMode ? (data?.debug ?? null) : undefined,
            },
          ];
          const sid = (data as { session_id?: string })?.session_id || sessionId;
          if (sid) persistLocalMessages(sid, next);
          return next;
        });
        void refreshSessionList();

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
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text:
              "Сейчас я не могу ответить — похоже, нет связи с Genesis.\n\n" +
              "Попробуйте обновить страницу через минуту или напишите ещё раз.",
          },
        ]);
      } finally {
        setBusy(false);
        if (!lastInputWasVoiceRef.current) setVoiceThinking(false);
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
    ],
  );

  const MIC_GRANTED_KEY = "genesis_mic_granted";

  const releaseMicStream = useCallback(() => {
    mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
    mediaStreamRef.current = null;
  }, []);

  const stopVoice = useCallback(() => {
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

  const interruptSpeechIfNeeded = useCallback(() => {
    stopSpeaking();
    stopInterruptListener();
    setVoiceSpeaking(false);
  }, []);

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

    setVoiceHint("Слушаю…");

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
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      rec.onstart = () => {
        console.info("[Genesis] speech recognition started");
        setVoiceListening(true);
        setVoiceHint("Слушаю… говорите свободно");
      };
      rec.onresult = (event: SpeechRecognitionEvent) => {
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
          setVoiceListening(false);
          setVoiceHint("Не расслышал — нажмите микрофон и говорите чуть громче.");
          return;
        }
        setVoiceListening(false);
        setVoiceHint(undefined);
        failMic("Не получилось распознать речь. Попробуйте ещё раз.");
      };
      rec.onend = () => {
        console.info("[Genesis] speech recognition ended");
        setVoiceListening(false);
      };
      recognitionRef.current = rec;
      rec.start();
    } catch (err) {
      failMic("Не удалось запустить распознавание речи.", err);
    }
  }, [failMic, sendMessage, stopVoice]);

  startVoiceRef.current = startVoice;

  const toggleVoice = useCallback(async () => {
    if (voiceListening) {
      voiceContinuousRef.current = false;
      stopVoice();
      return;
    }
    interruptSpeechIfNeeded();
    voiceContinuousRef.current = !voiceSettingsRef.current.pushToTalk;
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

  useEffect(() => {
    const focus = () => {
      document.getElementById("genesis-chat-input")?.focus();
    };
    const voice = () => {
      /* Must stay tied to user gesture — do not dispatch genesis:start-voice on mount */
      void toggleVoice();
    };
    window.addEventListener("genesis:focus-chat", focus);
    window.addEventListener("genesis:start-voice", voice);
    return () => {
      window.removeEventListener("genesis:focus-chat", focus);
      window.removeEventListener("genesis:start-voice", voice);
    };
  }, [toggleVoice]);

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
      <GenesisChatComposer
        value={input}
        onChange={setInput}
        onSend={() => void sendMessage(input, pendingFiles)}
        busy={busy}
        attachments={pendingFiles ?? []}
        onPickFiles={(files) => void uploadFiles(files)}
        onRemoveAttachment={removeAttachment}
        onToggleVoice={() => void toggleVoice()}
        onRetryVoice={() => {
          setMicNotice(undefined);
          void startVoice();
        }}
        voiceListening={voiceListening}
        voiceThinking={voiceThinking || (busy && lastInputWasVoiceRef.current)}
        voiceSpeaking={voiceSpeaking}
        micPermissionModal={micPermissionModal}
        onConfirmMicPermission={confirmMicPermission}
        onCancelMicPermission={() => setMicPermissionModal(false)}
        voiceHint={voiceHint}
        micNotice={micNotice}
        onDismissMicNotice={() => setMicNotice(undefined)}
        onOpenVoiceSettings={() => setVoiceSettingsOpen((o) => !o)}
        voiceSettingsOpen={voiceSettingsOpen}
        inputId="genesis-chat-input"
      />
    </>
  );

  const thread = messages ?? [];

  return (
    <div className="flex flex-col gap-2 md:flex-row md:items-stretch">
      <ChatHistorySidebar
        sessions={sessionList}
        activeSessionId={activeSessionId}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        onNewChat={() => void handleNewChat()}
        onSelect={(id) => void handleSelectSession(id)}
        onDelete={(id) => void handleDeleteSession(id)}
        onPin={(id, pinned) => void handlePinSession(id, pinned)}
      />
    <section
      id="genesis-chat"
      className={`flex min-w-0 flex-1 flex-col overflow-hidden rounded-3xl border border-genesis-accent/25 bg-gradient-to-b from-indigo-950/40 via-genesis-panel to-genesis-bg shadow-glow transition-all duration-300 ${
        showThread ? "min-h-[min(72vh,40rem)] max-h-[min(85vh,48rem)]" : ""
      }`}
      aria-label="Диалог с Genesis"
    >
      <header
        className={`flex shrink-0 items-center justify-between border-b border-white/5 transition-all duration-300 ${
          showThread ? "px-4 py-3 sm:px-6" : "px-5 py-4 sm:px-8"
        }`}
      >
        {showThread ? (
          <button
            type="button"
            onClick={() => setChatCollapsed(true)}
            className="rounded-lg px-2 py-1 text-sm text-genesis-muted transition hover:bg-white/5 hover:text-white"
          >
            ← Назад
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void handleNewChat()}
            className="rounded-lg px-2 py-1 text-sm text-genesis-muted transition hover:bg-white/5 hover:text-white"
          >
            + Новый
          </button>
        )}
        <Badge variant="accent" className="tracking-[0.25em]">
          Genesis
        </Badge>
        {devAvailable ? (
          <button
            type="button"
            onClick={toggleDeveloperMode}
            title="Genesis Developer Mode — Thinking Brief только для разработки"
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
      </header>

      {!showThread && (
        <div className="shrink-0 px-5 py-4 sm:px-8">
          <div className="rounded-2xl border border-white/5 bg-genesis-panel/50 px-5 py-5 text-[15px] leading-relaxed whitespace-pre-wrap text-genesis-text">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-genesis-accent">
              Genesis
            </p>
            {welcomeText}
          </div>
        </div>
      )}

      <div
        ref={messagesRef}
        className={`min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 transition-all duration-300 sm:px-6 ${
          showThread ? "py-4 opacity-100" : "max-h-0 py-0 opacity-0"
        }`}
      >
        <ul className="mx-auto w-full max-w-3xl space-y-4">
          {thread.map((m, i) => (
            <li
              key={`${m.role}-${i}`}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[min(92%,36rem)] rounded-3xl px-4 py-3 text-[15px] leading-relaxed whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-genesis-accent/20 text-white"
                    : "border border-white/5 bg-genesis-panel/60 text-genesis-text"
                }`}
              >
                {m.role === "assistant" && (
                  <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-genesis-accent">
                    Genesis
                  </p>
                )}
                {m.text}
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
                {m.cta_href && m.cta_label ? (
                  <Link
                    href={m.cta_href}
                    className="mt-3 inline-block rounded-xl bg-gradient-to-r from-genesis-accent to-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:opacity-90"
                  >
                    {m.cta_label}
                  </Link>
                ) : null}
                {m.role === "assistant" && developerMode && m.debug && i > 0 ? (
                  <div className="mt-3 border-t border-white/10 pt-2">
                    <button
                      type="button"
                      onClick={() => setOpenDebugIndex(openDebugIndex === i ? null : i)}
                      className="text-left text-xs font-medium text-amber-300/90 hover:text-amber-200 hover:underline"
                    >
                      {openDebugIndex === i
                        ? "Скрыть Thinking Brief"
                        : "Почему Genesis ответил именно так?"}
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
            </li>
          ))}
          {busy && (
            <li className="flex justify-start">
              <div className="rounded-3xl border border-white/5 bg-genesis-panel/60 px-4 py-3 text-sm text-genesis-muted">
                Genesis печатает…
              </div>
            </li>
          )}
        </ul>
      </div>

      {!showThread && (
        <div className="flex flex-wrap gap-2 px-5 pb-2 sm:px-8">
          {STARTERS_VISIBLE.map((s) => (
            <button
              key={s.label}
              type="button"
              disabled={busy}
              onClick={() => void sendMessage(s.message)}
              className="rounded-full border border-genesis-border-subtle bg-genesis-bg/50 px-4 py-2 text-xs text-genesis-muted transition hover:border-genesis-accent/40 hover:text-white disabled:opacity-40"
            >
              {s.label}
            </button>
          ))}
          {!showMoreStarters ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => setShowMoreStarters(true)}
              className="rounded-full border border-dashed border-genesis-border-subtle px-4 py-2 text-xs text-genesis-muted transition hover:border-genesis-accent/40 hover:text-white disabled:opacity-40"
            >
              Посмотреть ещё
            </button>
          ) : (
            STARTERS_MORE.map((s) => (
              <button
                key={s.label}
                type="button"
                disabled={busy}
                onClick={() => void sendMessage(s.message)}
                className="rounded-full border border-genesis-border-subtle bg-genesis-bg/50 px-4 py-2 text-xs text-genesis-muted transition hover:border-genesis-accent/40 hover:text-white disabled:opacity-40"
              >
                {s.label}
              </button>
            ))
          )}
        </div>
      )}

      <footer className="shrink-0 border-t border-white/5 px-1 pb-1 pt-2 sm:px-2">
        {composer}
      </footer>
    </section>
    </div>
  );
}

export const GenesisAI = GenesisConcierge;
