import { useState } from "react";
import { useAppSettings } from "../context/AppSettingsContext";
import { useCustomerAuth } from "../context/CustomerAuthContext";
import { useSession } from "../context/SessionContext";
import { useNavigation } from "../context/NavigationContext";
import { checkForUpdates } from "../lib/updater";
import type { ThemeMode } from "../lib/tokens";
import { useI18n } from "../i18n/I18nProvider";
import { CEO_DESKTOP_LOCALES, type LocaleId } from "@genesis/i18n/types";
import { LOCALE_REGISTRY } from "@genesis/i18n/registry";
import { BRAND_NAME, ASSISTANT_NAME } from "../lib/publicBrand";

const DEV_UNLOCK_CLICKS = 5;

function CustomerSettingsPage() {
  const { settings, updateSettings } = useAppSettings();
  const { session, logout } = useCustomerAuth();
  const { openChat } = useNavigation();
  const [updateMsg, setUpdateMsg] = useState<string | null>(null);
  const [aboutClicks, setAboutClicks] = useState(0);
  const [showDev, setShowDev] = useState(false);

  function onAboutClick() {
    const next = aboutClicks + 1;
    setAboutClicks(next);
    if (next >= DEV_UNLOCK_CLICKS) setShowDev(true);
  }

  return (
    <div className="page page--wide">
      <header className="page__header">
        <h1>Настройки</h1>
        <p>Аккаунт, язык и поддержка.</p>
      </header>

      <div className="settings-grid">
        <section className="card settings-card">
          <h2>Аккаунт</h2>
          <p>
            <strong>{session?.name}</strong>
            <br />
            <span className="hint">{session?.email}</span>
          </p>
          <button type="button" className="btn btn--ghost" onClick={logout}>
            Выйти
          </button>
        </section>

        <section className="card settings-card">
          <h2>Язык</h2>
          <label className="field">
            <span>Язык интерфейса</span>
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
          <h2>Уведомления</h2>
          <label className="field field--row">
            <input
              type="checkbox"
              checked={settings.checkUpdatesOnLaunch}
              onChange={(e) =>
                updateSettings({ checkUpdatesOnLaunch: e.target.checked })
              }
            />
            <span>Сообщать о новых версиях приложения</span>
          </label>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() =>
              void checkForUpdates(true).then((r) => setUpdateMsg(r.message))
            }
          >
            Проверить обновления
          </button>
          {updateMsg ? <p className="hint">{updateMsg}</p> : null}
        </section>

        <section className="card settings-card">
          <h2>Безопасность</h2>
          <p className="hint">
            Смена пароля и двухфакторная защита — скоро. Сейчас выход из аккаунта
            в разделе «Аккаунт».
          </p>
        </section>

        <section className="card settings-card">
          <h2>Подписка</h2>
          <p>
            <strong>Free</strong> — без срока, один активный проект.
          </p>
          <p className="hint">
            Professional и Business — скоро. Без давления: переход, когда вам
            станет тесно.
          </p>
        </section>

        <section className="card settings-card">
          <h2>Поддержка</h2>
          <p className="hint">
            {ASSISTANT_NAME} — ваша первая линия поддержки. Напишите о проблеме,
            идее или вопросе.
          </p>
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => openChat("Нужна помощь")}
          >
            Написать {ASSISTANT_NAME}
          </button>
        </section>

        <section className="card settings-card">
          <h2>
            <button
              type="button"
              className="btn btn--link settings-about-title"
              onClick={onAboutClick}
            >
              О программе
            </button>
          </h2>
          <p>
            {BRAND_NAME} — ваша цифровая компания с {ASSISTANT_NAME}.
          </p>
        </section>

        {showDev ? (
          <section className="card settings-card card--muted">
            <h2>Для команды Virtus</h2>
            <p className="hint">Технические параметры — только для разработки.</p>
            <label className="field field--row">
              <input
                type="checkbox"
                checked={settings.devMode}
                onChange={(e) => updateSettings({ devMode: e.target.checked })}
              />
              <span>Режим команды (внутренний)</span>
            </label>
            <label className="field">
              <span>Адрес сервера</span>
              <input
                type="url"
                value={settings.apiUrl}
                onChange={(e) => updateSettings({ apiUrl: e.target.value })}
              />
            </label>
          </section>
        ) : null}
      </div>
    </div>
  );
}

function DevSettingsPage() {
  const { settings, updateSettings, resetSettings } = useAppSettings();
  const { disconnect, ownerLabel } = useSession();
  const { t } = useI18n();

  return (
    <div className="page page--wide">
      <header className="page__header">
        <h1>{t("settings.title")}</h1>
        <p>{t("settings.lead")}</p>
      </header>
      <div className="settings-grid">
        <section className="card settings-card">
          <h2>{t("settings.account")}</h2>
          <p>
            {t("settings.account.signedIn")} <strong>{ownerLabel}</strong>
          </p>
          <label className="field">
            <span>{t("settings.displayName")}</span>
            <input
              value={settings.ownerName}
              onChange={(e) => updateSettings({ ownerName: e.target.value })}
            />
          </label>
          <button type="button" className="btn btn--ghost" onClick={disconnect}>
            {t("settings.disconnect")}
          </button>
        </section>
        <section className="card settings-card">
          <h2>{t("settings.api")}</h2>
          <label className="field">
            <span>{t("connect.apiUrl")}</span>
            <input
              type="url"
              value={settings.apiUrl}
              onChange={(e) => updateSettings({ apiUrl: e.target.value })}
            />
          </label>
          <label className="field">
            <span>{t("settings.apiKey")}</span>
            <input
              type="password"
              value={settings.apiKey}
              onChange={(e) => updateSettings({ apiKey: e.target.value })}
            />
          </label>
        </section>
        <section className="card settings-card">
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
            </select>
          </label>
        </section>
        <section className="card settings-card">
          <label className="field field--row">
            <input
              type="checkbox"
              checked={settings.devMode}
              onChange={(e) => updateSettings({ devMode: e.target.checked })}
            />
            <span>Dev mode</span>
          </label>
        </section>
      </div>
      <section className="card card--muted">
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

export function SettingsPage() {
  const { settings } = useAppSettings();
  const { session } = useCustomerAuth();
  const isCustomer = !settings.devMode && session;
  if (isCustomer) return <CustomerSettingsPage />;
  return <DevSettingsPage />;
}
