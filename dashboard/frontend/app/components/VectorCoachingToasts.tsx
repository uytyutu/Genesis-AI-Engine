"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { publicApiBase } from "../lib/publicApiBase";

type CoachNote = {
  id: string;
  title: string;
  body: string;
  action_label?: string;
  href?: string;
  ttl_sec?: number;
};

/**
 * Vector as ephemeral coaching notifications — appears, teaches, auto-dismisses.
 * Not a chat dock.
 */
export function VectorCoachingToasts() {
  const [notes, setNotes] = useState<CoachNote[]>([]);
  const [visibleId, setVisibleId] = useState<string | null>(null);

  useEffect(() => {
    if (!getClientToken()) return;
    let cancelled = false;
    const api = publicApiBase();
    void fetch(`${api}/api/client/vector-coaching`, {
      headers: { ...clientAuthHeaders() },
      cache: "no-store",
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        if (cancelled || !body?.notifications) return;
        const list = body.notifications as CoachNote[];
        setNotes(list);
        if (list[0]) setVisibleId(list[0].id);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!visibleId || notes.length === 0) return;
    const note = notes.find((n) => n.id === visibleId) || notes[0];
    const ttl = Math.max(6, Math.min(20, note?.ttl_sec || 12)) * 1000;
    const t = window.setTimeout(() => {
      const idx = notes.findIndex((n) => n.id === visibleId);
      const next = notes[idx + 1];
      setVisibleId(next ? next.id : null);
    }, ttl);
    return () => window.clearTimeout(t);
  }, [visibleId, notes]);

  const current = notes.find((n) => n.id === visibleId);
  if (!current) return null;

  return (
    <div
      className="pointer-events-none fixed inset-x-0 bottom-20 z-40 flex justify-center px-3 sm:bottom-6 sm:justify-end sm:px-6"
      role="status"
      aria-live="polite"
    >
      <div className="pointer-events-auto w-full max-w-sm rounded-2xl border border-emerald-400/30 bg-zinc-950/95 p-4 shadow-xl shadow-black/40 backdrop-blur">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-300/90">
          Vector
        </p>
        <p className="mt-1 text-sm font-semibold text-white">{current.title}</p>
        <p className="mt-1 text-xs leading-relaxed text-zinc-300">{current.body}</p>
        <div className="mt-3 flex items-center justify-between gap-2">
          {current.href ? (
            <Link
              href={current.href}
              className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-black"
            >
              {current.action_label || "Öffnen"}
            </Link>
          ) : (
            <span />
          )}
          <button
            type="button"
            className="text-xs text-zinc-400 hover:text-white"
            onClick={() => {
              const idx = notes.findIndex((n) => n.id === visibleId);
              const next = notes[idx + 1];
              setVisibleId(next ? next.id : null);
            }}
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  );
}
