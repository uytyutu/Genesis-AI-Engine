import { useState } from "react";
import { CursorHandoffPanel } from "../components/CursorHandoffPanel";
import { DevWorkspacePanel } from "../components/DevWorkspacePanel";
import { useI18n } from "../i18n/I18nProvider";

type StudioTab = "handoff" | "workspace";

export function DevStudioPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState<StudioTab>("handoff");

  return (
    <div className="page page--wide">
      <header className="page__header">
        <h1>{t("nav.studio")}</h1>
        <p>{t("nav.studio.hint")}</p>
      </header>

      <div className="studio-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "handoff"}
          className={`studio-tabs__btn${tab === "handoff" ? " is-active" : ""}`}
          onClick={() => setTab("handoff")}
        >
          {t("studio.tab.handoff")}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "workspace"}
          className={`studio-tabs__btn${tab === "workspace" ? " is-active" : ""}`}
          onClick={() => setTab("workspace")}
        >
          {t("studio.tab.workspace")}
        </button>
      </div>

      {tab === "handoff" ? <CursorHandoffPanel /> : <DevWorkspacePanel />}
    </div>
  );
}
