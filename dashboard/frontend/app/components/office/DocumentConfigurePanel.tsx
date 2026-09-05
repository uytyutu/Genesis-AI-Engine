"use client";

import { useEffect, useMemo, useState } from "react";
import type { OfficeJobView, OfficeLanguage } from "../../lib/officeApi";
import { useOfficeT } from "../../lib/useOfficeT";

export type DocumentSettingsValues = Record<string, unknown>;

type CatalogField = {
  id: string;
  kind?: string;
  group?: string;
  options?: string[];
  required?: boolean;
  default?: unknown;
  when?: Record<string, string>;
  fact?: string;
};

type SettingsBlob = {
  catalog?: CatalogField[];
  values?: DocumentSettingsValues;
  ops?: Array<{
    id?: string;
    label_key?: string;
    from?: string;
    to?: string;
    value?: string;
    section?: string;
    text?: string;
    executable_now?: boolean;
    status?: string;
  }>;
  preview?: Array<{ before?: string; after?: string; note?: string }>;
  available_sections?: string[];
  special_wishes?: string | null;
  confirmed?: boolean;
  instruction_count?: number;
  executable_now_count?: number;
};

type Props = {
  job: OfficeJobView;
  languages: OfficeLanguage[];
  sourceLang: string;
  targetLang: string;
  outputFmt: string;
  busy?: boolean;
  onSourceLang: (v: string) => void;
  onTargetLang: (v: string) => void;
  onOutputFmt: (v: string) => void;
  onApply: (payload: {
    values: DocumentSettingsValues;
    special_wishes: string;
    confirm: boolean;
  }) => void;
};

function settingsFromJob(job: OfficeJobView): SettingsBlob {
  const proposal = job.proposal as { document_settings?: SettingsBlob } | null | undefined;
  if (proposal?.document_settings) return proposal.document_settings;
  const intent = (job.understanding as { intent?: { document_settings?: SettingsBlob } } | null)
    ?.intent;
  return intent?.document_settings || {};
}

export function DocumentConfigurePanel({
  job,
  languages,
  sourceLang,
  targetLang,
  outputFmt,
  busy,
  onSourceLang,
  onTargetLang,
  onOutputFmt,
  onApply,
}: Props) {
  const { t } = useOfficeT();
  const settings = useMemo(() => settingsFromJob(job), [job]);
  const catalog = settings.catalog || [];
  const sections = settings.available_sections || [];
  const [values, setValues] = useState<DocumentSettingsValues>(() => ({
    ...(settings.values || {}),
    source_language: sourceLang !== "auto" ? sourceLang : settings.values?.source_language,
    target_language: targetLang || settings.values?.target_language,
    output_format: outputFmt || settings.values?.output_format || "pdf",
  }));
  const [wishes, setWishes] = useState(String(settings.special_wishes || ""));
  const [extraOpen, setExtraOpen] = useState(
    () => Boolean(settings.special_wishes) || (settings.catalog || []).length <= 4,
  );

  useEffect(() => {
    setValues((prev) => ({
      ...prev,
      ...(settings.values || {}),
      source_language: sourceLang !== "auto" ? sourceLang : prev.source_language,
      target_language: targetLang || prev.target_language,
      output_format: outputFmt || prev.output_format,
    }));
    if (settings.special_wishes) setWishes(String(settings.special_wishes));
  }, [settings, sourceLang, targetLang, outputFmt]);

  function setField(id: string, value: unknown) {
    setValues((prev) => ({ ...prev, [id]: value }));
    if (id === "source_language" && typeof value === "string") onSourceLang(value);
    if (id === "target_language" && typeof value === "string") onTargetLang(value);
    if (id === "output_format" && typeof value === "string") onOutputFmt(value);
  }

  function visible(field: CatalogField): boolean {
    if (!field.when) return true;
    return Object.entries(field.when).every(([k, v]) => String(values[k] ?? "") === v);
  }

  const langOptions = languages.length
    ? languages
    : [
        { code: "de", native: "Deutsch", label_en: "German", label_de: "Deutsch" },
        { code: "en", native: "English", label_en: "English", label_de: "Englisch" },
        { code: "uk", native: "Українська", label_en: "Ukrainian", label_de: "Ukrainisch" },
        { code: "ru", native: "Русский", label_en: "Russian", label_de: "Russisch" },
      ];

  const ops = settings.ops || [];
  const preview = settings.preview || [];

  return (
    <div className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-5">
      <h3 className="vo-display text-xl font-semibold text-[var(--vo-ink)]">
        {t("configure.title")}
      </h3>
      <p className="mt-1 text-sm text-[var(--vo-muted)]">{t("configure.lead")}</p>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {catalog.filter(visible).map((field) => {
          const label = t(`configure.fields.${field.id}`, { defaultValue: field.id });
          if (field.kind === "language") {
            const isTarget = field.id === "target_language";
            const val = String(
              values[field.id] ?? (isTarget ? targetLang : sourceLang) ?? "",
            );
            return (
              <label key={field.id} className="block text-xs font-semibold text-[var(--vo-muted)]">
                {label}
                <select
                  className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2.5 text-sm text-[var(--vo-ink)]"
                  value={val === "auto" && isTarget ? "" : val}
                  onChange={(e) => setField(field.id, e.target.value)}
                >
                  {!isTarget ? (
                    <option value="auto">{t("service.sourceAutoDetect")}</option>
                  ) : (
                    <option value="">{t("service.chooseTarget")}</option>
                  )}
                  {langOptions.map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.native || l.label_en || l.code}
                    </option>
                  ))}
                </select>
              </label>
            );
          }
          if (field.kind === "format" || field.kind === "enum") {
            return (
              <label key={field.id} className="block text-xs font-semibold text-[var(--vo-muted)]">
                {label}
                <select
                  className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2.5 text-sm text-[var(--vo-ink)]"
                  value={String(values[field.id] ?? field.options?.[0] ?? "")}
                  onChange={(e) => setField(field.id, e.target.value)}
                >
                  {(field.options || []).map((opt) => (
                    <option key={opt} value={opt}>
                      {t(`configure.options.${field.id}.${opt}`, { defaultValue: opt.toUpperCase() })}
                    </option>
                  ))}
                </select>
              </label>
            );
          }
          if (field.kind === "bool") {
            return (
              <label
                key={field.id}
                className="flex items-center gap-2 text-sm text-[var(--vo-ink)] sm:col-span-2"
              >
                <input
                  type="checkbox"
                  checked={Boolean(
                    values[field.id] ?? (field.default !== undefined ? field.default : true),
                  )}
                  onChange={(e) => setField(field.id, e.target.checked)}
                />
                <span>{label}</span>
              </label>
            );
          }
          if (field.kind === "replace") {
            const current =
              (job.proposal?.explanation?.key_facts || []).find((f) => f.id === field.fact)
                ?.value || "—";
            return (
              <div key={field.id} className="sm:col-span-2 rounded-xl border border-[var(--vo-border)] p-3">
                <p className="text-xs font-semibold text-[var(--vo-muted)]">{label}</p>
                <p className="mt-1 text-xs text-[var(--vo-muted)]">
                  {t("configure.current")}: <span className="text-[var(--vo-ink)]">{current}</span>
                </p>
                <input
                  className="mt-2 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm"
                  placeholder={t("configure.newValue")}
                  value={String(values[field.id] ?? "")}
                  onChange={(e) => setField(field.id, e.target.value)}
                />
              </div>
            );
          }
          if (field.kind === "section_multi") {
            return (
              <label key={field.id} className="block text-xs font-semibold text-[var(--vo-muted)] sm:col-span-2">
                {label}
                <select
                  className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2.5 text-sm"
                  value={String(
                    Array.isArray(values[field.id])
                      ? (values[field.id] as string[])[0] || ""
                      : values[field.id] || "",
                  )}
                  onChange={(e) =>
                    setField(field.id, e.target.value ? [e.target.value] : [])
                  }
                >
                  <option value="">{t("configure.none")}</option>
                  {sections.map((sid) => (
                    <option key={sid} value={sid}>
                      {t(`analysis.sections.${sid}`, { defaultValue: sid })}
                    </option>
                  ))}
                </select>
              </label>
            );
          }
          if (field.kind === "text") {
            return (
              <label key={field.id} className="block text-xs font-semibold text-[var(--vo-muted)]">
                {label}
                <input
                  className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm"
                  value={String(values[field.id] ?? "")}
                  onChange={(e) => setField(field.id, e.target.value)}
                />
              </label>
            );
          }
          if (field.kind === "notice") {
            return (
              <p key={field.id} className="sm:col-span-2 text-xs text-amber-800">
                {t(`configure.fields.${field.id}`, { defaultValue: label })}
              </p>
            );
          }
          return null;
        })}
      </div>

      <button
        type="button"
        className="mt-4 text-sm font-semibold text-[var(--vo-accent)]"
        onClick={() => setExtraOpen((v) => !v)}
      >
        {extraOpen ? "− " : "+ "}
        {t("configure.addChange")}
      </button>

      {extraOpen || wishes ? (
        <label className="mt-3 block text-xs font-semibold text-[var(--vo-muted)]">
          {t("configure.specialWishes")}
          <textarea
            className="mt-1 min-h-[88px] w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm text-[var(--vo-ink)]"
            value={wishes}
            onChange={(e) => setWishes(e.target.value)}
            placeholder={t("configure.specialPlaceholder")}
          />
        </label>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            onApply({
              values: {
                ...values,
                source_language: sourceLang !== "auto" ? sourceLang : values.source_language,
                target_language: targetLang || values.target_language,
                output_format: outputFmt || values.output_format,
              },
              special_wishes: wishes,
              confirm: false,
            })
          }
          className="rounded-xl border border-[var(--vo-border)] px-4 py-2 text-sm font-semibold text-[var(--vo-ink)]"
        >
          {t("configure.previewOps")}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            onApply({
              values: {
                ...values,
                source_language: sourceLang !== "auto" ? sourceLang : values.source_language,
                target_language: targetLang || values.target_language,
                output_format: outputFmt || values.output_format,
              },
              special_wishes: wishes,
              confirm: true,
            })
          }
          className="rounded-xl bg-[var(--vo-accent)] px-4 py-2 text-sm font-semibold text-white"
        >
          {t("configure.confirmPay")}
        </button>
      </div>

      {ops.length ? (
        <div className="mt-5 rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] p-3">
          <p className="text-sm font-semibold text-[var(--vo-ink)]">{t("configure.understood")}</p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-[var(--vo-muted)]">
            {ops.slice(0, 12).map((op, i) => (
              <li key={`${op.id}-${i}`}>
                {t(`configure.ops.${op.label_key || op.id || "op"}`, {
                  defaultValue: op.label_key || op.id || "op",
                })}
                {op.from && op.to ? (
                  <span className="text-[var(--vo-ink)]">
                    {`: ${op.from} → ${op.to}`}
                  </span>
                ) : null}
                {op.value && !op.to ? (
                  <span className="text-[var(--vo-ink)]">{`: ${op.value}`}</span>
                ) : null}
                {op.section ? (
                  <span className="text-[var(--vo-ink)]">{`: ${op.section}`}</span>
                ) : null}
                {op.text ? (
                  <span className="block text-xs">{op.text}</span>
                ) : null}
                {!op.executable_now ? (
                  <span className="ml-1 text-[10px] uppercase text-amber-700">
                    {t("configure.instruction")}
                  </span>
                ) : null}
              </li>
            ))}
          </ol>
        </div>
      ) : null}

      {preview.length ? (
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {preview.slice(0, 4).map((row, i) => (
            <div
              key={i}
              className="rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] p-3 text-xs"
            >
              <p className="font-semibold text-[var(--vo-muted)]">{t("configure.before")}</p>
              <p className="mt-1 text-[var(--vo-ink)]">{row.before || "—"}</p>
              <p className="mt-2 font-semibold text-[var(--vo-muted)]">{t("configure.after")}</p>
              <p className="mt-1 text-[var(--vo-ink)]">{row.after || "—"}</p>
            </div>
          ))}
        </div>
      ) : null}

      <p className="mt-3 text-[11px] text-[var(--vo-muted)]">{t("configure.fullAfterPay")}</p>
    </div>
  );
}
