"use client";

/**
 * Website Chat preview harness — Live channel browser smoke.
 * /spike/website-chat?key=wc_...
 */

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

declare global {
  interface Window {
    VirtusWebsiteChat?: {
      mount: (opts: { key: string; endpoint?: string }) => HTMLElement | null;
    };
  }
}

function SpikeInner() {
  const search = useSearchParams();
  const key = (search.get("key") || "").trim();
  const label = search.get("label") || "Demo website";
  const tenant = search.get("tenant") || "";
  const [mounted, setMounted] = useState(false);

  const hint = useMemo(() => {
    if (!key) return "Missing ?key=wc_… — create a connection from Client Workspace first.";
    return `Preview site for key ${key.slice(0, 12)}…`;
  }, [key]);

  useEffect(() => {
    if (!key) return;
    let cancelled = false;

    function ensureMount() {
      if (cancelled) return;
      if (window.VirtusWebsiteChat?.mount) {
        window.VirtusWebsiteChat.mount({ key });
        setMounted(true);
        return true;
      }
      return false;
    }

    if (ensureMount()) return;

    const existing = document.querySelector(
      'script[src="/widget/website-chat.js"]',
    ) as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", () => ensureMount());
      ensureMount();
      return () => {
        cancelled = true;
      };
    }

    const s = document.createElement("script");
    s.src = "/widget/website-chat.js";
    s.async = true;
    s.onload = () => ensureMount();
    document.body.appendChild(s);
    return () => {
      cancelled = true;
    };
  }, [key]);

  return (
    <main className="min-h-screen bg-[#071018] text-zinc-100">
      <div className="mx-auto max-w-3xl px-6 py-16 space-y-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300/80">
          Virtus Website Chat · Live preview
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">{label}</h1>
        <p className="text-sm text-zinc-400">{hint}</p>
        {tenant ? (
          <p className="text-xs text-zinc-500" data-testid="tenant-label">
            Tenant: {tenant}
          </p>
        ) : null}
        <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 space-y-3">
          <p className="text-sm text-zinc-300">
            This page simulates a customer website. Open the Chat button and send a message.
          </p>
          <p className="text-xs text-emerald-200/90">
            Commercial status: Live — Telegram + Website Chat. WhatsApp / Instagram / Messenger —
            Coming Soon.
          </p>
          {!key ? (
            <p className="text-sm text-rose-200">Provide a public key to mount the widget.</p>
          ) : (
            <>
              <p className="font-mono text-xs text-zinc-500" data-testid="public-key">
                {key}
              </p>
              <p className="text-xs text-zinc-500" data-testid="widget-mounted">
                Widget: {mounted ? "mounted" : "loading…"}
              </p>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

export default function WebsiteChatSpikePage() {
  return (
    <Suspense fallback={<p className="p-10 text-center text-zinc-400">Loading preview…</p>}>
      <SpikeInner />
    </Suspense>
  );
}
