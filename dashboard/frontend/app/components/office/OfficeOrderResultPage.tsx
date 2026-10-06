"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  continueOfficeJob,
  downloadOfficeArtifact,
  getOfficeJob,
  type OfficeJobView,
} from "../../lib/officeApi";
import { publicApiBase } from "../../lib/publicApiBase";
import {
  getOfficeJobToken,
  saveOfficeJobToken,
  updateOfficeJobTokenMeta,
} from "../../lib/officeSession";
import { useOfficeT } from "../../lib/useOfficeT";
import { OfficeOrderProgress } from "./OfficeOrderProgress";
import { OfficeShell } from "./OfficeShell";

const DT_KEY = (jobId: string) => `virtus_office_dt_${jobId}`;

export function OfficeOrderResultPage({ jobId }: { jobId: string }) {
  const { t } = useOfficeT();
  const [job, setJob] = useState<OfficeJobView | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [deliveryToken, setDeliveryToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const ranExecute = useRef(false);

  useEffect(() => {
    const stored = getOfficeJobToken(jobId);
    setToken(stored);
    let dt: string | null = null;
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      dt = params.get("dt");
      if (dt) {
        try {
          sessionStorage.setItem(DT_KEY(jobId), dt);
        } catch {
          /* ignore */
        }
      } else {
        try {
          dt = sessionStorage.getItem(DT_KEY(jobId));
        } catch {
          dt = null;
        }
      }
    }
    setDeliveryToken(dt);
    let cancelled = false;
    (async () => {
      try {
        if (dt) {
          const res = await fetch(
            `${publicApiBase()}/api/office/jobs/${encodeURIComponent(jobId)}/claim-delivery`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ delivery_token: dt }),
            },
          );
          const data = (await res.json()) as OfficeJobView;
          if (!res.ok) throw new Error(t("errors.deliveryLinkInvalid"));
          if (!cancelled) setJob(data);
          return;
        }
        const view = await getOfficeJob(jobId, stored);
        if (cancelled) return;
        setJob(view);
        updateOfficeJobTokenMeta(jobId, {
          filename: view.filename,
          status: view.status,
        });
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : t("errors.generic"));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [jobId, t]);

  useEffect(() => {
    if (!job || ranExecute.current) return;
    const unlocked = Boolean(job.payment?.execute_unlocked || job.payment?.paid);
    const needsRun =
      unlocked &&
      (job.status === "paid" || job.status === "awaiting_payment" || job.status === "proposal_ready");
    if (!needsRun) return;
    ranExecute.current = true;
    setBusy(true);
    continueOfficeJob(jobId, token)
      .then((view) => {
        setJob(view);
        updateOfficeJobTokenMeta(jobId, { status: view.status, filename: view.filename });
      })
      .catch((e) => setError(e instanceof Error ? e.message : t("errors.generic")))
      .finally(() => setBusy(false));
  }, [job, jobId, token, t]);

  async function onDownload(format: string) {
    setError(null);
    try {
      await downloadOfficeArtifact(jobId, token, format, deliveryToken);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"));
    }
  }

  useEffect(() => {
    if (token) saveOfficeJobToken(jobId, token);
  }, [jobId, token]);

  const completed = job?.status === "completed";
  const failed = job?.status === "failed";
  const receiptPath =
    job?.delivery?.receipt_path ||
    (job?.payment?.order_id ? `/order/status/${job.payment.order_id}` : null);

  return (
    <OfficeShell active="cabinet">
      <div className="vo-enter mx-auto max-w-2xl space-y-8">
        <div>
          <Link href="/office/cabinet" className="text-sm text-[var(--vo-muted)] hover:underline">
            ← {t("cabinet.title")}
          </Link>
          <h1 className="vo-display mt-3 text-3xl font-semibold">{t("progress.title")}</h1>
          <p className="mt-1 text-sm text-[var(--vo-muted)]">
            {job?.filename || jobId}
          </p>
        </div>

        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </p>
        ) : null}

        <OfficeOrderProgress steps={job?.progress} />

        {busy ? (
          <p className="text-sm text-[var(--vo-muted)]">{t("progress.working")}</p>
        ) : null}

        {failed ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-900">
            <p className="font-semibold">{t("result.failed")}</p>
            <p className="mt-2">{job?.failure_detail || job?.failure_reason}</p>
          </div>
        ) : null}

        {completed ? (
          <section className="rounded-2xl border border-[var(--vo-ok)]/30 bg-[var(--vo-surface)] p-6">
            <h2 className="vo-display text-2xl font-semibold">{t("result.ready")}</h2>
            <p className="mt-2 text-sm text-[var(--vo-muted)]">{t("result.readyHint")}</p>

            {job?.quality_report ? (
              <div className="mt-5 rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] p-4">
                <p className="text-sm font-semibold text-[var(--vo-ink)]">
                  {t("result.qualityTitle")}
                </p>
                <p
                  className={`mt-2 text-lg font-bold ${
                    job.quality_report.status === "READY"
                      ? "text-[var(--vo-ok)]"
                      : "text-[var(--vo-warn)]"
                  }`}
                >
                  {job.quality_report.status === "READY"
                    ? t("result.qualityReady")
                    : t("result.qualityNotReady")}
                </p>
                <p className="mt-1 text-xs text-[var(--vo-muted)]">
                  {t("result.qualityProblems", {
                    count: job.quality_report.problem_count ?? 0,
                  })}
                </p>
                {(job.quality_report.problems || []).length ? (
                  <ul className="mt-3 space-y-2 text-sm text-[var(--vo-ink)]">
                    {(job.quality_report.problems || []).slice(0, 12).map((p) => (
                      <li key={`${p.code}-${p.title}`} className="rounded-lg border border-[var(--vo-border)]/70 px-3 py-2">
                        <span className="font-semibold uppercase text-[11px] text-[var(--vo-muted)]">
                          {p.severity || "—"}
                        </span>
                        <p className="font-medium">{p.title || p.code}</p>
                        {p.detail ? (
                          <p className="text-xs text-[var(--vo-muted)]">{p.detail}</p>
                        ) : null}
                        {p.fix_hint ? (
                          <p className="mt-1 text-xs text-[var(--vo-accent)]">
                            {t("result.qualityFix")}: {p.fix_hint}
                          </p>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                ) : null}
                <p className="mt-3 text-[11px] text-[var(--vo-muted)]">
                  {t("result.qualityHonesty")}
                </p>
              </div>
            ) : null}

            <div className="mt-5 flex flex-wrap gap-3">
              {(job?.download_formats || [])
                .filter((fmt) => fmt.available)
                .map((fmt) => (
                  <button
                    key={fmt.format}
                    type="button"
                    onClick={() => onDownload(fmt.format)}
                    className="rounded-xl bg-[var(--vo-accent)] px-4 py-3 text-sm font-semibold text-white"
                  >
                    {fmt.label} {t("result.download")}
                  </button>
                ))}
            </div>
            {receiptPath ? (
              <p className="mt-4 text-sm">
                <Link href={receiptPath} className="font-semibold text-[var(--vo-accent)] underline">
                  {t("cabinet.receipt")}
                </Link>
              </p>
            ) : null}
            {(job?.delivery?.email_status && job.delivery.email_status !== "none") ? (
              <p className="mt-2 text-xs text-[var(--vo-muted)]">
                {t("result.emailStatus", { status: job.delivery.email_status })}
              </p>
            ) : null}
          </section>
        ) : null}
      </div>
    </OfficeShell>
  );
}
