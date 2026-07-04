import type { ReactNode } from "react";
import { Sidebar, type NavId } from "./Sidebar";

type ShellProps = {
  active: NavId;
  ownerLabel: string;
  connected: boolean;
  onNavigate: (id: NavId) => void;
  onDisconnect: () => void;
  children: ReactNode;
};

export function Shell({
  active,
  ownerLabel,
  connected,
  onNavigate,
  onDisconnect,
  children,
}: ShellProps) {
  return (
    <div className="shell">
      <Sidebar
        active={active}
        ownerLabel={ownerLabel}
        connected={connected}
        onNavigate={onNavigate}
        onDisconnect={onDisconnect}
      />
      <div className="shell__main">
        <header className="shell__titlebar" data-tauri-drag-region>
          <span className="shell__mark" aria-hidden>
            G
          </span>
          <span className="shell__product">Genesis Client</span>
          <span
            className={`shell__conn${connected ? " is-online" : ""}`}
            title={connected ? "API connected" : "Not connected"}
          >
            {connected ? "Online" : "Offline"}
          </span>
        </header>
        <div className="shell__content">{children}</div>
      </div>
    </div>
  );
}
