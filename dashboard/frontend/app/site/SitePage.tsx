"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { GenesisConcierge } from "../components/GenesisConcierge";
import { GenesisChatErrorBoundary } from "../components/GenesisChatErrorBoundary";
import { GuidedCommerceFlow } from "../components/GuidedCommerceFlow";
import { GuidedProgressPanel } from "../components/GuidedProgressPanel";
import { initPublicSiteSession } from "../lib/visitorId";

export function SitePage() {
  const { t: tCommon } = useTranslation("common");
  const searchParams = useSearchParams();
  const vectorView = searchParams.get("view") === "vector";
  const chatView = searchParams.get("view") === "chat";
  const [ready, setReady] = useState(false);
  const [showChat, setShowChat] = useState(chatView);

  useEffect(() => {
    initPublicSiteSession();
    setReady(true);
  }, []);

  useEffect(() => {
    setShowChat(chatView);
  }, [chatView]);

  if (!ready) {
    return (
      <PublicPageShell minimal>
        <p className="text-sm text-genesis-muted">Открываем ваш кабинет…</p>
      </PublicPageShell>
    );
  }

  const useGuided = !showChat && !vectorView;

  return (
    <PublicPageShell minimal>
      <div
        className={`grid min-h-0 gap-3 lg:gap-4 ${
          vectorView
            ? "grid-cols-1"
            : "min-h-0 gap-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(300px,42%)] lg:gap-6"
        }`}
      >
        <section
          id="vector-panel"
          className={`flex min-w-0 flex-col lg:min-h-0 ${
            vectorView
              ? "order-2 min-h-[min(56dvh,32rem)] max-h-[min(62dvh,36rem)]"
              : "order-1 min-h-[min(56dvh,32rem)] max-h-[min(62dvh,36rem)]"
          }`}
          aria-label={tCommon("nav.vector")}
        >
          {useGuided ? (
            <GuidedCommerceFlow
              onNeedHelp={() => {
                setShowChat(true);
                window.history.replaceState(null, "", "/site?view=chat");
              }}
            />
          ) : (
            <GenesisChatErrorBoundary publicMode>
              <GenesisConcierge hubMode={!vectorView} />
            </GenesisChatErrorBoundary>
          )}
        </section>

        <section
          className={`min-h-0 ${
            vectorView ? "order-1 mb-2 min-h-[14rem] max-h-[42dvh]" : "order-2"
          }`}
          aria-label="Проект"
        >
          <GuidedProgressPanel compact={vectorView} />
        </section>
      </div>
    </PublicPageShell>
  );
}
