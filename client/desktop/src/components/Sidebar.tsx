export type NavId = "home" | "settings";

const NAV: { id: NavId; label: string; hint: string }[] = [
  { id: "home", label: "Home", hint: "Connection & status" },
  { id: "settings", label: "Settings", hint: "API, theme, updates" },
];

type SidebarProps = {
  active: NavId;
  onNavigate: (id: NavId) => void;
};

export function Sidebar({ active, onNavigate }: SidebarProps) {
  return (
    <nav className="sidebar" aria-label="Primary">
      <div className="sidebar__brand">
        <div className="sidebar__logo" aria-hidden>
          G
        </div>
        <div>
          <div className="sidebar__name">Genesis</div>
          <div className="sidebar__tag">Client Foundation</div>
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
      <p className="sidebar__footer">Windows-first · Tauri 2</p>
    </nav>
  );
}
