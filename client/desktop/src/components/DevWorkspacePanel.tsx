import { useCallback, useEffect, useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useI18n } from "../i18n/I18nProvider";
import {
  fetchDevProjectFiles,
  fetchDevWorkspace,
  type DevFileEntry,
  type DevWorkspaceSnapshot,
} from "../lib/endpoints";

export function DevWorkspacePanel() {
  const { settings } = useAppSettings();
  const { t } = useI18n();
  const [snap, setSnap] = useState<DevWorkspaceSnapshot | null>(null);
  const [projectId, setProjectId] = useState("genesis");
  const [files, setFiles] = useState<DevFileEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const ws = await fetchDevWorkspace(settings);
      setSnap(ws);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
  }, [settings]);

  const loadFiles = useCallback(async () => {
    try {
      const list = await fetchDevProjectFiles(settings, projectId);
      setFiles(list);
    } catch {
      setFiles([]);
    }
  }, [settings, projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    void loadFiles();
  }, [loadFiles]);

  if (!snap) {
    return <p className="hint">{t("boot.loading")}</p>;
  }

  return (
    <div className="studio-workspace">
      {error ? <p className="banner banner--warn">{error}</p> : null}

      <section className="card">
        <h2>{t("studio.workspace.projects")}</h2>
        <ul className="module-list">
          {snap.projects.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                className={`link-list__btn${projectId === p.id ? " is-active" : ""}`}
                onClick={() => setProjectId(p.id)}
              >
                <strong>{p.name}</strong>
                <span>
                  {p.available ? p.path_label : t("studio.workspace.unavailable")}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      {snap.suggestions.length > 0 ? (
        <section className="card">
          <h2>{t("studio.workspace.suggestions")}</h2>
          <ul className="link-list">
            {snap.suggestions.map((s) => (
              <li key={s.id}>
                <div className="link-list__btn">
                  <strong>{s.title}</strong>
                  <span>{s.detail}</span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="studio-columns">
        <section className="card">
          <h2>{t("studio.workspace.files")}</h2>
          {files.length === 0 ? (
            <p className="hint">{t("studio.workspace.noFiles")}</p>
          ) : (
            <ul className="file-list">
              {files.map((f) => (
                <li key={f.path}>{f.path}</li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2>{t("studio.workspace.buildHistory")}</h2>
          {snap.build_history.length === 0 ? (
            <p className="hint">{t("studio.handoff.empty")}</p>
          ) : (
            <ul className="timeline timeline--dense">
              {snap.build_history.map((b, i) => (
                <li key={`${b.task_id}-${i}`}>
                  <time>{b.at ?? "—"}</time>
                  <span>
                    {b.label} — {b.state_label ?? b.state}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
