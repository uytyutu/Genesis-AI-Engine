import { useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useSession } from "../context/SessionContext";
import { checkForUpdates } from "../lib/updater";
import type { ThemeMode } from "../lib/tokens";

export function SettingsPage() {
  const { settings, updateSettings, resetSettings } = useAppSettings();
  const { disconnect, ownerLabel } = useSession();
  const [updateMsg, setUpdateMsg] = useState<string | null>(null);

  return (
    <div className="page page--wide">
      <header className="page__header">
        <h1>Settings</h1>
        <p>Account, connection, and appearance.</p>
      </header>

      <div className="settings-grid">
        <section className="card settings-card">
          <div className="settings-card__icon" aria-hidden>
            👤
          </div>
          <h2>Account</h2>
          <p className="settings-card__lead">
            Signed in as <strong>{ownerLabel}</strong>
          </p>
          <label className="field">
            <span>Display name</span>
            <input
              value={settings.ownerName}
              onChange={(e) => updateSettings({ ownerName: e.target.value })}
              placeholder="Overrides API owner name"
              autoComplete="name"
            />
          </label>
          <button type="button" className="btn btn--ghost" onClick={disconnect}>
            Disconnect session
          </button>
        </section>

        <section className="card settings-card">
          <div className="settings-card__icon" aria-hidden>
            🔗
          </div>
          <h2>API connection</h2>
          <label className="field">
            <span>Genesis API URL</span>
            <input
              type="url"
              value={settings.apiUrl}
              onChange={(e) => updateSettings({ apiUrl: e.target.value })}
              autoComplete="off"
            />
          </label>
          <label className="field">
            <span>API key (reserved)</span>
            <input
              type="password"
              value={settings.apiKey}
              onChange={(e) => updateSettings({ apiKey: e.target.value })}
              placeholder="Future secured owner auth"
              autoComplete="off"
            />
          </label>
        </section>

        <section className="card settings-card">
          <div className="settings-card__icon" aria-hidden>
            🎨
          </div>
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

        <section className="card settings-card">
          <div className="settings-card__icon" aria-hidden>
            ⬆️
          </div>
          <h2>Updates</h2>
          <label className="field field--row">
            <input
              type="checkbox"
              checked={settings.checkUpdatesOnLaunch}
              onChange={(e) =>
                updateSettings({ checkUpdatesOnLaunch: e.target.checked })
              }
            />
            <span>Check on launch</span>
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
      </div>

      <section className="card card--muted">
        <h2>Reset</h2>
        <p>Restore defaults and sign out.</p>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => {
            resetSettings();
            disconnect();
          }}
        >
          Reset all settings
        </button>
      </section>
    </div>
  );
}
