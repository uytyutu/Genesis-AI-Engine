import type { ReactNode } from "react";
import { Sidebar, type NavId } from "./Sidebar";
import { GenesisMark } from "./GenesisMark";
import { VectorStatus } from "./VectorStatus";
import { useI18n } from "../i18n/I18nProvider";

type ShellProps = {
  active: NavId;
  ownerLabel: string;
  connected: boolean;
  customerMode?: boolean;
  vectorThinking?: boolean;
  onNavigate: (id: NavId) => void;
  onDisconnect: () => void;
  onOpenPalette: () => void;
  children: ReactNode;
};

export function Shell({
  active,
  ownerLabel,
  connected,
  customerMode = false,
  vectorThinking = false,
  onNavigate,
  onDisconnect,
  onOpenPalette,
  children,
}: ShellProps) {
  const { t } = useI18n();

  return (
    <div className="shell">
      <Sidebar
        active={active}
        ownerLabel={ownerLabel}
        connected={connected}
        customerMode={customerMode}
        vectorThinking={vectorThinking}
        onNavigate={onNavigate}
        onDisconnect={onDisconnect}
      />
      <div className="shell__main">
        <header className="shell__titlebar" data-tauri-drag-region>
          {customerMode ? (
            <VectorStatus connected={connected} thinking={vectorThinking} />
          ) : (
            <>
              <span className="shell__mark" aria-hidden>
                <GenesisMark className="shell__mark-svg" />
              </span>
              <span className="shell__product">{t("app.product")}</span>
            </>
          )}
          {!customerMode ? (
            <span
              className={`shell__conn${connected ? " is-online" : ""}`}
              title={connected ? t("shell.online") : t("shell.offline")}
            >
              {connected ? t("shell.online") : t("shell.offline")}
            </span>
          ) : null}
      {!customerMode ? (
        <button
          type="button"
          className="shell__palette"
          onClick={onOpenPalette}
          title={t("shell.palette")}
        >
          <kbd>Ctrl</kbd>+<kbd>K</kbd>
        </button>
      ) : null}
        </header>
        <div className="shell__content">{children}</div>
      </div>
    </div>
  );
}
