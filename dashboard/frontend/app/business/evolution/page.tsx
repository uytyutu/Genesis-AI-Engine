"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BRAND_NAME } from "../../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type BusinessImpact = {
  clients_affected_estimate?: number;
  error_reduction_percent_estimate?: number;
  risk?: string;
  sales_impact?: string;
  sales_impact_label?: string;
};

type Proposal = {
  proposal_id: string;
  ticket_id: string;
  status: string;
  problem: string;
  analysis: string;
  suggested_fix: string;
  diff_preview: string;
  diff_summary?: string;
  risk: string;
  confidence_percent?: number;
  confidence_basis?: string[];
  business_impact?: BusinessImpact;
  rollback_available?: boolean;
  rule_candidate_pending?: boolean;
  tests_planned: string[];
  security_suite: string;
  similar_case_ids: string[];
  created_at: string;
  owner_note?: string;
};

type LearningItem = {
  learning_id: string;
  proposal_id: string;
  knowledge_id: string;
  status: string;
  note?: string;
  problem?: string;
  solution?: string;
  awaits_second_confirm?: boolean;
};

/**
 * G3.1 — Owner quality operations (recommend only · Owner approves).
 */
export default function EvolutionCenterPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [learning, setLearning] = useState<LearningItem[]>([]);
  const [selected, setSelected] = useState<Proposal | null>(null);
  const [ledgerCount, setLedgerCount] = useState(0);
  const [demoMessage, setDemoMessage] = useState(
    "У меня не работает форма на сайте.",
  );
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [pRes, lRes] = await Promise.all([
        fetch(`${API}/api/owner/evolution/proposals`),
        fetch(`${API}/api/owner/evolution/ledger`),
      ]);
      if (pRes.ok) {
        const body = await pRes.json();
        setProposals(body.proposals ?? []);
      } else {
        setError("Owner API unavailable (localhost / owner gate).");
      }
      if (lRes.ok) {
        const body = await lRes.json();
        setLedgerCount((body.entries ?? []).length);
        setLearning(body.learning_queue ?? []);
      }
    } catch {
      setError("Cannot reach API.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const submitDemo = async () => {
    setBusy("submit");
    setMsg("");
    try {
      const res = await fetch(`${API}/api/public/evolution/tickets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: demoMessage, contact: "demo@client.test" }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMsg(body.detail ?? "Submit failed");
        return;
      }
      setMsg(
        `Ticket ${body.ticket?.ticket_id} → proposal ${body.proposal?.proposal_id} (not applied)`,
      );
      await refresh();
      if (body.proposal) setSelected(body.proposal);
    } finally {
      setBusy(null);
    }
  };

  const decide = async (action: "approve" | "reject") => {
    if (!selected) return;
    setBusy(action);
    setMsg("");
    try {
      const res = await fetch(
        `${API}/api/owner/evolution/proposals/${selected.proposal_id}/${action}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            owner_note: action === "approve" ? "Owner OK" : "Rejected",
          }),
        },
      );
      const body = await res.json();
      if (!res.ok) {
        setMsg(body.detail ?? "Decision failed");
        return;
      }
      setMsg(
        action === "approve"
          ? `Approved → Rule Candidate (ожидает второго подтверждения). Код не применён.`
          : `Rejected — no platform change.`,
      );
      setSelected(body.proposal ?? null);
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const ruleSecond = async (learningId: string, action: "promote" | "dismiss") => {
    setBusy(action);
    setMsg("");
    try {
      const res = await fetch(
        `${API}/api/owner/evolution/learning/${learningId}/${action}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            owner_note:
              action === "promote" ? "Confirm rule" : "Dismiss candidate",
          }),
        },
      );
      const body = await res.json();
      if (!res.ok) {
        setMsg(body.detail ?? "Rule decision failed");
        return;
      }
      setMsg(
        action === "promote"
          ? `Rule promoted → Knowledge Ledger (still not auto-applied).`
          : `Rule Candidate dismissed — not in ledger.`,
      );
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const candidates = learning.filter((l) => l.status === "candidate");
  const impact = selected?.business_impact;

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-8">
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/30 via-genesis-panel to-genesis-bg p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-400/80">
            {BRAND_NAME} · G3.1
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-white">
            Evolution · AI Support Center
          </h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Evolution Center не создаёт новые функции. Он делает существующую
            платформу безопаснее, стабильнее, полезнее и умнее на основе
            подтверждённого опыта.
          </p>
          <p className="mt-3 text-xs text-amber-100/90">
            Rule:{" "}
            <strong>
              AI may recommend changes. Only the Owner approves changes.
            </strong>
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-xs text-zinc-400">
            <span>Ledger entries: {ledgerCount}</span>
            <span>Rule candidates: {candidates.length}</span>
            <Link href="/business" className="text-emerald-300 hover:underline">
              ← Business Health
            </Link>
          </div>
        </header>

        {error ? (
          <p className="rounded-xl border border-rose-500/30 bg-rose-950/30 px-4 py-3 text-sm text-rose-100">
            {error}
          </p>
        ) : null}
        {msg ? (
          <p className="rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-zinc-200">
            {msg}
          </p>
        ) : null}

        <section className="rounded-2xl border border-white/10 bg-genesis-panel p-5">
          <h2 className="text-lg font-semibold text-white">Simulate client ticket</h2>
          <textarea
            className="mt-3 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
            rows={3}
            value={demoMessage}
            onChange={(e) => setDemoMessage(e.target.value)}
          />
          <button
            type="button"
            disabled={busy !== null}
            onClick={() => void submitDemo()}
            className="mt-3 rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-50"
          >
            {busy === "submit" ? "Analyzing…" : "Submit → Analyze → Propose"}
          </button>
        </section>

        {candidates.length > 0 ? (
          <section className="rounded-2xl border border-amber-500/25 bg-amber-950/20 p-5">
            <h2 className="text-lg font-semibold text-white">
              Rule Candidate — ожидает подтверждения
            </h2>
            <p className="mt-1 text-xs text-zinc-400">
              После Approve правило ещё не в базе знаний. Нужно второе
              подтверждение Owner.
            </p>
            <ul className="mt-3 space-y-3">
              {candidates.map((c) => (
                <li
                  key={c.learning_id}
                  className="rounded-xl border border-white/10 bg-black/30 px-3 py-3 text-sm"
                >
                  <p className="font-medium text-white">{c.learning_id}</p>
                  <p className="mt-1 text-zinc-400">{c.problem}</p>
                  <p className="mt-1 text-xs text-amber-100/80">
                    Rule Candidate: Да · Ожидает подтверждения
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={busy !== null}
                      onClick={() => void ruleSecond(c.learning_id, "promote")}
                      className="rounded-xl bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-50"
                    >
                      Confirm → Knowledge Ledger
                    </button>
                    <button
                      type="button"
                      disabled={busy !== null}
                      onClick={() => void ruleSecond(c.learning_id, "dismiss")}
                      className="rounded-xl border border-white/20 px-3 py-1.5 text-xs text-white disabled:opacity-50"
                    >
                      Dismiss
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-2xl border border-white/10 bg-genesis-panel p-5">
            <h2 className="text-lg font-semibold text-white">Change proposals</h2>
            <ul className="mt-3 max-h-96 space-y-2 overflow-auto">
              {proposals.length === 0 ? (
                <li className="text-sm text-zinc-500">No proposals yet.</li>
              ) : (
                proposals.map((p) => (
                  <li key={p.proposal_id}>
                    <button
                      type="button"
                      onClick={() => setSelected(p)}
                      className={`w-full rounded-xl border px-3 py-2 text-left text-sm ${
                        selected?.proposal_id === p.proposal_id
                          ? "border-emerald-500/40 bg-emerald-950/30"
                          : "border-white/10 bg-black/20 hover:bg-white/5"
                      }`}
                    >
                      <span className="font-medium text-white">{p.proposal_id}</span>
                      <span className="ml-2 text-xs text-zinc-400">{p.status}</span>
                      {typeof p.confidence_percent === "number" ? (
                        <span className="ml-2 text-xs text-emerald-300/80">
                          {p.confidence_percent}%
                        </span>
                      ) : null}
                      <p className="mt-1 line-clamp-2 text-zinc-400">{p.problem}</p>
                    </button>
                  </li>
                ))
              )}
            </ul>
          </section>

          <section className="rounded-2xl border border-white/10 bg-genesis-panel p-5">
            <h2 className="text-lg font-semibold text-white">Proposal detail</h2>
            {!selected ? (
              <p className="mt-3 text-sm text-zinc-500">Select a proposal.</p>
            ) : (
              <div className="mt-3 space-y-3 text-sm text-zinc-300">
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-3">
                  <p className="text-xs uppercase tracking-wide text-emerald-300/80">
                    Analysis Confidence
                  </p>
                  <p className="mt-1 text-2xl font-semibold text-white">
                    {selected.confidence_percent ?? "—"}%
                  </p>
                  <ul className="mt-2 space-y-1 text-xs text-zinc-400">
                    {(selected.confidence_basis || []).map((b) => (
                      <li key={b}>✓ {b}</li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <p className="text-xs uppercase tracking-wide text-zinc-500">
                    Business Impact
                  </p>
                  <dl className="mt-2 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <dt className="text-zinc-500">Клиентов затронуто</dt>
                      <dd className="text-white">
                        {impact?.clients_affected_estimate ?? "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-zinc-500">Ожидаемое снижение ошибок</dt>
                      <dd className="text-white">
                        {impact?.error_reduction_percent_estimate != null
                          ? `${impact.error_reduction_percent_estimate}%`
                          : "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-zinc-500">Риск</dt>
                      <dd className="text-white capitalize">
                        {impact?.risk ?? selected.risk}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-zinc-500">Влияние на продажи</dt>
                      <dd className="text-white">
                        {impact?.sales_impact_label ?? "—"}
                      </dd>
                    </div>
                  </dl>
                </div>

                <p>
                  <span className="text-zinc-500">Rollback:</span>{" "}
                  {selected.rollback_available === false ? "Нет" : "Да · доступен"}
                </p>

                <div>
                  <p className="text-xs uppercase text-zinc-500">Diff Summary</p>
                  <p className="mt-1">
                    {selected.diff_summary ||
                      "Человеческое описание изменений отсутствует."}
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase text-zinc-500">Analysis</p>
                  <p className="mt-1">{selected.analysis}</p>
                </div>
                <div>
                  <p className="text-xs uppercase text-zinc-500">Suggested fix</p>
                  <p className="mt-1">{selected.suggested_fix}</p>
                </div>
                <div>
                  <p className="text-xs uppercase text-zinc-500">Technical diff</p>
                  <pre className="mt-1 overflow-auto rounded-lg bg-black/50 p-2 text-xs text-emerald-100/90">
                    {selected.diff_preview}
                  </pre>
                </div>
                <div>
                  <p className="text-xs uppercase text-zinc-500">Tests · Security Suite</p>
                  <p className="mt-1 text-xs">
                    {(selected.tests_planned || []).join(" · ")}
                  </p>
                  <p className="text-xs text-zinc-500">{selected.security_suite}</p>
                </div>
                {selected.similar_case_ids?.length ? (
                  <p className="text-xs text-zinc-400">
                    Similar cases: {selected.similar_case_ids.join(", ")}
                  </p>
                ) : null}
                {selected.rule_candidate_pending ? (
                  <p className="text-xs text-amber-100/90">
                    Rule Candidate: Да · Ожидает подтверждения (см. блок выше)
                  </p>
                ) : null}
                {selected.status === "pending_owner" ? (
                  <div className="flex flex-wrap gap-2 pt-2">
                    <button
                      type="button"
                      disabled={busy !== null}
                      onClick={() => void decide("approve")}
                      className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
                    >
                      Approve → Rule Candidate
                    </button>
                    <button
                      type="button"
                      disabled={busy !== null}
                      onClick={() => void decide("reject")}
                      className="rounded-xl border border-white/20 px-4 py-2 text-sm text-white disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                ) : (
                  <p className="text-xs text-zinc-500">
                    Status: {selected.status} — platform code was not auto-modified.
                  </p>
                )}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
