import { useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useSession } from "../context/SessionContext";
import { useI18n } from "../i18n/I18nProvider";
import { GenesisMark } from "../components/GenesisMark";

export function ConnectPage() {
  const { settings, updateSettings } = useAppSettings();
  const { connect, connecting, error } = useSession();
  const { t } = useI18n();
  const [localError, setLocalError] = useState<string | null>(null);

  async function onConnect() {
    setLocalError(null);
    if (!settings.apiUrl.trim()) {
      setLocalError(t("connect.error.url"));
      return;
    }
    const ok = await connect();
    if (!ok && !error) setLocalError(t("connect.error.failed"));
  }

  return (
    <div className="connect">
      <div className="connect__card">
        <div className="connect__logo" aria-hidden>
          <GenesisMark className="connect__logo-svg" />
        </div>
        <h1>{t("connect.title")}</h1>
        <p className="connect__lead">{t("connect.lead")}</p>

        <label className="field">
          <span>{t("connect.name")}</span>
          <input
            value={settings.ownerName}
            onChange={(e) => updateSettings({ ownerName: e.target.value })}
            placeholder="Ramish"
            autoComplete="name"
          />
        </label>

        <label className="field">
          <span>{t("connect.apiUrl")}</span>
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
          className="btn btn--primary connect__submit"
          disabled={connecting}
          onClick={() => void onConnect()}
        >
          {connecting ? t("boot.connecting") : t("connect.submit")}
        </button>
      </div>
    </div>
  );
}
