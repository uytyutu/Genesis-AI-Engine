"use client";

import { useEffect, useState } from "react";
import { ASSISTANT_NAME } from "../lib/publicBrand";
import {
  LEAD_CAPTURE_EVENT,
  leadGaps,
  leadKnownSummary,
  leadNicheLabel,
  loadLeadCapture,
  pickLeadFollowUp,
  type LeadCaptureState,
  type LeadNiche,
} from "../lib/leadDialogEngine";

type Props = {
  niche: LeadNiche;
};

const GAP_LABEL: Record<string, string> = {
  problem: "проблема",
  location: "локация",
  contact: "контакт",
  urgency: "срочность",
};

export function LeadCapturePanel({ niche }: Props) {
  const [state, setState] = useState<LeadCaptureState>(() => loadLeadCapture(niche));

  useEffect(() => {
    const sync = (e: Event) => {
      const detail = (e as CustomEvent<LeadCaptureState>).detail;
      if (detail) setState(detail);
      else setState(loadLeadCapture(niche));
    };
    window.addEventListener(LEAD_CAPTURE_EVENT, sync);
    return () => window.removeEventListener(LEAD_CAPTURE_EVENT, sync);
  }, [niche]);

  const known = leadKnownSummary(state);
  const gaps = leadGaps(state);
  const followUp = pickLeadFollowUp(state);

  return (
    <div className="mt-3 shrink-0 space-y-3 border-t border-white/8 pt-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-genesis-accent">
        Заявка · {leadNicheLabel(state.niche)}
      </p>

      {known.length ? (
        <ul className="space-y-1 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-[11px] text-genesis-muted">
          {known.map((line) => (
            <li key={line}>
              <span className="text-emerald-300/90">✓</span> {line}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-genesis-muted">
          Опишите проблему {ASSISTANT_NAME} — без формы. Он сам соберёт заявку.
        </p>
      )}

      {state.hot && state.leadId ? (
        <p className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-100">
          Горячая заявка принята · {state.score}% · ID {state.leadId}
        </p>
      ) : gaps.length ? (
        <p className="text-[11px] leading-relaxed text-genesis-muted">
          {ASSISTANT_NAME} уточнит в чате
          {followUp ? `: «${followUp}»` : ` — не хватает: ${gaps.map((g) => GAP_LABEL[g] ?? g).join(", ")}`}
        </p>
      ) : (
        <p className="text-xs text-genesis-accent">Проверяем заявку…</p>
      )}
    </div>
  );
}
