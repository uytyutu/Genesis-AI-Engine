"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../PublicPageShell";
import { PublicFunnelFooter } from "../navigation/PublicFunnelFooter";
import { BRAND_NAME } from "../../lib/publicBrand";
import { logCommerceEvent } from "../../lib/commerceFunnel";
import {
  continueOfficeJob,
  createOfficeJob,
  downloadOfficeArtifact,
  selectOfficeAction,
  uploadOfficeFile,
  uploadOfficePages,
  type OfficeJobView,
} from "../../lib/officeApi";

const NS = "agencyHub.office";

type Props = {
  servicePreset?: string | null;
};

export function VirtusOfficeStorefront({ servicePreset = null }: Props) {
  const { t } = useTranslation("site");
  const isTranslate = servicePreset === "translate";

  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState<"idle" | "analyzing" | "proposal" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [job, setJob] = useState<OfficeJobView | null>(null);
  const [targetLang, setTargetLang] = useState("uk");
  const [outputFmt, setOutputFmt] = useState("pdf");

  const proposal = job?.proposal;
  const languages = job?.languages || [];
  const nextStep = proposal?.next_step || "";

  const title = useMemo(
    () =>
      isTranslate
        ? t(`${NS}.translateTitle`, { defaultValue: "Dokument übersetzen" })
        : t(`${NS}.title`, {
            defaultValue: "Fertige Dokumente, Übersetzungen und Berechnungen",
          }),
    [isTranslate, t],
  );

  async function onFiles(list: FileList | null) {
    const files = list ? Array.from(list) : [];
    if (!files.length) return;
    setError(null);
    setBusy(true);
    setPhase("analyzing");
    try {
      const created = await createOfficeJob({
        service_preset: servicePreset || undefined,
      });
      if (!created.owner_token || !created.job_id) {
        throw new Error("Job konnte nicht erstellt werden");
      }
      setToken(created.owner_token);
      logCommerceEvent("tier_select", servicePreset || "office_upload", "office");
      const allImages = files.every((f) => /\.(png|jpe?g)$/i.test(f.name) || f.type.startsWith("image/"));
      const viewed =
        files.length > 1 && allImages
          ? await uploadOfficePages(created.job_id, created.owner_token, files)
          : await uploadOfficeFile(created.job_id, created.owner_token, files[0]);
      setJob(viewed);
      setPhase(viewed.status === "failed" ? "idle" : "proposal");
      if (viewed.status === "failed") {
        setError(viewed.failure_detail || viewed.failure_reason || "Upload fehlgeschlagen");
      }
    } catch (e) {
      setPhase("idle");
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setBusy(false);
    }
  }

  async function onChoose(actionId: string) {
    if (!job?.job_id || !token) return;
    setBusy(true);
    setError(null);
    try {
      const needsLang = (proposal?.choice_options || []).find((c) => c.id === actionId)
        ?.needs_target_language;
      const viewed = await selectOfficeAction(job.job_id, token, {
        action_id: actionId,
        target_language: needsLang ? targetLang : undefined,
        output_format: needsLang ? outputFmt : undefined,
      });
      setJob(viewed);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setBusy(false);
    }
  }

  async function onConfigureTranslate() {
    if (!job?.job_id || !token) return;
    setBusy(true);
    setError(null);
    try {
      const viewed = await selectOfficeAction(job.job_id, token, {
        action_id: "translate",
        target_language: targetLang,
        output_format: outputFmt,
      });
      setJob(viewed);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setBusy(false);
    }
  }

  async function onContinue() {
    if (!job?.job_id || !token) return;
    setBusy(true);
    setError(null);
    try {
      const viewed = await continueOfficeJob(job.job_id, token);
      setJob(viewed);
      if (viewed.status === "completed") {
        setPhase("done");
      } else if (viewed.status === "failed") {
        setError(viewed.failure_detail || viewed.failure_reason || "Ausführung fehlgeschlagen");
        setPhase("proposal");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setBusy(false);
    }
  }

  async function onDownload() {
    if (!job?.job_id || !token) return;
    setBusy(true);
    setError(null);
    try {
      await downloadOfficeArtifact(job.job_id, token);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-3xl px-4 py-12 text-zinc-100">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-300/90">
          {t(`${NS}.badge`, { defaultValue: "Virtus Office" })}
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          {title}
        </h1>
        <p className="mt-3 text-sm text-zinc-400">
          {isTranslate
            ? t(`${NS}.translateSub`, {
                defaultValue:
                  "Datei laden → Sprache erkennen → Zielsprache wählen → Vorschlag. Kein Chat. Noch keine Zahlung.",
              })
            : t(`${NS}.smartUploadSub`, {
                defaultValue:
                  "Datei laden — Virtus erkennt Typ und Sprache und schlägt Aktionen vor. Kein AI-Chat.",
              })}
        </p>

        <div className="mt-4 rounded-xl border border-amber-400/30 bg-amber-500/[0.08] px-4 py-3 text-xs text-amber-100/95">
          {t(`${NS}.stage4Honest`, {
            defaultValue:
              "Stage 4: Foto/Scan → OCR → Vorschlag → Vorschau → Zahlung → Ergebnis. Kein kostenloser Final-Download. OFFICE_PIPELINE_LIVE = false.",
          })}
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <label className="inline-flex min-h-[44px] cursor-pointer items-center justify-center rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-500">
            {busy && phase === "analyzing"
              ? t(`${NS}.analyzing`, { defaultValue: "Dokument wird analysiert…" })
              : t(`${NS}.uploadCta`, { defaultValue: "Datei laden und Aufgabe bestimmen" })}
            <input
              type="file"
              className="hidden"
              multiple
              accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx,.csv,.txt,application/pdf,image/*"
              disabled={busy}
              onChange={(e) => onFiles(e.target.files)}
            />
          </label>
          <Link
            href="/office/bewerbung"
            className="inline-flex min-h-[44px] items-center justify-center rounded-xl border border-white/15 px-5 py-2.5 text-sm font-semibold text-zinc-200 hover:bg-white/[0.04]"
          >
            {t(`${NS}.goBewerbung`, { defaultValue: "Bewerbung Office →" })}
          </Link>
          {!isTranslate ? (
            <Link
              href="/office/translate"
              className="inline-flex min-h-[44px] items-center justify-center rounded-xl border border-white/15 px-5 py-2.5 text-sm font-semibold text-zinc-200 hover:bg-white/[0.04]"
            >
              {t(`${NS}.goTranslate`, { defaultValue: "Direkt: Übersetzen →" })}
            </Link>
          ) : (
            <Link
              href="/office"
              className="inline-flex min-h-[44px] items-center justify-center rounded-xl border border-white/15 px-5 py-2.5 text-sm font-semibold text-zinc-200 hover:bg-white/[0.04]"
            >
              {t(`${NS}.goSmart`, { defaultValue: "Smart Office →" })}
            </Link>
          )}
          <Link
            href="/site#b2b"
            className="inline-flex min-h-[44px] items-center justify-center rounded-xl border border-white/10 px-4 py-2.5 text-sm text-zinc-400 hover:text-zinc-200"
          >
            {t(`${NS}.ctaB2b`, { defaultValue: "Zu den B2B-Leistungen" })}
          </Link>
        </div>

        {error ? (
          <p className="mt-4 rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {error}
          </p>
        ) : null}

        {phase === "analyzing" ? (
          <div className="mt-10 rounded-2xl border border-sky-400/25 bg-sky-500/[0.06] p-6">
            <h2 className="text-lg font-semibold text-white">
              {t(`${NS}.analyzingTitle`, { defaultValue: "Dokument wird analysiert…" })}
            </h2>
            <p className="mt-2 text-sm text-zinc-400">
              {t(`${NS}.analyzingBody`, {
                defaultValue: "Sprache, Dokumenttyp und Inhalt werden erkannt.",
              })}
            </p>
            <ul className="mt-4 space-y-1 text-sm text-zinc-300">
              <li>✓ Dateityp</li>
              <li>✓ Text / Struktur</li>
              <li>✓ Sprache</li>
              <li>✓ Mögliche Aktionen</li>
            </ul>
          </div>
        ) : null}

        {phase === "proposal" && proposal?.filled ? (
          <section className="mt-10 space-y-5 rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <h2 className="text-xl font-semibold text-white">
              {proposal.title_de || "Wir haben Ihr Dokument verstanden"}
            </h2>
            <dl className="grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-zinc-500">Dokument</dt>
                <dd className="text-white">{proposal.filename || job?.filename}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Typ</dt>
                <dd className="text-white">
                  {proposal.detected?.document_type_label_de || "—"}
                </dd>
              </div>
              <div>
                <dt className="text-zinc-500">Sprache</dt>
                <dd className="text-white">{proposal.detected?.language_label_de || "—"}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Seiten</dt>
                <dd className="text-white">{proposal.detected?.pages ?? "—"}</dd>
              </div>
            </dl>
            {proposal.detected?.ocr_status === "pending" ? (
              <p className="text-xs text-amber-200/90">
                Scan/Foto erkannt — OCR folgt in Stage 3. Aktionen trotzdem wählbar.
              </p>
            ) : null}

            {proposal.show_choice_cards || nextStep === "select_action" ? (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-zinc-200">
                  Was möchten Sie machen?
                </h3>
                <div className="grid gap-2 sm:grid-cols-2">
                  {(proposal.choice_options || []).map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      disabled={busy}
                      onClick={() => onChoose(opt.id)}
                      className="rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-left text-sm text-white hover:border-sky-400/40 hover:bg-sky-500/10"
                    >
                      <span className="font-medium">{opt.label_de}</span>
                      {opt.price_eur != null ? (
                        <span className="mt-1 block text-xs text-zinc-400">
                          ab €{Number(opt.price_eur).toFixed(2).replace(".", ",")}
                        </span>
                      ) : null}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {nextStep === "configure_translate" ||
            (proposal.task === "translate" && !proposal.target_language) ? (
              <div className="space-y-3 rounded-xl border border-sky-400/20 bg-sky-500/[0.05] p-4">
                <h3 className="text-sm font-semibold text-white">Übersetzung konfigurieren</h3>
                <label className="block text-xs text-zinc-400">
                  Zielsprache
                  <select
                    className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-sm text-white"
                    value={targetLang}
                    onChange={(e) => setTargetLang(e.target.value)}
                  >
                    {languages
                      .filter((l) => l.code !== "auto")
                      .map((l) => (
                        <option key={l.code} value={l.code}>
                          {l.native} ({l.label_de})
                        </option>
                      ))}
                  </select>
                </label>
                <label className="block text-xs text-zinc-400">
                  Ausgabe
                  <select
                    className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-sm text-white"
                    value={outputFmt}
                    onChange={(e) => setOutputFmt(e.target.value)}
                  >
                    <option value="pdf">PDF</option>
                    <option value="docx">Word (DOCX)</option>
                    <option value="txt">Text</option>
                  </select>
                </label>
                <p className="text-sm text-sky-100">
                  Voraussichtlicher Preis: €
                  {Number(proposal.price_eur || 7.9).toFixed(2).replace(".", ",")}
                </p>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onConfigureTranslate()}
                  className="inline-flex min-h-[44px] items-center justify-center rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-500"
                >
                  Übernehmen
                </button>
              </div>
            ) : null}

            {nextStep === "awaiting_stage3" ? (
              <div className="space-y-3 border-t border-white/10 pt-4">
                <p className="text-sm text-zinc-300">
                  Aufgabe: <strong className="text-white">{proposal.task_label_de || proposal.task}</strong>
                  {proposal.target_language ? ` → ${proposal.target_language}` : ""}
                  {proposal.result_format ? ` · ${proposal.result_format.toUpperCase()}` : ""}
                </p>
                <p className="text-sm text-sky-100">
                  Voraussichtlicher Preis: €
                  {Number(proposal.price_eur || 0).toFixed(2).replace(".", ",")}
                </p>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onContinue()}
                  className="inline-flex min-h-[44px] items-center justify-center rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-zinc-900 hover:bg-zinc-100"
                >
                  {proposal.continue_label_de || "Weiter"}
                </button>
                <p className="text-xs text-zinc-500">{proposal.continue_hint_de}</p>
              </div>
            ) : null}
          </section>
        ) : null}

        {phase === "done" ? (
          <div className="mt-10 rounded-2xl border border-emerald-400/25 bg-emerald-500/[0.06] p-6">
            <h2 className="text-lg font-semibold text-white">Ergebnis bereit</h2>
            <p className="mt-2 text-sm text-zinc-300">
              Quality Gate:{" "}
              <strong className="text-white">
                {job?.quality?.passed ? "PASS" : "—"}
              </strong>
              {job?.artifact?.filename ? (
                <>
                  {" "}
                  · Datei: <span className="text-white">{job.artifact.filename}</span>
                </>
              ) : null}
            </p>
            <button
              type="button"
              disabled={busy || !job?.artifact_download}
              onClick={() => onDownload()}
              className="mt-5 inline-flex min-h-[44px] items-center justify-center rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-zinc-900 hover:bg-zinc-100 disabled:opacity-50"
            >
              Datei herunterladen
            </button>
            <p className="mt-3 text-xs text-zinc-500">
              Stage 3 Preview — Stripe LIVE und Werbung noch HOLD. {BRAND_NAME} Office · Job{" "}
              {job?.job_id}
            </p>
          </div>
        ) : null}
      </main>
      <PublicFunnelFooter />
    </PublicPageShell>
  );
}
