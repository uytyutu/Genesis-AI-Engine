import { GenesisMark } from "./GenesisMark";
import { useI18n } from "../i18n/I18nProvider";

export type NavId = "home" | "chat" | "studio" | "projects" | "settings";

type SidebarProps = {
  active: NavId;
  ownerLabel: string;
  connected: boolean;
  onNavigate: (id: NavId) => void;
  onDisconnect: () => void;
};

export function Sidebar({
  active,
  ownerLabel,
  connected,
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
          <div className="sidebar__name">{t("app.name")}</div>
          <div className="sidebar__tag">{t("app.platform")}</div>
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
        {nav.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className={`sidebar__link${active === item.id ? " is-active" : ""}`}
              aria-current={active === item.id ? "page" : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <span className="sidebar__link-label">{t(item.labelKey)}</span>
              <span className="sidebar__link-hint">{t(item.hintKey)}</span>
            </button>
          </li>
        ))}
      </ul>

      <button type="button" className="sidebar__disconnect" onClick={onDisconnect}>
        {t("session.disconnect")}
      </button>
      <p className="sidebar__footer">{t("app.stage")}</p>
    </nav>
  );
}
