import { GenesisMark } from "./GenesisMark";
import { VectorStatus } from "./VectorStatus";
import { useI18n } from "../i18n/I18nProvider";

export type NavId = "home" | "chat" | "studio" | "projects" | "settings";

type SidebarProps = {
  active: NavId;
  ownerLabel: string;
  connected: boolean;
  customerMode?: boolean;
  vectorThinking?: boolean;
  onNavigate: (id: NavId) => void;
  onDisconnect: () => void;
};

const CUSTOMER_NAV: { id: NavId; label: string; hint: string }[] = [
  { id: "chat", label: "Vector", hint: "Ваш цифровой сотрудник" },
  { id: "home", label: "Компания", hint: "Обзор и быстрые действия" },
  { id: "projects", label: "Проекты", hint: "Результаты и материалы" },
  { id: "settings", label: "Настройки", hint: "Профиль и язык" },
];

export function Sidebar({
  active,
  ownerLabel,
  connected,
  customerMode = false,
  vectorThinking = false,
  onNavigate,
  onDisconnect,
}: SidebarProps) {
  const { t } = useI18n();

  const nav: { id: NavId; labelKey: string; hintKey: string }[] = [
    { id: "home", labelKey: "nav.home", hintKey: "nav.home.hint" },
    { id: "chat", labelKey: "nav.chat", hintKey: "nav.chat.hint" },
    { id: "studio", labelKey: "nav.studio", hintKey: "nav.studio.hint" },
    { id: "projects", labelKey: "nav.projects", hintKey: "nav.projects.hint" },
    { id: "settings", labelKey: "nav.settings", hintKey: "nav.settings.hint" },
  ];

  return (
    <nav className="sidebar" aria-label="Primary">
      <div className="sidebar__brand">
        <div className="sidebar__logo" aria-hidden>
          <GenesisMark />
        </div>
        <div>
          {customerMode ? (
            <VectorStatus connected={connected} thinking={vectorThinking} compact />
          ) : (
            <>
              <div className="sidebar__name">{t("app.name")}</div>
              <div className="sidebar__tag">{t("app.platform")}</div>
            </>
          )}
        </div>
      </div>

      <div className="sidebar__session">
        <span
          className={`sidebar__dot${connected ? " is-online" : ""}`}
          aria-hidden
        />
        <div>
          <div className="sidebar__user">{ownerLabel}</div>
          <div className="sidebar__status">
            {connected ? t("session.connected") : t("session.offline")}
          </div>
        </div>
      </div>

      <ul className="sidebar__list">
        {(customerMode ? CUSTOMER_NAV : nav).map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className={`sidebar__link${active === item.id ? " is-active" : ""}`}
              aria-current={active === item.id ? "page" : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <span className="sidebar__link-label">
                {customerMode
                  ? (item as (typeof CUSTOMER_NAV)[0]).label
                  : t((item as (typeof nav)[0]).labelKey)}
              </span>
              <span className="sidebar__link-hint">
                {customerMode
                  ? (item as (typeof CUSTOMER_NAV)[0]).hint
                  : t((item as (typeof nav)[0]).hintKey)}
              </span>
            </button>
          </li>
        ))}
      </ul>

      <button type="button" className="sidebar__disconnect" onClick={onDisconnect}>
        {customerMode ? "Выйти" : t("session.disconnect")}
      </button>
      <p className="sidebar__footer">{t("app.stage")}</p>
    </nav>
  );
}
