"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  checkoutOfficeJob,
  configureOfficeDocument,
  createOfficeJob,
  selectOfficeAction,
  uploadOfficeFile,
  uploadOfficePages,
  type OfficeJobView,
} from "../../lib/officeApi";
import { saveOfficeJobToken } from "../../lib/officeSession";
import { useOfficeT } from "../../lib/useOfficeT";
import { DocumentConfigurePanel } from "./DocumentConfigurePanel";
import { OfficeShell } from "./OfficeShell";

type ServiceKind = "translate" | "documents" | "excel" | "smart";

const PRESET: Record<ServiceKind, string | null> = {
  translate: "translate",
  documents: null,
  excel: null,
  smart: null,
};

const DEFAULT_ACTION: Record<ServiceKind, string | null> = {
  translate: "translate",
  documents: "convert_docx",
  excel: "extract_data",
  smart: null,
};

const LEGAL_HINT =
  /legal|recht|vertrag|bescheid|klage|anwalt|official|amtlich|jurid|юрид|правов|зверненн/i;

export function OfficeServiceFlow({ kind }: { kind: ServiceKind }) {
  const { t } = useOfficeT();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState<"idle" | "analyzing" | "proposal">("idle");
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [job, setJob] = useState<OfficeJobView | null>(null);
  const [targetLang, setTargetLang] = useState("");
  const [sourceLang, setSourceLang] = useState("auto");
  const [outputFmt, setOutputFmt] = useState(kind === "excel" ? "xlsx" : "pdf");
  const [analysisStep, setAnalysisStep] = useState(0);
  const [legalConfirm, setLegalConfirm] = useState(false);
  const [customerEmail, setCustomerEmail] = useState("");
  const configureRef = useRef<HTMLDivElement | null>(null);

  const proposal = job?.proposal;
  const languages = job?.languages || [];

  useEffect(() => {
    const detected = proposal?.detected?.language || proposal?.explanation?.language_code;
    if (detected && detected !== "unknown") {
      setSourceLang(String(detected));
    }
  }, [proposal?.detected?.language, proposal?.explanation?.language_code]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const paidJob = params.get("job");
    if (params.get("paid") === "1" && paidJob) {
      router.replace(`/office/order/${encodeURIComponent(paidJob)}`);
    }
  }, [router]);

  const bullets = useMemo(
    () => [1, 2, 3, 4].map((n) => t(`service.${kind}.b${n}`)),
    [kind, t],
  );

  function abandonJob() {
    setBusy(false);
    setPhase("idle");
    setError(null);
    setToken(null);
    setJob(null);
    setAnalysisStep(0);
    setLegalConfirm(false);
    router.push("/office");
  }

  function goBackStep() {
    if (phase === "proposal" || phase === "analyzing") {
      setPhase("idle");
      setJob(null);
      setToken(null);
      setError(null);
      setLegalConfirm(false);
      return;
    }
    router.push("/office");
  }

  async function onFiles(list: FileList | null) {
    const files = list ? Array.from(list) : [];
    if (!files.length) return;
    setError(null);
    setBusy(true);
    setPhase("analyzing");
    setAnalysisStep(0);
    setLegalConfirm(false);
    const timers = [0, 1, 2].map((i) =>
      window.setTimeout(() => setAnalysisStep(i + 1), 400 + i * 450),
    );
    try {
      const created = await createOfficeJob({
        service_preset: PRESET[kind] || undefined,
      });
      if (!created.owner_token || !created.job_id) {
        throw new Error(t("errors.generic"));
      }
      setToken(created.owner_token);
      saveOfficeJobToken(created.job_id, created.owner_token, {
        filename: files[0]?.name,
        status: "created",
      });
      const allImages = files.every(
        (f) => /\.(png|jpe?g)$/i.test(f.name) || f.type.startsWith("image/"),
      );
      const viewed =
        files.length > 1 && allImages
          ? await uploadOfficePages(created.job_id, created.owner_token, files)
          : await uploadOfficeFile(created.job_id, created.owner_token, files[0]);
      setJob(viewed);
      setAnalysisStep(3);
      if (viewed.status === "failed") {
        setError(viewed.failure_detail || viewed.failure_reason || t("errors.uploadFailed"));
        setPhase("idle");
      } else {
        const action = DEFAULT_ACTION[kind];
        if (action && action !== "translate") {
          const configured = await selectOfficeAction(created.job_id, created.owner_token, {
            action_id: action,
            output_format:
              action === "convert_docx"
                ? "docx"
                : action === "extract_data"
                  ? "xlsx"
                  : outputFmt,
            confirm_settings: false,
          });
          setJob(configured);
          window.setTimeout(() => {
            configureRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 120);
        }
        setPhase("proposal");
      }
    } catch (e) {
      setPhase("idle");
      setError(e instanceof Error ? e.message : t("errors.generic"));
    } finally {
      timers.forEach((id) => window.clearTimeout(id));
      setBusy(false);
    }
  }

  async function onChoose(actionId: string) {
    if (!job?.job_id || !token) return;
    setBusy(true);
    setError(null);
    setLegalConfirm(false);
    try {
      const needsLang = (proposal?.choice_options || []).find((c) => c.id === actionId)
        ?.needs_target_language;
      const viewed = await selectOfficeAction(job.job_id, token, {
        action_id: actionId,
        target_language: needsLang ? targetLang || undefined : undefined,
        source_language: needsLang && sourceLang !== "auto" ? sourceLang : undefined,
        output_format: needsLang
          ? outputFmt
          : actionId === "convert_docx"
            ? "docx"
            : actionId === "extract_data"
              ? "xlsx"
              : outputFmt,
        confirm_settings: false,
      });
      setJob(viewed);
      window.setTimeout(() => {
        configureRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 80);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"));
    } finally {
      setBusy(false);
    }
  }

  async function onConfigureTranslate() {
    if (!job?.job_id || !token) return;
    if (!targetLang) {
      setError(t("service.chooseTarget"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const viewed = await selectOfficeAction(job.job_id, token, {
        action_id: "translate",
        target_language: targetLang,
        source_language: sourceLang !== "auto" ? sourceLang : undefined,
        output_format: outputFmt === "xlsx" ? "pdf" : outputFmt,
        confirm_settings: false,
      });
      setJob(viewed);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"));
    } finally {
      setBusy(false);
    }
  }

  async function onDocumentSettings(payload: {
    values: Record<string, unknown>;
    special_wishes: string;
    confirm: boolean;
  }) {
    if (!job?.job_id || !token) return;
    const actionId =
      proposal?.task ||
      (job.understanding as { intent?: { id?: string } } | null | undefined)?.intent?.id ||
      DEFAULT_ACTION[kind] ||
      "translate";
    if (payload.confirm && actionId === "translate" && !targetLang && !payload.values.target_language) {
      setError(t("service.chooseTarget"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const tgt = String(payload.values.target_language || targetLang || "");
      const src = String(payload.values.source_language || sourceLang || "auto");
      const fmt = String(payload.values.output_format || outputFmt || "pdf");
      if (tgt) setTargetLang(tgt);
      if (src) setSourceLang(src);
      if (fmt) setOutputFmt(fmt);
      const viewed = await configureOfficeDocument(job.job_id, token, {
        values: payload.values,
        special_wishes: payload.special_wishes,
        confirm: payload.confirm,
        action_id: String(actionId),
        target_language: tgt || undefined,
        source_language: src !== "auto" ? src : undefined,
        output_format: fmt,
      });
      setJob(viewed);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"));
    } finally {
      setBusy(false);
    }
  }

  async function onPay() {
    if (!job?.job_id || !token) return;
    const email = customerEmail.trim();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError(t("proposal.emailRequired"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      const orderPath = `/office/order/${encodeURIComponent(job.job_id)}`;
      const viewed = await checkoutOfficeJob(job.job_id, token, {
        success_url: `${origin}${orderPath}?paid=1`,
        cancel_url: `${origin}${orderPath}?cancel=1`,
        email,
      });
      setJob(viewed);
      saveOfficeJobToken(job.job_id, token, {
        filename: viewed.filename,
        status: viewed.status,
      });
      const url = viewed.checkout?.checkout_url || viewed.payment?.checkout_url;
      if (url) {
        window.location.assign(url);
        return;
      }
      if (viewed.checkout?.already_paid || viewed.payment?.paid) {
        router.push(orderPath);
        return;
      }
      setError(t("errors.checkoutUnavailable"));
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"));
    } finally {
      setBusy(false);
    }
  }

  const detected = proposal?.detected;
  const explanation = proposal?.explanation;
  const nextStep = proposal?.next_step || "";
  const showConfigure =
    nextStep === "configure_document" ||
    nextStep === "configure_translate" ||
    (Boolean(proposal?.document_settings) && !proposal?.document_settings?.confirmed && Boolean(proposal?.task));
  // After a task is chosen, hide priced choice cards so configure is the clear next step.
  const showChoices = Boolean(proposal?.show_choice_cards) && !showConfigure;
  const canPay =
    nextStep === "awaiting_stage3" ||
    nextStep === "awaiting_payment" ||
    Boolean(proposal?.payment_enabled && proposal?.document_settings?.confirmed);
  const showTranslateLang =
    kind === "translate" ||
    proposal?.task === "translate" ||
    nextStep === "configure_translate";
  const pathStep = showChoices ? 1 : showConfigure ? 2 : canPay ? 3 : proposal?.task ? 2 : 0;
  const steps = [
    t("analysis.stepFile"),
    t("analysis.stepLang"),
    t("analysis.stepDoc"),
    t("analysis.stepTask"),
  ];

  const docTypeBlob = [
    detected?.document_type,
    detected?.document_type_label_de,
    explanation?.kind,
    proposal?.task,
    proposal?.task_label_de,
  ]
    .filter(Boolean)
    .join(" ");
  const needsLegalGate =
    kind === "documents" || Boolean(docTypeBlob && LEGAL_HINT.test(docTypeBlob));
  const payBlockedByLegal = needsLegalGate && !legalConfirm;

  function findingLabel(f: { id: string; value?: string; count?: number; code?: string }) {
    const base = t(`analysis.findings.${f.id}`, { defaultValue: f.id });
    if (f.value) return `${base}: ${f.value}`;
    if (f.count != null) return t(`analysis.findings.${f.id}_n`, {
      defaultValue: `${base}: ${f.count}`,
      count: f.count,
    });
    if (f.code) return `${base}: ${f.code}`;
    return base;
  }

  return (
    <OfficeShell active={kind === "smart" ? "smart" : kind}>
      <div className="mb-6 flex flex-wrap items-center gap-3 text-sm">
        <button
          type="button"
          onClick={goBackStep}
          className="rounded-lg border border-[var(--vo-border)] px-3 py-1.5 text-[var(--vo-ink)] hover:bg-black/[0.03]"
        >
          ← {t("back")}
        </button>
        <button
          type="button"
          onClick={abandonJob}
          className="rounded-lg px-3 py-1.5 text-[var(--vo-muted)] underline-offset-2 hover:text-[var(--vo-ink)] hover:underline"
        >
          {t("cancel")}
        </button>
        <Link
          href="/office"
          className="ml-auto text-xs text-[var(--vo-muted)] underline-offset-2 hover:underline"
        >
          {t("backHome")}
        </Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="vo-enter">
          <h1 className="vo-display text-3xl font-semibold tracking-tight sm:text-4xl">
            {t(`service.${kind}.title`)}
          </h1>
          <p className="mt-3 text-[var(--vo-muted)]">{t(`service.${kind}.lead`)}</p>
          <ul className="mt-6 space-y-2 text-sm text-[var(--vo-ink)]">
            {bullets.map((b) => (
              <li key={b} className="flex gap-2">
                <span className="text-[var(--vo-ok)]">✓</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>

          {showTranslateLang && (phase === "idle" || phase === "proposal") && (
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <label className="block text-xs font-semibold text-[var(--vo-muted)]">
                {t("service.sourceLanguage")}
                <select
                  className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] px-3 py-2.5 text-sm text-[var(--vo-ink)]"
                  value={sourceLang}
                  onChange={(e) => setSourceLang(e.target.value)}
                >
                  <option value="auto">{t("service.sourceAutoDetect")}</option>
                  {(languages.length
                    ? languages
                    : [
                        { code: "de", native: "Deutsch", label_en: "German", label_de: "Deutsch" },
                        { code: "en", native: "English", label_en: "English", label_de: "Englisch" },
                        { code: "uk", native: "Українська", label_en: "Ukrainian", label_de: "Ukrainisch" },
                        { code: "ru", native: "Русский", label_en: "Russian", label_de: "Russisch" },
                      ]
                  ).map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.native || ("label_en" in l ? l.label_en : undefined) || l.code}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-xs font-semibold text-[var(--vo-muted)]">
                {t("service.targetLanguage")}
                <select
                  className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] px-3 py-2.5 text-sm text-[var(--vo-ink)]"
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                >
                  <option value="">{t("service.chooseTarget")}</option>
                  {(languages.length
                    ? languages.map((l) => ({
                        code: l.code,
                        native: l.native || l.label_en || l.code,
                      }))
                    : [
                        { code: "de", native: "Deutsch" },
                        { code: "en", native: "English" },
                        { code: "uk", native: "Українська" },
                        { code: "ru", native: "Русский" },
                      ]
                  ).map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.native}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-xs font-semibold text-[var(--vo-muted)] sm:col-span-2">
                {t("service.outputFormat")}
                <select
                  className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] px-3 py-2.5 text-sm text-[var(--vo-ink)]"
                  value={outputFmt}
                  onChange={(e) => setOutputFmt(e.target.value)}
                >
                  <option value="pdf">PDF</option>
                  <option value="docx">DOCX</option>
                  {kind === "excel" ? <option value="xlsx">XLSX</option> : null}
                </select>
              </label>
              <p className="sm:col-span-2 text-xs text-[var(--vo-muted)]">
                {t("langSeparationHint")}
              </p>
            </div>
          )}

          <label className="mt-8 inline-flex min-h-[48px] cursor-pointer items-center justify-center rounded-xl bg-[var(--vo-accent)] px-6 text-sm font-semibold text-white hover:brightness-110">
            {busy && phase === "analyzing" ? t("analyzing") : t("uploadCta")}
            <input
              type="file"
              className="hidden"
              multiple
              accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx,.csv,.txt,application/pdf,image/*"
              disabled={busy}
              onChange={(e) => onFiles(e.target.files)}
            />
          </label>
          <p className="mt-2 text-xs text-[var(--vo-muted)]">{t("uploadHint")}</p>
        </section>

        <aside className="vo-enter rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-5 shadow-[0_8px_24px_rgba(24,32,51,0.04)]">
          <h2 className="text-sm font-semibold text-[var(--vo-ink)]">{t("youReceive")}</h2>
          <ul className="mt-3 space-y-2 text-sm text-[var(--vo-muted)]">
            {bullets.map((b) => (
              <li key={`side-${b}`}>• {b}</li>
            ))}
          </ul>
          {(kind === "excel" || kind === "documents" || kind === "translate") && (
            <p className="mt-4 text-xs text-[var(--vo-muted)]">{t("ocrHonesty")}</p>
          )}
          {kind === "excel" ? (
            <p className="mt-2 text-xs text-[var(--vo-muted)]">{t("excelHonesty")}</p>
          ) : null}
          <p className="mt-6 text-xs text-[var(--vo-muted)]">{t("customerPayHint")}</p>
          <p className="mt-2 text-xs text-[var(--vo-muted)]">{t("customerNotice")}</p>
        </aside>
      </div>

      {error ? (
        <p className="mt-6 rounded-xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {error}
        </p>
      ) : null}

      {phase === "analyzing" ? (
        <section className="vo-enter mt-10 rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-6">
          <h2 className="vo-display text-2xl font-semibold">{t("analysis.title")}</h2>
          <ol className="mt-6 space-y-3">
            {steps.map((label, i) => {
              const done = analysisStep > i;
              const live = analysisStep === i;
              return (
                <li key={label} className="flex items-center gap-3 text-sm">
                  <span
                    className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                      done
                        ? "bg-[var(--vo-ok)] text-white"
                        : live
                          ? "bg-[var(--vo-accent-soft)] text-[var(--vo-accent)] vo-dot-live"
                          : "bg-black/[0.04] text-[var(--vo-muted)]"
                    }`}
                  >
                    {done ? "✓" : "●"}
                  </span>
                  <span className={done || live ? "text-[var(--vo-ink)]" : "text-[var(--vo-muted)]"}>
                    {label}
                  </span>
                </li>
              );
            })}
          </ol>
        </section>
      ) : null}

      {phase === "proposal" && proposal ? (
        <section className="vo-enter mt-10 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)]/90 px-4 py-3 lg:col-span-2">
            <ol className="flex flex-wrap items-center gap-2 text-xs font-semibold sm:gap-3">
              {[1, 2, 3].map((n) => (
                <li
                  key={n}
                  className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 ${
                    pathStep === n
                      ? "bg-[var(--vo-accent)] text-white"
                      : pathStep > n
                        ? "bg-[var(--vo-accent-soft)] text-[var(--vo-accent)]"
                        : "bg-[var(--vo-bg)] text-[var(--vo-muted)]"
                  }`}
                >
                  <span aria-hidden>{n}</span>
                  {t(`path.step${n}`)}
                </li>
              ))}
            </ol>
            <p className="mt-2 text-[11px] text-[var(--vo-muted)]">{t("path.hint")}</p>
          </div>
          <div className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--vo-muted)]">
              {t("analysis.reviewedTitle")}
            </h2>
            <p className="mt-2 text-lg font-semibold text-[var(--vo-ink)]">
              {job?.filename || "—"}
            </p>
            <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs text-[var(--vo-muted)]">{t("analysis.metaType")}</dt>
                <dd className="font-medium text-[var(--vo-ink)]">
                  {t(`docTypes.${explanation?.kind || detected?.document_type || "general"}`, {
                    defaultValue:
                      detected?.document_type_label_de ||
                      detected?.document_type ||
                      t("analysis.unknownType"),
                  })}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-[var(--vo-muted)]">{t("analysis.metaLanguage")}</dt>
                <dd className="font-medium text-[var(--vo-ink)]">
                  {t(`langNames.${explanation?.language_code || detected?.language || "unknown"}`, {
                    defaultValue:
                      detected?.language_label_de ||
                      detected?.language ||
                      "—",
                  })}
                  {explanation?.language_confidence != null
                    ? ` · ${Math.round(Number(explanation.language_confidence) * 100)}%`
                    : ""}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-[var(--vo-muted)]">{t("analysis.metaPages")}</dt>
                <dd className="font-medium text-[var(--vo-ink)]">
                  {detected?.pages != null
                    ? t("analysis.pages", { count: detected.pages })
                    : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-[var(--vo-muted)]">{t("analysis.metaContent")}</dt>
                <dd className="font-medium text-[var(--vo-ink)]">
                  {t(`analysis.contentKind.${explanation?.content_kind || "text"}`, {
                    defaultValue: explanation?.content_kind || "text",
                  })}
                </dd>
              </div>
            </dl>

            <p className="mt-4 text-base font-semibold text-[var(--vo-ink)]">
              {t(`analysis.headline.${explanation?.about_id || "general"}`, {
                defaultValue: t("analysis.headline.general"),
                type: t(`docTypes.${explanation?.kind || "general"}`, {
                  defaultValue: detected?.document_type_label_de || t("analysis.unknownType"),
                }),
                language: t(
                  `langNames.${explanation?.language_code || detected?.language || "unknown"}`,
                  {
                    defaultValue: detected?.language_label_de || "—",
                  },
                ),
                pages: detected?.pages ?? explanation?.pages ?? "?",
              })}
            </p>

            {(explanation?.sections || []).length ? (
              <div className="mt-4">
                <p className="text-sm font-semibold text-[var(--vo-ink)]">
                  {t("analysis.sectionsTitle")}
                </p>
                <ul className="mt-2 flex flex-wrap gap-1.5">
                  {(explanation?.sections || []).map((s) => (
                    <li
                      key={s.id}
                      className="rounded-full border border-[var(--vo-border)] bg-[var(--vo-bg)] px-2.5 py-1 text-xs text-[var(--vo-ink)]"
                    >
                      {t(`analysis.sections.${s.id}`, { defaultValue: s.id })}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {(explanation?.key_facts || []).length ? (
              <div className="mt-4">
                <p className="text-sm font-semibold text-[var(--vo-ink)]">
                  {t("analysis.keyFactsTitle")}
                </p>
                <ul className="mt-2 space-y-1.5 text-sm text-[var(--vo-muted)]">
                  {(explanation?.key_facts || []).map((f, i) => (
                    <li key={`${f.id}-${i}`} className="flex justify-between gap-3 border-b border-[var(--vo-border)]/50 pb-1">
                      <span>{t(`analysis.facts.${f.id}`, { defaultValue: f.id })}</span>
                      <span className="text-right font-medium text-[var(--vo-ink)]">
                        {f.value || t("analysis.factPresent")}
                        {f.confidence === "low" || f.confidence === "medium"
                          ? ` · ${t("analysis.pleaseVerify")}`
                          : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {(explanation?.findings || []).length ? (
              <div className="mt-4">
                <p className="text-sm font-semibold text-[var(--vo-ink)]">
                  {t("analysis.foundTitle")}
                </p>
                <ul className="mt-2 space-y-1.5 text-sm text-[var(--vo-muted)]">
                  {(explanation?.findings || []).map((f, i) => (
                    <li key={`${f.id}-${i}`} className="flex gap-2">
                      <span className="text-[var(--vo-ok)]" aria-hidden>
                        •
                      </span>
                      <span>{findingLabel(f)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="mt-4 text-sm text-[var(--vo-muted)]">
                {t("analysis.foundEmpty")}
              </p>
            )}

            <p className="mt-4 text-sm text-[var(--vo-ink)]">
              <span className="font-semibold">{t("analysis.aboutTitle")}: </span>
              {t(`analysis.about.${explanation?.about_id || "general"}`, {
                defaultValue: t("analysis.about.general"),
              })}
            </p>

            {(explanation?.uncertain || []).length ? (
              <div className="mt-4 rounded-xl border border-amber-300/50 bg-amber-50/80 px-3 py-3 text-xs text-amber-950">
                <p className="font-semibold">{t("analysis.uncertainTitle")}</p>
                <ul className="mt-1 space-y-1">
                  {(explanation?.uncertain || []).map((u) => (
                    <li key={u.id}>
                      {t(`analysis.uncertain.${u.id}`, {
                        defaultValue: t("analysis.uncertain.generic"),
                      })}
                    </li>
                  ))}
                </ul>
                <p className="mt-2">{t("analysis.confirmPlease")}</p>
              </div>
            ) : null}

            <p className="mt-3 text-[11px] text-[var(--vo-muted)]">{t("analysis.noInvent")}</p>

            {showChoices ? (
              <div className="mt-6">
                <p className="text-sm font-semibold">{t("analysis.whatNext")}</p>
                <p className="mt-1 text-xs text-[var(--vo-muted)]">
                  {t("analysis.afterChooseHint")}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(proposal.choice_options || []).map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      disabled={busy}
                      onClick={() => onChoose(opt.id)}
                      className="rounded-xl border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm font-medium text-[var(--vo-ink)] hover:border-[var(--vo-accent)]"
                    >
                      {t(`actions.${opt.id}`, {
                        defaultValue: opt.label_de || opt.id,
                      })}
                      {opt.price_eur != null ? (
                        <span className="ml-1 text-xs text-[var(--vo-muted)]">
                          · {opt.price_eur.toFixed(2)} €
                        </span>
                      ) : null}
                    </button>
                  ))}
                </div>
                {explanation?.kind === "invoice" ? (
                  <p className="mt-3 text-xs text-[var(--vo-muted)]">
                    {t("analysis.invoiceCalcHint")}
                  </p>
                ) : null}
              </div>
            ) : null}

            {(kind === "translate" || nextStep === "configure_translate") && !showConfigure ? (
              <button
                type="button"
                disabled={busy}
                onClick={onConfigureTranslate}
                className="mt-6 rounded-xl border border-[var(--vo-accent)] px-4 py-2 text-sm font-semibold text-[var(--vo-accent)]"
              >
                {t("configure.open")}
              </button>
            ) : null}

            {showConfigure && job ? (
              <div ref={configureRef} className="mt-6 scroll-mt-6">
                <DocumentConfigurePanel
                  job={job}
                  languages={languages}
                  sourceLang={sourceLang}
                  targetLang={targetLang}
                  outputFmt={outputFmt}
                  busy={busy}
                  onSourceLang={setSourceLang}
                  onTargetLang={setTargetLang}
                  onOutputFmt={setOutputFmt}
                  onApply={onDocumentSettings}
                />
              </div>
            ) : null}
          </div>

          <div className="rounded-2xl border border-[var(--vo-accent)]/25 bg-[var(--vo-accent-soft)]/40 p-6">
            <h2 className="vo-display text-2xl font-semibold">{t("proposal.title")}</h2>
            <dl className="mt-5 space-y-3 text-sm">
              <Row label={t("proposal.document")} value={job?.filename || "—"} />
              <Row
                label={t("proposal.task")}
                value={
                  (proposal.task
                    ? t(`actions.${proposal.task}`)
                    : proposal.task_label_de) || "—"
                }
              />
              {proposal.target_language ? (
                <>
                  <Row
                    label={t("proposal.from")}
                    value={String(detected?.language_label_de || detected?.language || "auto")}
                  />
                  <Row label={t("proposal.to")} value={String(proposal.target_language)} />
                </>
              ) : null}
              <Row label={t("proposal.output")} value={String(proposal.result_format || "—")} />
              <Row
                label={t("proposal.scope")}
                value={
                  detected?.pages != null
                    ? t("analysis.pages", { count: detected.pages })
                    : "—"
                }
              />
              <Row
                label={t("proposal.price")}
                value={
                  proposal.price_eur != null ? `${proposal.price_eur.toFixed(2)} €` : "—"
                }
              />
            </dl>
            {(proposal.includes || []).length ? (
              <div className="mt-4">
                <p className="text-xs font-semibold text-[var(--vo-muted)]">
                  {t("proposal.includes")}
                </p>
                <ul className="mt-1 space-y-1 text-xs text-[var(--vo-muted)]">
                  {proposal.includes!.map((line) => (
                    <li key={line}>• {line}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {proposal.preview ? (
              <div className="mt-4 rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-3 text-xs">
                <p className="font-semibold text-[var(--vo-ink)]">{t("preview.title")}</p>
                {proposal.preview.excerpt ? (
                  <p className="mt-2 whitespace-pre-wrap text-[var(--vo-muted)]">
                    {proposal.preview.excerpt}
                  </p>
                ) : null}
                <p className="mt-2 font-semibold text-[var(--vo-accent)]">
                  {t("preview.fullAfterPay")}
                </p>
              </div>
            ) : null}

            {needsLegalGate ? (
              <div className="mt-5 rounded-xl border border-amber-300/60 bg-amber-50/80 p-4 text-xs text-amber-950">
                <p className="font-semibold">{t("legalGate.title")}</p>
                <p className="mt-1">{t("legalGate.lead")}</p>
                <ul className="mt-2 list-disc space-y-1 pl-4">
                  <li>{t("legalGate.c1")}</li>
                  <li>{t("legalGate.c2")}</li>
                  <li>{t("legalGate.c3")}</li>
                  <li>{t("legalGate.c4")}</li>
                </ul>
                <p className="mt-2 text-amber-900/80">{t("legalGate.specialist")}</p>
                <label className="mt-3 flex items-start gap-2">
                  <input
                    type="checkbox"
                    className="mt-0.5"
                    checked={legalConfirm}
                    onChange={(e) => setLegalConfirm(e.target.checked)}
                  />
                  <span>{t("legalGate.confirm")}</span>
                </label>
              </div>
            ) : null}

            <label className="mt-5 block text-xs font-semibold text-[var(--vo-muted)]">
              {t("proposal.emailLabel")}
              <input
                type="email"
                autoComplete="email"
                className="mt-1 w-full rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] px-3 py-2.5 text-sm text-[var(--vo-ink)]"
                value={customerEmail}
                onChange={(e) => setCustomerEmail(e.target.value)}
                placeholder={t("proposal.emailPlaceholder")}
              />
              <span className="mt-1 block text-[11px] font-normal">{t("proposal.emailHint")}</span>
            </label>

            <button
              type="button"
              disabled={busy || Boolean(job?.payment?.paid) || payBlockedByLegal || !canPay}
              onClick={onPay}
              className="mt-6 w-full rounded-xl bg-[var(--vo-accent)] px-4 py-3 text-sm font-semibold text-white hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
              title={t("proposal.payHint")}
            >
              {job?.payment?.paid
                ? t("proposal.paid")
                : !canPay
                  ? t("configure.confirmFirst")
                  : t("proposal.payCta")}
            </button>
            <p className="mt-2 text-xs text-[var(--vo-muted)]">{t("customerPayHint")}</p>
          </div>
        </section>
      ) : null}
    </OfficeShell>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-[var(--vo-border)]/70 pb-2">
      <dt className="text-[var(--vo-muted)]">{label}</dt>
      <dd className="text-right font-medium text-[var(--vo-ink)]">{value}</dd>
    </div>
  );
}
