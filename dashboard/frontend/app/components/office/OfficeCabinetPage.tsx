"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  downloadOfficeArtifact,
  fetchOfficeCabinet,
  type OfficeCabinet,
} from "../../lib/officeApi";
import { getClientToken } from "../../lib/clientAuth";
import { getOfficeJobToken, listOfficeJobTokens } from "../../lib/officeSession";
import { useOfficeT } from "../../lib/useOfficeT";
import { OfficeShell } from "./OfficeShell";
import { OfficeOrderProgress } from "./OfficeOrderProgress";

type Tab = "orders" | "files" | "invoices" | "downloads";

export function OfficeCabinetPage() {
  const { t } = useOfficeT();
  const [tab, setTab] = useState<Tab>("orders");
  const [data, setData] = useState<OfficeCabinet | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const loggedIn = Boolean(getClientToken());
  const localJobs = listOfficeJobTokens();

  useEffect(() => {
    if (!loggedIn) return;
    setBusy(true);
    fetchOfficeCabinet()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : t("errors.generic")))
      .finally(() => setBusy(false));
  }, [loggedIn, t]);

  async function onDownload(jobId: string, format?: string) {
    try {
      const token = getOfficeJobToken(jobId);
      await downloadOfficeArtifact(jobId, token, format);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"));
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "orders", label: t("cabinet.orders") },
    { id: "files", label: t("cabinet.files") },
    { id: "invoices", label: t("cabinet.invoices") },
    { id: "downloads", label: t("cabinet.downloads") },
  ];

  return (
    <OfficeShell active="cabinet">
      <div className="vo-enter space-y-8">
        <header>
          <p className="text-sm font-medium uppercase tracking-[0.14em] text-[var(--vo-muted)]">
            Virtus Office
          </p>
          <h1 className="vo-display mt-2 text-4xl font-semibold tracking-tight">
            {t("cabinet.title")}
          </h1>
          <p className="mt-2 max-w-2xl text-[var(--vo-muted)]">{t("cabinet.subtitle")}</p>
        </header>

        {!loggedIn ? (
          <div className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-6">
            <p className="text-sm text-[var(--vo-muted)]">{t("cabinet.loginHint")}</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                href="/client/login"
                className="rounded-xl bg-[var(--vo-accent)] px-4 py-2 text-sm font-semibold text-white"
              >
                {t("cabinet.login")}
              </Link>
              {localJobs.length ? (
                <p className="text-sm text-[var(--vo-muted)]">
                  {t("cabinet.localJobs", { count: localJobs.length })}
                </p>
              ) : null}
            </div>
            {localJobs.length ? (
              <ul className="mt-6 space-y-3">
                {localJobs.map((row) => (
                  <li
                    key={row.job_id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--vo-border)] px-4 py-3"
                  >
                    <div>
                      <p className="font-medium">{row.filename || row.job_id}</p>
                      <p className="text-xs text-[var(--vo-muted)]">{row.status || "—"}</p>
                    </div>
                    <Link
                      href={`/office/order/${encodeURIComponent(row.job_id)}`}
                      className="text-sm font-semibold text-[var(--vo-accent)]"
                    >
                      {t("cabinet.open")}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : (
          <>
            <div className="flex flex-wrap gap-2">
              {tabs.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setTab(item.id)}
                  className={`rounded-xl px-3 py-2 text-sm font-medium ${
                    tab === item.id
                      ? "bg-[var(--vo-accent-soft)] text-[var(--vo-accent)]"
                      : "text-[var(--vo-muted)] hover:bg-black/[0.03]"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            {error ? (
              <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                {error}
              </p>
            ) : null}
            {busy ? <p className="text-sm text-[var(--vo-muted)]">{t("analyzing")}</p> : null}

            {tab === "orders" ? (
              <ul className="space-y-4">
                {(data?.jobs || []).map((job) => (
                  <li
                    key={job.job_id}
                    className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-5"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold">
                          {job.task_label_de || job.task || job.filename || job.job_id}
                        </p>
                        <p className="mt-1 text-xs text-[var(--vo-muted)]">
                          {job.status}
                          {job.price_eur != null ? ` · ${Number(job.price_eur).toFixed(2)} €` : ""}
                        </p>
                      </div>
                      <Link
                        href={`/office/order/${encodeURIComponent(job.job_id)}`}
                        className="text-sm font-semibold text-[var(--vo-accent)]"
                      >
                        {t("cabinet.open")}
                      </Link>
                    </div>
                    <div className="mt-4">
                      <OfficeOrderProgress steps={job.progress} />
                    </div>
                    {job.failure_detail ? (
                      <p className="mt-3 text-sm text-red-700">{job.failure_detail}</p>
                    ) : null}
                  </li>
                ))}
                {!busy && !(data?.jobs || []).length ? (
                  <p className="text-sm text-[var(--vo-muted)]">{t("cabinet.empty")}</p>
                ) : null}
              </ul>
            ) : null}

            {tab === "files" ? (
              <ul className="space-y-3">
                {(data?.files || []).map((f) => (
                  <li
                    key={String(f.job_id)}
                    className="flex justify-between gap-3 rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] px-4 py-3 text-sm"
                  >
                    <span>{String(f.artifact_filename || f.filename || f.job_id)}</span>
                    <span className="text-[var(--vo-muted)]">{String(f.status || "")}</span>
                  </li>
                ))}
              </ul>
            ) : null}

            {tab === "invoices" ? (
              <ul className="space-y-3">
                {(data?.invoices || []).map((inv) => (
                  <li
                    key={String(inv.order_id)}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] px-4 py-3 text-sm"
                  >
                    <div>
                      <p className="font-medium">{inv.package_name || inv.order_id}</p>
                      <p className="text-xs text-[var(--vo-muted)]">
                        {inv.price_label ||
                          (inv.price_eur != null ? `${inv.price_eur} €` : "")}{" "}
                        · {inv.status}
                      </p>
                    </div>
                    {inv.receipt_path ? (
                      <Link
                        href={inv.receipt_path}
                        className="font-semibold text-[var(--vo-accent)]"
                      >
                        {t("cabinet.receipt")}
                      </Link>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : null}

            {tab === "downloads" ? (
              <ul className="space-y-3">
                {(data?.downloads || []).map((d) => {
                  const jobId = String(d.job_id || "");
                  const ext = String(d.artifact_ext || "").toLowerCase();
                  return (
                    <li
                      key={jobId}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] px-4 py-3 text-sm"
                    >
                      <span>{String(d.artifact_filename || d.filename || jobId)}</span>
                      <button
                        type="button"
                        onClick={() => onDownload(jobId, ext || undefined)}
                        className="rounded-lg bg-[var(--vo-accent)] px-3 py-1.5 font-semibold text-white"
                      >
                        {t("result.download")} {ext ? ext.toUpperCase() : ""}
                      </button>
                    </li>
                  );
                })}
              </ul>
            ) : null}
          </>
        )}
      </div>
    </OfficeShell>
  );
}
