import type { ReactNode } from "react";
import { Sidebar, type NavId } from "./Sidebar";

type ShellProps = {
  active: NavId;
  onNavigate: (id: NavId) => void;
  children: ReactNode;
};

export function Shell({ active, onNavigate, children }: ShellProps) {
  return (
    <div className="shell">
      <Sidebar active={active} onNavigate={onNavigate} />
      <div className="shell__main">
        <header className="shell__titlebar" data-tauri-drag-region>
          <span className="shell__mark" aria-hidden>
            G
          </span>
          <span className="shell__product">Genesis Client</span>
          <span className="shell__stage">Foundation · Stage 1</span>
        </header>
        <div className="shell__content">{children}</div>
      </div>
    </div>
  );
}
