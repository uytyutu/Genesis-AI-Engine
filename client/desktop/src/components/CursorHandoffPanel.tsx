import { useCallback, useEffect, useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useI18n } from "../i18n/I18nProvider";
import {
  approveAiHubTask,
  createAiHubTask,
  cursorVerify,
  fetchAiHubTasks,
  fetchCursorHistory,
  fetchCursorStatus,
  fetchCursorTasks,
  verifyAiHubTask,
  type AiHubTask,
  type CursorHistoryItem,
  type CursorStatus,
  type CursorTask,
} from "../lib/endpoints";
import { BRAND_NAME } from "../lib/publicBrand";

function formatWhen(iso: string | null | undefined) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function CursorHandoffPanel() {
  const { settings } = useAppSettings();
  const { t } = useI18n();
  const [status, setStatus] = useState<CursorStatus | null>(null);
  const [hubTasks, setHubTasks] = useState<AiHubTask[]>([]);
  const [cursorTasks, setCursorTasks] = useState<CursorTask[]>([]);
  const [history, setHistory] = useState<CursorHistoryItem[]>([]);
  const [input, setInput] = useState("");
  const [projectId, setProjectId] = useState("genesis");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [active, setActive] = useState<AiHubTask | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [st, hub, cur, hist] = await Promise.all([
        fetchCursorStatus(settings),
        fetchAiHubTasks(settings),
        fetchCursorTasks(settings),
        fetchCursorHistory(settings),
      ]);
      setStatus(st);
      setHubTasks(hub);
      setCursorTasks(cur);
      setHistory(hist);
      setActive(hub.find((x) => !["report", "failed", "cancelled"].includes(x.phase)) ?? hub[0] ?? null);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "API error");
    }
  }, [settings]);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 12000);
    return () => window.clearInterval(id);
  }, [refresh]);

  async function onCreate() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setMessage(null);
    try {
      const task = await createAiHubTask(settings, text, projectId);
      setActive(task);
      setInput("");
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function onApprove() {
    if (!active || busy) return;
    setBusy(true);
    setMessage(null);
    try {
      const task = await approveAiHubTask(settings, active.id);
      setActive(task);
      setMessage(t("studio.handoff.approved"));
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Approve failed");
    } finally {
      setBusy(false);
    }
  }

  async function onVerify() {
    if (!active || busy) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await verifyAiHubTask(settings, active.id);
      setMessage(result.message);
      if (result.hub_task) setActive(result.hub_task);
      await refresh();
    } catch {
      const fallback = await cursorVerify(settings);
      setMessage(fallback.message);
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  const cursorLinked = active?.cursor_task ?? cursorTasks[0] ?? null;

  return (
    <div className="studio-handoff">
      <section className="card">
        <div className="card__head">
          <h2>{t("studio.handoff.status")}</h2>
          <button type="button" className="btn btn--ghost" onClick={() => void refresh()}>
            {t("home.refresh")}
          </button>
        </div>
        {status ? (
          <p className="studio-handoff__status">
            <span aria-hidden>{status.status_icon}</span> {status.status_label} — {status.hint}
          </p>
        ) : (
          <p className="hint">{t("boot.loading")}</p>
        )}
      </section>

      <section className="card">
        <h2>{t("studio.handoff.newTask")}</h2>
        <label className="field">
          <span>{t("studio.workspace.project")}</span>
          <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
            <option value="genesis">{BRAND_NAME}</option>
            <option value="perfect-pallet">Perfect Pallet</option>
          </select>
        </label>
        <label className="field">
          <span>{t("studio.handoff.taskInput")}</span>
          <textarea
            rows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t("studio.handoff.placeholder")}
          />
        </label>
        <div className="studio-handoff__actions">
          <button type="button" className="btn btn--primary" disabled={busy || !input.trim()} onClick={() => void onCreate()}>
            {t("studio.handoff.createPlan")}
          </button>
        </div>
      </section>

      {active ? (
        <section className="card">
          <h2>{t("studio.handoff.plan")}</h2>
          <p className="studio-handoff__phase">
            {t("studio.handoff.phase")}: <strong>{active.phase}</strong>
          </p>
          <pre className="studio-handoff__plan">{active.plan_summary}</pre>
          <ol className="studio-handoff__steps">
            {active.plan.map((step) => (
              <li key={step.id} className={step.status === "done" ? "is-done" : step.status === "active" ? "is-active" : ""}>
                {step.title}
                {step.requires_approve ? " · ✔" : ""}
              </li>
            ))}
          </ol>
          {active.phase === "awaiting_approve" ? (
            <button type="button" className="btn btn--primary" disabled={busy} onClick={() => void onApprove()}>
              {t("studio.handoff.approve")}
            </button>
          ) : null}
          {["executing", "verify", "dispatch"].includes(active.phase) ? (
            <button type="button" className="btn btn--secondary" disabled={busy} onClick={() => void onVerify()}>
              {t("studio.handoff.verify")}
            </button>
          ) : null}
          {active.error ? <p className="banner banner--warn">{active.error}</p> : null}
        </section>
      ) : null}

      {cursorLinked ? (
        <section className="card">
          <h2>{t("studio.handoff.cursorTask")}</h2>
          <p>
            <strong>{cursorLinked.state_label}</strong>
            {cursorLinked.task_note ? ` — ${cursorLinked.task_note}` : ""}
          </p>
          <ul className="studio-handoff__steps">
            {cursorLinked.steps.map((s) => (
              <li key={s.id} className={s.done ? "is-done" : s.active ? "is-active" : ""}>
                {s.label}
              </li>
            ))}
          </ul>
          {cursorLinked.verify_summary ? (
            <pre className="studio-handoff__verify">{cursorLinked.verify_summary}</pre>
          ) : null}
        </section>
      ) : null}

      <div className="studio-columns">
        <section className="card">
          <h2>{t("studio.handoff.hubHistory")}</h2>
          {hubTasks.length === 0 ? (
            <p className="hint">{t("studio.handoff.empty")}</p>
          ) : (
            <ul className="link-list">
              {hubTasks.slice(0, 8).map((task) => (
                <li key={task.id}>
                  <button type="button" className="link-list__btn" onClick={() => setActive(task)}>
                    <strong>{task.input_text.slice(0, 60)}</strong>
                    <span>
                      {task.phase} · {formatWhen(task.updated_at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2>{t("studio.handoff.cursorHistory")}</h2>
          {history.length === 0 ? (
            <p className="hint">{t("studio.handoff.empty")}</p>
          ) : (
            <ul className="timeline timeline--dense">
              {history.slice(0, 10).map((h, i) => (
                <li key={`${h.at}-${i}`}>
                  <time>{formatWhen(h.at)}</time>
                  <span>
                    {h.kind} — {h.task_note ?? `${h.chars} chars`}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {message ? <p className="banner">{message}</p> : null}
    </div>
  );
}
