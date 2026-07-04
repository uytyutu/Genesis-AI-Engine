export type NavId = "home" | "chat" | "projects" | "settings";

const NAV: { id: NavId; label: string; hint: string }[] = [
  { id: "home", label: "Home", hint: "Owner dashboard" },
  { id: "chat", label: "Chat", hint: "Genesis assistant" },
  { id: "projects", label: "Projects", hint: "Factory products" },
  { id: "settings", label: "Settings", hint: "API, theme, updates" },
];

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
  return (
    <nav className="sidebar" aria-label="Primary">
      <div className="sidebar__brand">
        <div className="sidebar__logo" aria-hidden>
          G
        </div>
        <div>
          <div className="sidebar__name">Genesis</div>
          <div className="sidebar__tag">Windows Client</div>
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
            {connected ? "Connected" : "Offline"}
          </div>
        </div>
      </div>

      <ul className="sidebar__list">
        {NAV.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className={`sidebar__link${active === item.id ? " is-active" : ""}`}
              aria-current={active === item.id ? "page" : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <span className="sidebar__link-label">{item.label}</span>
              <span className="sidebar__link-hint">{item.hint}</span>
            </button>
          </li>
        ))}
      </ul>

      <button type="button" className="sidebar__disconnect" onClick={onDisconnect}>
        Disconnect
      </button>
      <p className="sidebar__footer">Stage 2 · Tauri 2</p>
    </nav>
  );
}
