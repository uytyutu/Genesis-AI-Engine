import { useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useSession } from "../context/SessionContext";
import { checkForUpdates } from "../lib/updater";
import type { ThemeMode } from "../lib/tokens";
import { useI18n } from "../i18n/I18nProvider";
import { CEO_DESKTOP_LOCALES, type LocaleId } from "@genesis/i18n/types";
import { LOCALE_REGISTRY } from "@genesis/i18n/registry";

export function SettingsPage() {
  const { settings, updateSettings, resetSettings } = useAppSettings();
  const { disconnect, ownerLabel } = useSession();
  const { t } = useI18n();
  const [updateMsg, setUpdateMsg] = useState<string | null>(null);

  return (
    <div className="page page--wide">
      <header className="page__header">
        <h1>{t("settings.title")}</h1>
        <p>{t("settings.lead")}</p>
      </header>

      <div className="settings-grid">
        <section className="card settings-card">
          <div className="settings-card__icon" aria-hidden>
            👤
          </div>
          <h2>{t("settings.account")}</h2>
          <p className="settings-card__lead">
            {t("settings.account.signedIn")}{" "}
            <strong>{ownerLabel}</strong>
          </p>
          <label className="field">
            <span>{t("settings.displayName")}</span>
            <input
              value={settings.ownerName}
              onChange={(e) => updateSettings({ ownerName: e.target.value })}
              placeholder={t("settings.displayName.placeholder")}
              autoComplete="name"
            />
          </label>
          <button type="button" className="btn btn--ghost" onClick={disconnect}>
            {t("settings.disconnect")}
          </button>
        </section>

        <section className="card settings-card">
          <div className="settings-card__icon" aria-hidden>
            🔗
          </div>
          <h2>{t("settings.api")}</h2>
          <label className="field">
            <span>{t("connect.apiUrl")}</span>
            <input
              type="url"
              value={settings.apiUrl}
              onChange={(e) => updateSettings({ apiUrl: e.target.value })}
              autoComplete="off"
            />
          </label>
          <label className="field">
            <span>{t("settings.apiKey")}</span>
            <input
              type="password"
              value={settings.apiKey}
              onChange={(e) => updateSettings({ apiKey: e.target.value })}
              placeholder={t("settings.apiKey.placeholder")}
              autoComplete="off"
            />
          </label>
        </section>

        <section className="card settings-card">
          <div className="settings-card__icon" aria-hidden>
            🎨
          </div>
          <h2>{t("settings.appearance")}</h2>
          <label className="field">
            <span>{t("settings.theme")}</span>
            <select
              value={settings.theme}
              onChange={(e) =>
                updateSettings({ theme: e.target.value as ThemeMode })
              }
            >
              <option value="dark">{t("settings.theme.dark")}</option>
              <option value="light">{t("settings.theme.light")}</option>
              <option value="system">{t("settings.theme.system")}</option>
            </select>
          </label>
          <label className="field">
            <span>{t("settings.language")}</span>
            <select
              value={settings.locale}
              onChange={(e) =>
                updateSettings({ locale: e.target.value as LocaleId })
              }
            >
              {CEO_DESKTOP_LOCALES.map((id: LocaleId) => (
                <option key={id} value={id}>
                  {LOCALE_REGISTRY[id].nativeName}
                </option>
              ))}
            </select>
          </label>
        </section>

        <section className="card settings-card">
          <div className="settings-card__icon" aria-hidden>
            ⬆️
          </div>
          <h2>{t("settings.updates")}</h2>
          <label className="field field--row">
            <input
              type="checkbox"
              checked={settings.checkUpdatesOnLaunch}
              onChange={(e) =>
                updateSettings({ checkUpdatesOnLaunch: e.target.checked })
              }
            />
            <span>{t("settings.updates.onLaunch")}</span>
          </label>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() =>
              void checkForUpdates(true).then((r) => setUpdateMsg(r.message))
            }
          >
            {t("settings.updates.checkNow")}
          </button>
          {updateMsg ? <p className="hint">{updateMsg}</p> : null}
        </section>
      </div>

      <section className="card card--muted">
        <h2>{t("settings.reset")}</h2>
        <p>{t("settings.reset.lead")}</p>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => {
            resetSettings();
            disconnect();
          }}
        >
          {t("settings.reset.button")}
        </button>
      </section>
    </div>
  );
}
