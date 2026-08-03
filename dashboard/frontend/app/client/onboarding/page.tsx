"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type WelcomeState = {
  phase?: string;
  question?: string | null;
  message?: string;
  headline?: string;
  done?: boolean;
};

export default function ClientOnboardingPage() {
  const [state, setState] = useState<WelcomeState | null>(null);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!getClientToken()) {
      setError("Войдите в кабинет.");
      return;
    }
    try {
      const res = await fetch(`${API}/api/client/welcome`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || `HTTP ${res.status}`);
      setState(body as WelcomeState);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function advance() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/welcome/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...clientAuthHeaders() },
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || `HTTP ${res.status}`);
      setState(body as WelcomeState);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }

  async function submitAnswer(skip = false) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/welcome/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...clientAuthHeaders() },
        body: JSON.stringify({ answer: skip ? "" : answer, skip }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || `HTTP ${res.status}`);
      setAnswer("");
      setState(body as WelcomeState);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }

  const phase = state?.phase || "greeting";
  const done = phase === "ready" || phase === "done" || Boolean(state?.done);

  return (
    <ClientWorkspaceShell
      title="Профиль компании"
      subtitle="Vector узнаёт ваш бизнес — Factory использует эти данные для сайта."
    >
      {error ? <p className="mb-4 text-sm text-rose-200">{error}</p> : null}
      {!state ? (
        <p className="text-sm text-zinc-500">Загрузка…</p>
      ) : done ? (
        <div className="rounded-2xl border border-emerald-400/25 bg-emerald-950/20 p-6">
          <p className="text-lg font-semibold text-white">
            {state.headline || "Профиль готов."}
          </p>
          <p className="mt-2 text-sm text-zinc-300">
            Дальше — магазин услуг: сайт и бот под ваш бизнес.
          </p>
          <Link
            href="/client/shop"
            className="mt-4 inline-flex rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
          >
            К магазину →
          </Link>
        </div>
      ) : (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
          {state.message ? (
            <p className="whitespace-pre-wrap text-sm text-zinc-200">{state.message}</p>
          ) : null}
          {phase === "greeting" ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void advance()}
              className="mt-4 rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-40"
            >
              Начать настройку
            </button>
          ) : null}
          {phase === "wizard" && state.question ? (
            <div className="mt-4 space-y-3">
              <p className="text-base font-medium text-white">{state.question}</p>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={3}
                className="w-full rounded-xl border border-white/15 bg-black/30 px-3 py-2 text-sm text-white"
                placeholder="Короткий ответ…"
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy || !answer.trim()}
                  onClick={() => void submitAnswer(false)}
                  className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-40"
                >
                  Далее
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void submitAnswer(true)}
                  className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300"
                >
                  Пропустить
                </button>
              </div>
            </div>
          ) : null}
          {phase === "personalized" ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void advance()}
              className="mt-4 rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
            >
              Готово — в магазин
            </button>
          ) : null}
        </div>
      )}
    </ClientWorkspaceShell>
  );
}
