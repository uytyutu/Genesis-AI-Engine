"use client";

import { useMemo, useState } from "react";
import { generateOfficeQr, type OfficeQrResult } from "../../lib/officeApi";
import { useOfficeT } from "../../lib/useOfficeT";
import { OfficeShell } from "./OfficeShell";

const QR_TYPES = ["url", "whatsapp", "maps", "email", "phone", "text", "wifi", "vcard"] as const;
type QrType = (typeof QR_TYPES)[number];

const TYPE_FIELDS: Record<QrType, string[]> = {
  url: ["url"],
  whatsapp: ["phone", "message"],
  maps: ["address"],
  email: ["email", "subject", "message"],
  phone: ["phone"],
  text: ["text"],
  wifi: ["ssid", "password", "security"],
  vcard: ["name", "company", "phone", "email", "url"],
};

export function OfficeQrPage() {
  const { t } = useOfficeT();
  const [qrType, setQrType] = useState<QrType>("url");
  const [fields, setFields] = useState<Record<string, string>>({});
  const [result, setResult] = useState<OfficeQrResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const visibleFields = useMemo(() => TYPE_FIELDS[qrType], [qrType]);

  async function onGenerate() {
    if (!visibleFields.some((field) => fields[field]?.trim())) {
      setError(t("qr.required"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setResult(await generateOfficeQr({ qr_type: qrType, fields }));
    } catch (e) {
      setError(e instanceof Error ? e.message : t("qr.error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <OfficeShell active="qr">
      <section className="vo-enter grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <div className="inline-flex rounded-full bg-[var(--vo-ok)] px-3 py-1 text-xs font-bold text-white">
            {t("qr.freeBadge")}
          </div>
          <h1 className="vo-display mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">
            {t("qr.title")}
          </h1>
          <p className="mt-4 max-w-xl text-lg leading-relaxed text-[var(--vo-muted)]">
            {t("qr.lead")}
          </p>
        </div>

        <div className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-6 shadow-[0_16px_40px_rgba(24,32,51,0.08)]">
          <label className="block text-sm font-semibold text-[var(--vo-ink)]">
            {t("qr.typeLabel")}
            <select
              value={qrType}
              onChange={(e) => {
                setQrType(e.target.value as QrType);
                setFields({});
                setResult(null);
              }}
              className="mt-2 w-full rounded-xl border border-[var(--vo-border)] bg-white px-3 py-3 text-sm"
            >
              {QR_TYPES.map((type) => (
                <option key={type} value={type}>
                  {t(`qr.types.${type}`)}
                </option>
              ))}
            </select>
          </label>

          <div className="mt-5 grid gap-4">
            {visibleFields.map((field) => (
              <label key={field} className="block text-xs font-semibold text-[var(--vo-muted)]">
                {t(`qr.fields.${field}`)}
                {field === "message" || field === "text" ? (
                  <textarea
                    rows={4}
                    value={fields[field] || ""}
                    onChange={(e) => setFields((current) => ({ ...current, [field]: e.target.value }))}
                    className="mt-1 w-full resize-y rounded-xl border border-[var(--vo-border)] bg-white px-3 py-2.5 text-sm text-[var(--vo-ink)]"
                  />
                ) : (
                  <input
                    value={fields[field] || ""}
                    onChange={(e) => setFields((current) => ({ ...current, [field]: e.target.value }))}
                    className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-white px-3 py-2.5 text-sm text-[var(--vo-ink)]"
                  />
                )}
              </label>
            ))}
          </div>

          {error ? (
            <p className="mt-4 rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-900">
              {error}
            </p>
          ) : null}

          <button
            type="button"
            onClick={onGenerate}
            disabled={busy}
            className="mt-6 w-full rounded-xl bg-[var(--vo-accent)] px-5 py-3 text-sm font-semibold text-white hover:brightness-110 disabled:cursor-wait disabled:opacity-60"
          >
            {busy ? t("qr.generating") : t("qr.generate")}
          </button>
        </div>
      </section>

      {result?.preview_png_base64 ? (
        <section className="vo-enter mt-10 flex flex-col items-center gap-6 rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-6 sm:flex-row sm:items-start">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`data:image/png;base64,${result.preview_png_base64}`}
            alt={t("qr.previewAlt")}
            className="h-52 w-52 rounded-xl border border-[var(--vo-border)] bg-white p-3"
          />
          <div>
            <h2 className="vo-display text-2xl font-semibold">{t("qr.ready")}</h2>
            <p className="mt-2 text-sm text-[var(--vo-muted)]">{t("qr.downloadLead")}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              {(["png", "svg", "pdf"] as const).map((format) => {
                const artifact = result.artifacts.find(
                  (item) => item.filename.toLowerCase().endsWith(`.${format}`),
                );
                if (!artifact) return null;
                return (
                  <a
                    key={format}
                    href={`data:${artifact.mime};base64,${artifact.base64}`}
                    download={artifact.filename}
                    className="rounded-xl border border-[var(--vo-accent)] px-4 py-2 text-sm font-semibold text-[var(--vo-accent)] hover:bg-[var(--vo-accent-soft)]"
                  >
                    {t(`qr.download${format[0].toUpperCase()}${format.slice(1)}`)}
                  </a>
                );
              })}
            </div>
          </div>
        </section>
      ) : null}
    </OfficeShell>
  );
}
