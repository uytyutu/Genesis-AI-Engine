import { useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useSession } from "../context/SessionContext";

export function ConnectPage() {
  const { settings, updateSettings } = useAppSettings();
  const { connect, connecting, error } = useSession();
  const [localError, setLocalError] = useState<string | null>(null);

  async function onConnect() {
    setLocalError(null);
    if (!settings.apiUrl.trim()) {
      setLocalError("Enter a Genesis API URL.");
      return;
    }
    const ok = await connect();
    if (!ok && !error) setLocalError("Could not connect to Genesis API.");
  }

  return (
    <div className="connect">
      <div className="connect__card">
        <div className="connect__logo" aria-hidden>
          G
        </div>
        <h1>Connect to Genesis</h1>
        <p className="connect__lead">
          Sign in to your company workspace. Stage 2 uses live API endpoints —
          no mock data.
        </p>

        <label className="field">
          <span>Your name</span>
          <input
            value={settings.ownerName}
            onChange={(e) => updateSettings({ ownerName: e.target.value })}
            placeholder="Ramish"
            autoComplete="name"
          />
        </label>

        <label className="field">
          <span>Genesis API URL</span>
          <input
            type="url"
            value={settings.apiUrl}
            onChange={(e) => updateSettings({ apiUrl: e.target.value })}
            placeholder="https://genesis-ai-engine-production.up.railway.app"
            autoComplete="off"
          />
        </label>

        {(localError || error) && (
          <p className="connect__error" role="alert">
            {localError || error}
          </p>
        )}

        <button
          type="button"
          className="btn btn--primary btn--block"
          onClick={() => void onConnect()}
          disabled={connecting}
        >
          {connecting ? "Connecting…" : "Connect"}
        </button>

        <p className="connect__hint">
          Verifies <code>/api/status</code> and loads your owner dashboard.
        </p>
      </div>
    </div>
  );
}
