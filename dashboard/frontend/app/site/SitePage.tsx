"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../components/PublicPageShell";
import { GenesisConcierge } from "../components/GenesisConcierge";
import { GenesisChatErrorBoundary } from "../components/GenesisChatErrorBoundary";
import { GuidedProgressPanel } from "../components/GuidedProgressPanel";
import { VectorCommerceSteps } from "../components/VectorCommerceSteps";
import { initVectorWorkspace } from "../lib/guidedSiteBootstrap";
import { initPublicSiteSession } from "../lib/visitorId";
import { ASSISTANT_NAME } from "../lib/publicBrand";

/**
 * Product Identity v1.0 — Vector-first workspace.
 * Left: digital employee. Right: live draft + ownership steps.
 */
export function SitePage() {
  const { t: tCommon } = useTranslation("common");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    initPublicSiteSession();
    initVectorWorkspace();
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <PublicPageShell minimal>
        <p className="text-sm text-genesis-muted">Открываем рабочее место…</p>
      </PublicPageShell>
    );
  }

  return (
    <PublicPageShell minimal>
      <p className="mb-3 text-sm text-genesis-muted">
        <span className="font-semibold text-white">{ASSISTANT_NAME}</span> — ваш цифровой сотрудник.
        Просто расскажите в чате о бизнесе и видении — без анкеты. Черновик справа собирается из диалога. Оплата только если результат подходит.
      </p>
      <div className="grid min-h-0 gap-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(300px,42%)] lg:gap-6">
        <section
          id="vector-panel"
          className="order-1 flex min-h-[min(56dvh,32rem)] max-h-[min(62dvh,36rem)] min-w-0 flex-col lg:min-h-0"
          aria-label={tCommon("nav.vector")}
        >
          <GenesisChatErrorBoundary publicMode>
            <GenesisConcierge hubMode />
          </GenesisChatErrorBoundary>
        </section>

        <section
          className="order-2 flex min-h-0 min-w-0 flex-col"
          aria-label="Ваш проект"
        >
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <GuidedProgressPanel />
            <VectorCommerceSteps />
          </div>
        </section>
      </div>
    </PublicPageShell>
  );
}
