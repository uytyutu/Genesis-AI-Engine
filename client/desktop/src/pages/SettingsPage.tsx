import { useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { checkForUpdates } from "../lib/updater";
import type { ThemeMode } from "../lib/tokens";

export function SettingsPage() {
  const { settings, updateSettings, resetSettings } = useAppSettings();
  const [updateMsg, setUpdateMsg] = useState<string | null>(null);

  return (
    <div className="page">
      <header className="page__header">
        <h1>Settings</h1>
        <p>Stored locally on this device (Stage 1).</p>
      </header>

      <section className="card">
        <h2>API</h2>
        <label className="field">
          <span>Genesis API URL</span>
          <input
            type="url"
            value={settings.apiUrl}
            onChange={(e) => updateSettings({ apiUrl: e.target.value })}
            placeholder="https://…"
            autoComplete="off"
          />
        </label>
        <label className="field">
          <span>API key (optional scaffold)</span>
          <input
            type="password"
            value={settings.apiKey}
            onChange={(e) => updateSettings({ apiKey: e.target.value })}
            placeholder="Reserved for owner auth"
            autoComplete="off"
          />
        </label>
      </section>

      <section className="card">
        <h2>Appearance</h2>
        <label className="field">
          <span>Theme</span>
          <select
            value={settings.theme}
            onChange={(e) =>
              updateSettings({ theme: e.target.value as ThemeMode })
            }
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="system">System</option>
          </select>
        </label>
      </section>

      <section className="card">
        <h2>Updates</h2>
        <label className="field field--row">
          <input
            type="checkbox"
            checked={settings.checkUpdatesOnLaunch}
            onChange={(e) =>
              updateSettings({ checkUpdatesOnLaunch: e.target.checked })
            }
          />
          <span>Check for updates on launch</span>
        </label>
        <button
          type="button"
          className="btn btn--secondary"
          onClick={() =>
            void checkForUpdates(true).then((r) => setUpdateMsg(r.message))
          }
        >
          Check now
        </button>
        {updateMsg ? <p className="hint">{updateMsg}</p> : null}
      </section>

      <section className="card card--muted">
        <h2>Reset</h2>
        <p>Restore default API URL and theme.</p>
        <button type="button" className="btn btn--ghost" onClick={resetSettings}>
          Reset settings
        </button>
      </section>
    </div>
  );
}
