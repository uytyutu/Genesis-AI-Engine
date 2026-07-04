import { useCallback, useEffect, useState } from "react";
import { pingApi, type ApiPingResult } from "../lib/api";
import { getAuthState } from "../lib/auth";
import { checkForUpdates } from "../lib/updater";
import { useAppSettings } from "../context/AppSettingsContext";

export function HomePage() {
  const { settings } = useAppSettings();
  const auth = getAuthState(settings);
  const [ping, setPing] = useState<ApiPingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [updateNote, setUpdateNote] = useState<string | null>(null);

  const runPing = useCallback(async () => {
    setLoading(true);
    const result = await pingApi(settings);
    setPing(result);
    setLoading(false);
  }, [settings]);

  useEffect(() => {
    void runPing();
  }, [runPing]);

  useEffect(() => {
    if (!settings.checkUpdatesOnLaunch) return;
    void checkForUpdates(true).then((r) => setUpdateNote(r.message));
  }, [settings.checkUpdatesOnLaunch]);

  return (
    <div className="page">
      <header className="page__header">
        <h1>Genesis workspace</h1>
        <p>Stage 1 shell — API connection and local settings only.</p>
      </header>

      <section className="card">
        <div className="card__head">
          <h2>API connection</h2>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => void runPing()}
            disabled={loading}
          >
            {loading ? "Checking…" : "Ping API"}
          </button>
        </div>
        <dl className="kv">
          <div>
            <dt>Endpoint</dt>
            <dd className="mono">{settings.apiUrl}</dd>
          </div>
          <div>
            <dt>Auth</dt>
            <dd>{auth.configured ? `Configured (${auth.maskedKey})` : "Not set"}</dd>
          </div>
        </dl>
        {ping?.ok ? (
          <div className="status status--ok">
            <strong>{ping.status.name}</strong> v{ping.status.version} · phase{" "}
            {ping.status.phase}
            {ping.status.paused ? " · paused" : ""} · {ping.latencyMs}ms
          </div>
        ) : ping ? (
          <div className="status status--err">Could not reach API: {ping.error}</div>
        ) : null}
      </section>

      {updateNote ? (
        <section className="card card--muted">
          <h2>Updates</h2>
          <p>{updateNote}</p>
        </section>
      ) : null}
    </div>
  );
}
