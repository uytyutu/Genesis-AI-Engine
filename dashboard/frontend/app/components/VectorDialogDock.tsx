"use client";

/**
 * Virtus AI dock — project director chat + wizard (extends Vector surface).
 */

import { useCallback, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import {
  loadVectorLearningMode,
  saveVectorLearningMode,
  type VectorAction,
  type VectorDialogPayload,
} from "../lib/vectorSurfaceContext";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { publicApiBase } from "../lib/publicApiBase";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import { COMPANION_TURN_PATH } from "../lib/vectorCompanionContracts";
import { useLocale } from "../context/LocaleContext";

const API = publicApiBase();

type ChatLine = { role: "user" | "assistant"; text: string };
type QuickAction = { id: string; label: string; message?: string; href?: string };

type Props = {
  surface: "store_admin" | "platform" | "website_admin" | "customer";
  orderId?: string;
  dark?: boolean;
  dock?: "right" | "bottom";
  /** Controlled open state (BCC customer companion). */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** Navigate admin shell section (store or website Workspace). */
  onNavigateSection?: (section: string) => void;
  onRefreshSetup?: () => void;
  commerceMode?: string;
  hasStore?: boolean;
};

export function VectorDialogDock({
  surface,
  orderId,
  dark = true,
  dock = "right",
  open: controlledOpen,
  onOpenChange,
  onNavigateSection,
  onRefreshSetup,
  commerceMode,
  hasStore,
}: Props) {
  const { uiLocale } = useLocale();
  const [internalOpen, setInternalOpen] = useState(surface !== "customer");
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : internalOpen;

  const setOpen = useCallback(
    (next: boolean) => {
      if (!isControlled) setInternalOpen(next);
      onOpenChange?.(next);
    },
    [isControlled, onOpenChange],
  );
  const [expanded, setExpanded] = useState(false);
  const [payload, setPayload] = useState<VectorDialogPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [stepId, setStepId] = useState<string | null>(null);
  const [learning, setLearning] = useState<"skip" | "show" | null>(null);
  const [chat, setChat] = useState<ChatLine[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [quick, setQuick] = useState<QuickAction[]>([]);
  const pathname = usePathname();
  const useCompanionRead = surface === "customer";

  const companionTurn = useCallback(
    async (message: string) => {
      const res = await fetch(`${API}${COMPANION_TURN_PATH}`, {
        method: "POST",
        headers: {
          ...clientAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          page_path: pathname || "/client",
          ui_locale: uiLocale,
        }),
      });
      if (!res.ok) return null;
      return (await res.json()) as {
        reply?: string;
        clarify_question?: string | null;
      };
    },
    [pathname, uiLocale],
  );

  useEffect(() => {
    setLearning(loadVectorLearningMode(surface));
  }, [surface]);

  const load = useCallback(async () => {
    if (!getClientToken()) return;
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      if (learning) qs.set("learning_mode", learning);
      if (stepId) qs.set("step_id", stepId);
      let url: string;
      if (surface === "store_admin" && orderId) {
        url = `${API}/api/client/stores/${orderId}/admin/vector/dialog?${qs}`;
      } else {
        qs.set("surface", surface);
        if (orderId) qs.set("order_id", orderId);
        url = `${API}/api/client/vector/dialog?${qs}`;
      }
      const res = await fetch(url, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      if (res.ok) {
        setPayload((await res.json()) as VectorDialogPayload);
      }
      if (useCompanionRead) {
        const body = await companionTurn("__welcome__");
        if (body?.reply) {
          setChat([{ role: "assistant", text: body.reply }]);
        }
        setQuick([
          {
            id: "connected",
            label: "Was ist verbunden?",
            message: "Was ist bei mir gerade verbunden?",
          },
          {
            id: "analytics",
            label: "Analytics?",
            message: "Warum brauche ich Analytics?",
          },
          {
            id: "next",
            label: "Nächster Schritt",
            message: "Was soll ich als Nächstes tun?",
          },
        ]);
      } else {
        // Welcome from Virtus AI orchestrator (store / website admin surfaces)
        const turn = await fetch(`${API}/api/client/virtus-ai/turn`, {
          method: "POST",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: "__welcome__",
            commerce_mode: commerceMode,
            context: { has_store: Boolean(hasStore) },
            products: hasStore
              ? [{ product_type: "website" }, { product_type: "store" }]
              : [{ product_type: "website" }],
          }),
        });
        if (turn.ok) {
          const body = (await turn.json()) as {
            reply?: string;
            quick_actions?: QuickAction[];
          };
          if (body.reply) {
            setChat([{ role: "assistant", text: body.reply }]);
          }
          if (body.quick_actions?.length) setQuick(body.quick_actions);
        }
      }
    } catch {
      /* optional */
    } finally {
      setLoading(false);
    }
  }, [surface, orderId, learning, stepId, commerceMode, hasStore, useCompanionRead, companionTurn]);

  useEffect(() => {
    void load();
  }, [load]);

  const send = async (text: string) => {
    const msg = text.trim();
    if (!msg || busy || !getClientToken()) return;
    setBusy(true);
    setChat((c) => [...c, { role: "user", text: msg }]);
    setDraft("");
    try {
      if (useCompanionRead) {
        const body = await companionTurn(msg);
        if (body?.reply) {
          const text = body.clarify_question
            ? `${body.reply}\n\n${body.clarify_question}`
            : body.reply;
          setChat((c) => [...c, { role: "assistant", text }]);
        } else {
          setChat((c) => [
            ...c,
            {
              role: "assistant",
              text: "Ich kann gerade keine Context-Daten laden. Bitte Seite aktualisieren.",
            },
          ]);
        }
      } else {
        const res = await fetch(`${API}/api/client/virtus-ai/turn`, {
          method: "POST",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: msg,
            commerce_mode: commerceMode,
            context: { has_store: Boolean(hasStore) },
            products: hasStore
              ? [{ product_type: "website" }, { product_type: "store" }]
              : [{ product_type: "website" }],
          }),
        });
        if (res.ok) {
          const body = (await res.json()) as {
            reply?: string;
            quick_actions?: QuickAction[];
            deep_link?: string;
            upsell?: { cta?: { href?: string; label?: string } };
          };
          if (body.reply) {
            setChat((c) => [...c, { role: "assistant", text: body.reply || "" }]);
          }
          if (body.quick_actions?.length) setQuick(body.quick_actions);
        } else {
          setChat((c) => [
            ...c,
            {
              role: "assistant",
              text: "Сейчас не могу связаться с сервером. Обновите страницу или откройте чек-лист на Dashboard.",
            },
          ]);
        }
      }
    } catch {
      setChat((c) => [
        ...c,
        { role: "assistant", text: "Нет связи с backend. Запустите Genesis.exe и повторите." },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const runAction = (action: VectorAction) => {
    if (action.kind === "set_learning" && (action.value === "skip" || action.value === "show")) {
      saveVectorLearningMode(surface, action.value);
      setLearning(action.value);
      setStepId(null);
      if (getClientToken()) {
        void fetch(`${API}/api/client/vector/progress`, {
          method: "POST",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            scope: surface,
            subject_id: orderId || surface,
            learning_mode: action.value,
          }),
        }).catch(() => undefined);
      }
      return;
    }
    if (action.kind === "wizard_goto" && action.step_id) {
      setStepId(action.step_id);
      if (getClientToken()) {
        void fetch(`${API}/api/client/vector/progress`, {
          method: "POST",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            scope: surface,
            subject_id: orderId || surface,
            learning_mode: learning || undefined,
            step_id: action.step_id,
          }),
        }).catch(() => undefined);
      }
      return;
    }
    if (action.kind === "navigate_section" && action.section && onNavigateSection) {
      onNavigateSection(action.section as string);
      onRefreshSetup?.();
      return;
    }
    if (action.kind === "navigate_href" && action.href) {
      window.location.href = action.href;
      return;
    }
    if (action.kind === "coming") {
      return;
    }
  };

  const isBottom = dock === "bottom" || payload?.dock === "bottom";
  const pct = payload?.readiness_pct ?? payload?.setup?.readiness_pct;

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`fixed z-40 flex items-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold shadow-lg transition ${
          isBottom ? "bottom-4 right-4" : "bottom-6 right-4"
        } ${
          dark
            ? "bg-emerald-500/90 text-black hover:bg-emerald-400"
            : "bg-emerald-700 text-white hover:bg-emerald-800"
        }`}
        aria-label={`Open ${ASSISTANT_NAME}`}
      >
        {ASSISTANT_NAME}
        {typeof pct === "number" ? (
          <span className="rounded-full bg-black/15 px-2 py-0.5 text-xs tabular-nums">
            {pct}%
          </span>
        ) : null}
      </button>
    );
  }

  return (
    <aside
      className={`fixed z-40 flex flex-col overflow-hidden border shadow-2xl backdrop-blur-xl ${
        expanded
          ? "inset-3 rounded-2xl sm:inset-6"
          : isBottom
            ? "inset-x-3 bottom-3 max-h-[48vh] rounded-2xl sm:inset-x-auto sm:right-4 sm:w-[24rem]"
            : "bottom-3 right-3 top-auto h-[min(40rem,82vh)] w-[min(24rem,calc(100vw-1.5rem))] rounded-2xl sm:bottom-4 sm:right-4"
      } ${
        dark
          ? "border-white/10 bg-[#0c0c12]/95 text-zinc-100"
          : "border-slate-200 bg-white/95 text-slate-900"
      }`}
      data-vector-surface={surface}
      aria-label={`${ASSISTANT_NAME} dialog`}
    >
      <header
        className={`flex items-center gap-2 border-b px-3 py-2.5 ${
          dark ? "border-white/10" : "border-slate-200"
        }`}
      >
        <div className="min-w-0 flex-1">
          <p
            className={`text-[10px] font-semibold uppercase tracking-[0.18em] ${
              dark ? "text-emerald-300/80" : "text-emerald-800"
            }`}
          >
            {ASSISTANT_NAME}
          </p>
          <p className={`truncate text-xs ${dark ? "text-zinc-500" : "text-slate-500"}`}>
            Цифровой директор проекта
            {typeof pct === "number" ? ` · ${pct}% ready` : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className={`rounded-lg px-2 py-1 text-[11px] ${
            dark ? "hover:bg-white/5" : "hover:bg-slate-100"
          }`}
          aria-label={expanded ? "Shrink" : "Expand"}
        >
          {expanded ? "↘" : "↖"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className={`rounded-lg px-2 py-1 text-[11px] ${
            dark ? "hover:bg-white/5" : "hover:bg-slate-100"
          }`}
          aria-label={`Minimize ${ASSISTANT_NAME}`}
        >
          −
        </button>
      </header>

      {payload?.wizard?.steps?.length ? (
        <div
          className={`flex gap-1 overflow-x-auto border-b px-3 py-2 ${
            dark ? "border-white/10" : "border-slate-100"
          }`}
        >
          {payload.wizard.steps.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setStepId(s.id)}
              className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                payload.wizard?.step_id === s.id
                  ? dark
                    ? "bg-emerald-500/25 text-emerald-100"
                    : "bg-emerald-100 text-emerald-900"
                  : s.done
                    ? dark
                      ? "bg-white/5 text-zinc-400"
                      : "bg-slate-100 text-slate-500"
                    : dark
                      ? "bg-white/[0.03] text-zinc-500"
                      : "bg-slate-50 text-slate-400"
              }`}
              title={s.coming ? `Coming ${s.coming}` : s.id}
            >
              {s.done ? "✓" : s.coming ? "⏳" : "○"} {s.id}
            </button>
          ))}
        </div>
      ) : null}

      <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
        {loading && !chat.length && !payload ? (
          <p className={`text-sm ${dark ? "text-zinc-500" : "text-slate-500"}`}>
            {ASSISTANT_NAME} готовит контекст проекта…
          </p>
        ) : null}
        {chat.map((m, i) => (
          <div
            key={`c-${i}`}
            className={`rounded-2xl px-3 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
              m.role === "user"
                ? dark
                  ? "ml-4 bg-emerald-500/15 text-emerald-50"
                  : "ml-4 bg-emerald-50 text-emerald-950"
                : dark
                  ? "bg-white/[0.04] text-zinc-200"
                  : "bg-slate-50 text-slate-800"
            }`}
          >
            {m.text}
          </div>
        ))}
        {!chat.length
          ? (payload?.messages || []).map((m, i) => (
              <div
                key={`${m.role}-${i}`}
                className={`rounded-2xl px-3 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  dark ? "bg-white/[0.04] text-zinc-200" : "bg-slate-50 text-slate-800"
                }`}
              >
                {m.text}
              </div>
            ))
          : null}
      </div>

      {quick.length ? (
        <div
          className={`flex flex-wrap gap-1.5 border-t px-3 py-2 ${
            dark ? "border-white/10" : "border-slate-100"
          }`}
        >
          {quick.slice(0, 6).map((q) => (
            <button
              key={q.id}
              type="button"
              onClick={() => {
                if (q.href && !q.message) window.location.href = q.href;
                else void send(q.message || q.label);
              }}
              className={`rounded-full px-2.5 py-1 text-[11px] ${
                dark
                  ? "border border-white/10 bg-white/[0.03] text-zinc-300 hover:bg-white/5"
                  : "border border-slate-200 bg-slate-50 text-slate-700"
              }`}
            >
              {q.label}
            </button>
          ))}
        </div>
      ) : null}

      <div
        className={`flex flex-col gap-2 border-t p-3 ${
          dark ? "border-white/10" : "border-slate-200"
        }`}
      >
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void send(draft);
          }}
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Что вы хотите сделать с вашим проектом?"
            className={`min-w-0 flex-1 rounded-xl border px-3 py-2 text-sm outline-none ${
              dark
                ? "border-white/15 bg-black/40 text-white placeholder:text-zinc-600"
                : "border-slate-200 bg-white text-slate-900"
            }`}
            disabled={busy}
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            className={`rounded-xl px-3 py-2 text-sm font-semibold ${
              dark
                ? "bg-emerald-500/90 text-black disabled:opacity-40"
                : "bg-emerald-700 text-white disabled:opacity-40"
            }`}
          >
            →
          </button>
        </form>
        {(payload?.actions || []).slice(0, 2).map((action) => {
          const coming = action.kind === "coming" || action.status === "coming";
          return (
            <button
              key={`${action.id}-${action.label}`}
              type="button"
              disabled={coming && action.kind === "coming"}
              onClick={() => runAction(action)}
              className={`rounded-xl px-3 py-2 text-left text-xs font-semibold transition ${
                coming
                  ? dark
                    ? "cursor-default border border-white/10 text-zinc-500"
                    : "cursor-default border border-slate-200 text-slate-500"
                  : dark
                    ? "border border-white/10 text-zinc-300 hover:bg-white/5"
                    : "border border-slate-200 text-slate-700"
              }`}
            >
              {action.label}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
