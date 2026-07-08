"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Badge } from "./ui/Badge";
import { Button } from "./ui";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const OPENAI_MODELS = [
  { id: "gpt-4o-mini", label: "GPT-4o mini" },
  { id: "gpt-4o", label: "GPT-4o" },
  { id: "gpt-4.1-mini", label: "GPT-4.1 mini" },
];

type EmployeeRow = {
  id: string;
  label: string;
  status: string;
  premium?: boolean;
  core?: boolean;
  tier?: string;
  roles?: string[];
  quota_remaining?: number;
  quota_limit?: number;
};

type SetupStatus = {
  genesis_ready?: boolean;
  employees?: EmployeeRow[];
  owner_setup_complete?: boolean;
  setup_once_hint?: string;
  workforce_director?: {
    failover_chain?: string[];
    chain_status?: Array<{
      employee_id?: string;
      remaining?: number;
      limit?: number;
      has_budget?: boolean;
    }>;
    policy?: string;
  };
};

const TIER_BADGE: Record<string, string> = {
  free: "Free",
  local: "Local",
  optional: "Optional",
  core: "Core",
};

const ACTION_LABEL: Record<string, string> = {
  groq: "Connect",
  gemini: "Connect",
  openrouter: "Connect",
  openai: "Connect",
  ollama: "Start",
};

type Props = {
  onComplete?: () => void;
  embedded?: boolean;
};

export function GenesisSetupWizard({ onComplete, embedded = false }: Props) {
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [connectingId, setConnectingId] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gpt-4o-mini");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hireNotice, setHireNotice] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/genesis-ai/setup`);
      if (res.ok) {
        setStatus(await res.json());
      }
    } catch {
      /* backend offline */
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  const beginConnect = (id: string) => {
    setConnectingId(id);
    setApiKey("");
    setError(null);
    setHireNotice(null);
  };

  const cancelConnect = () => {
    setConnectingId(null);
    setApiKey("");
    setError(null);
  };

  const submit = useCallback(async () => {
    if (!connectingId) return;
    setBusy(true);
    setError(null);
    try {
      const body: Record<string, string> = { provider: connectingId };
      if (connectingId !== "ollama") {
        const key = apiKey.trim();
        if (key.length < 8) {
          setError("Введите корректный API-ключ (минимум 8 символов).");
          return;
        }
        body.api_key = key;
      }
      if (connectingId === "openai") {
        body.model = model;
      }
      const res = await fetch(`${API}/api/owner/genesis-ai/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data?.detail;
        setError(
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((d: { msg?: string }) => d.msg).join(", ")
              : "Не удалось нанять сотрудника.",
        );
        return;
      }
      setApiKey("");
      setConnectingId(null);
      setHireNotice(data.message ?? "Сотрудник принят в штат.");
      setStatus((prev) => ({
        ...prev,
        employees: data.employees ?? prev?.employees,
      }));
      await loadStatus();
      onComplete?.();
    } catch {
      setError("Backend недоступен. Запустите сервер на порту 8000.");
    } finally {
      setBusy(false);
    }
  }, [apiKey, connectingId, loadStatus, model, onComplete]);

  const shell = embedded
    ? "w-full"
    : "mx-auto w-full max-w-lg overflow-hidden rounded-3xl border border-genesis-accent/25 bg-gradient-to-b from-indigo-950/40 via-genesis-panel to-genesis-bg shadow-glow";

  const employees = status?.employees ?? [];
  const core = employees.find((e) => e.core || e.id === "genesis-local");
  const hireable = employees.filter((e) => !e.core && e.id !== "genesis-local");

  return (
    <section className={shell} aria-label="Virtus Core Owner Setup">
      <div className="border-b border-white/5 px-6 py-5 sm:px-8">
        <Badge variant="accent" className="tracking-[0.25em]">
          Owner
        </Badge>
        <h1 className="mt-3 text-2xl font-bold sm:text-3xl">Панель директора</h1>
        <p className="mt-2 text-sm text-genesis-muted">
          Virtus Core уже работает. Здесь вы нанимаете дополнительных сотрудников.
        </p>
      </div>

      <div className="space-y-5 px-6 py-6 sm:px-8">
        <div className="rounded-2xl border border-indigo-400/20 bg-indigo-950/25 px-4 py-3 text-sm leading-relaxed text-indigo-100/90">
          <strong className="text-indigo-200">Workforce Director.</strong>{" "}
          {status?.setup_once_hint ??
            "Подключите бесплатных сотрудников один раз — Virtus Core сам переключается при лимитах."}
          {status?.owner_setup_complete ? (
            <span className="mt-1 block text-emerald-300/90">
              Настройка активна — Director управляет моделями автоматически.
            </span>
          ) : null}
        </div>

        <Link href="/site" className="block">
          <Button type="button" size="lg" className="w-full">
            Continue with Virtus Local
          </Button>
        </Link>

        {hireNotice ? (
          <p className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 px-4 py-2.5 text-sm text-emerald-200">
            {hireNotice}
          </p>
        ) : null}

        {/* Core — always ready, cannot disconnect */}
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/15 px-4 py-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-white">
                {core?.label ?? "Virtus Local"}
              </p>
              <p className="mt-0.5 text-xs text-emerald-300/90">✅ Ready · Core Brain</p>
            </div>
            <span className="shrink-0 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-emerald-300">
              Active
            </span>
          </div>
          <ul className="mt-3 space-y-1 text-[11px] text-genesis-muted">
            {(core?.roles ?? [
              "Core Brain",
              "Memory",
              "Executive Mind",
              "Thinking Engine",
              "Offline reasoning",
            ]).map((role) => (
              <li key={role} className="flex gap-2">
                <span className="text-emerald-400/80">·</span>
                {role}
              </li>
            ))}
          </ul>
        </div>

        {/* Workforce — hire, not choose-one */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-genesis-accent">
            AI Workforce — Director
          </p>
          {status?.workforce_director?.failover_chain ? (
            <p className="mt-1 text-[10px] text-genesis-muted">
              Failover: {status.workforce_director.failover_chain.join(" → ")}
            </p>
          ) : null}
          <ul className="mt-3 space-y-2">
            {hireable.map((e) => {
              const isReady = e.status === "ready";
              const tier = TIER_BADGE[e.tier ?? ""] ?? (e.premium ? "Optional" : "Free");
              const action = ACTION_LABEL[e.id] ?? "Connect";
              const isConnecting = connectingId === e.id;

              return (
                <li
                  key={e.id}
                  className="rounded-xl border border-white/10 bg-genesis-bg/30 px-4 py-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white">{e.label}</p>
                      <p className="mt-0.5 text-xs text-genesis-muted">
                        {isReady ? "✅ Ready" : `○ ${tier}`}
                        {e.quota_limit && e.quota_limit > 0 && isReady
                          ? ` · осталось ${e.quota_remaining ?? 0}`
                          : ""}
                      </p>
                    </div>
                    {!isReady && !isConnecting ? (
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => beginConnect(e.id)}
                      >
                        {action}
                      </Button>
                    ) : isReady ? (
                      <span className="text-xs text-emerald-400">В штате</span>
                    ) : null}
                  </div>

                  {isConnecting ? (
                    <div className="mt-3 border-t border-white/10 pt-3">
                      {e.id === "ollama" ? (
                        <p className="text-xs text-genesis-muted">
                          Запустите <code className="text-[11px]">ollama serve</code> и загрузите
                          модель. Нажмите Start — Virtus Core проверит подключение.
                        </p>
                      ) : (
                        <label className="block text-xs font-medium text-genesis-text">
                          API Key — {e.label}
                          <input
                            type="password"
                            autoComplete="off"
                            value={apiKey}
                            onChange={(ev) => setApiKey(ev.target.value)}
                            placeholder="вставьте ключ"
                            className="mt-2 w-full rounded-lg border border-white/10 bg-genesis-bg/80 px-3 py-2 text-sm text-white placeholder:text-genesis-muted/50 focus:border-genesis-accent/50 focus:outline-none"
                          />
                        </label>
                      )}
                      {e.id === "openai" ? (
                        <label className="mt-2 block text-xs font-medium text-genesis-text">
                          Модель
                          <select
                            value={model}
                            onChange={(ev) => setModel(ev.target.value)}
                            className="mt-1 w-full rounded-lg border border-white/10 bg-genesis-bg/80 px-3 py-2 text-sm text-white focus:border-genesis-accent/50 focus:outline-none"
                          >
                            {OPENAI_MODELS.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.label}
                              </option>
                            ))}
                          </select>
                        </label>
                      ) : null}
                      {error ? (
                        <p className="mt-2 text-xs text-rose-300">{error}</p>
                      ) : null}
                      <div className="mt-3 flex gap-2">
                        <Button type="button" variant="secondary" size="sm" onClick={cancelConnect}>
                          Отмена
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          className="flex-1"
                          disabled={busy || (e.id !== "ollama" && !apiKey.trim())}
                          onClick={() => void submit()}
                        >
                          {busy ? "Проверяем…" : action}
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>

        <p className="text-center text-[11px] text-genesis-muted">
          Посетители сайта видят только Vector — не сотрудников и не API.
        </p>
      </div>
    </section>
  );
}
