"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PublicPageShell } from "../components/PublicPageShell";
import { GenesisConcierge } from "../components/GenesisConcierge";
import { GenesisChatErrorBoundary } from "../components/GenesisChatErrorBoundary";
import { LeadCapturePanel } from "../components/LeadCapturePanel";
import { initPublicSiteSession } from "../lib/visitorId";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import { normalizeLeadNiche, type LeadNiche } from "../lib/leadDialogEngine";

/**
 * Model 3 — chat-only lead trap. No website factory, no forms.
 * Traffic: /capture?niche=autoservice
 */
export function CapturePage() {
  const searchParams = useSearchParams();
  const niche = useMemo(
    () => normalizeLeadNiche(searchParams.get("niche")),
    [searchParams],
  );
  const [ready, setReady] = useState(false);

  useEffect(() => {
    initPublicSiteSession();
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <PublicPageShell minimal>
        <p className="text-sm text-genesis-muted">Открываем приём заявок…</p>
      </PublicPageShell>
    );
  }

  return (
    <PublicPageShell minimal>
      <p className="mb-3 text-sm text-genesis-muted">
        <span className="font-semibold text-white">{ASSISTANT_NAME}</span> принимает заявки 24/7.
        Напишите проблему — система сама оформит горячий лид для партнёра. Без сайта и без анкеты.
      </p>
      <div className="grid min-h-0 gap-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(280px,36%)] lg:gap-6">
        <section className="order-1 flex min-h-[min(56dvh,32rem)] max-h-[min(62dvh,36rem)] min-w-0 flex-col lg:min-h-0">
          <GenesisChatErrorBoundary publicMode>
            <GenesisConcierge leadCapture={{ niche: niche as LeadNiche }} />
          </GenesisChatErrorBoundary>
        </section>
        <section className="order-2 flex min-h-0 min-w-0 flex-col rounded-2xl border border-white/10 bg-genesis-panel/40 p-4">
          <LeadCapturePanel niche={niche} />
        </section>
      </div>
    </PublicPageShell>
  );
}
