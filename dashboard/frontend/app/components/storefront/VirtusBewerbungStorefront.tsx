"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { PublicPageShell } from "../PublicPageShell";
import { PublicFunnelFooter } from "../navigation/PublicFunnelFooter";
import {
  attachBewerbungPhoto,
  checkoutOfficeJob,
  createOfficeJob,
  downloadOfficeArtifact,
  submitBewerbungProfile,
  type OfficeJobView,
} from "../../lib/officeApi";
import { saveOfficeJobToken } from "../../lib/officeSession";
import { useOfficeT } from "../../lib/useOfficeT";
import { logCommerceEvent } from "../../lib/commerceFunnel";
import "../office/office-shell.css";

type ActionId =
  | "lebenslauf_create"
  | "lebenslauf_improve"
  | "bewerbungsschreiben"
  | "bewerbung_paket";

const ACTION_IDS: ActionId[] = [
  "lebenslauf_create",
  "lebenslauf_improve",
  "bewerbungsschreiben",
  "bewerbung_paket",
];

export function VirtusBewerbungStorefront({ embedded = false }: { embedded?: boolean }) {
  const router = useRouter();
  const { t } = useOfficeT();
  const [action, setAction] = useState<ActionId>("lebenslauf_create");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [job, setJob] = useState<OfficeJobView | null>(null);
  const [phase, setPhase] = useState<"form" | "ready" | "done">("form");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [city, setCity] = useState("");
  const [address, setAddress] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [employer, setEmployer] = useState("");
  const [title, setTitle] = useState("");
  const [expStart, setExpStart] = useState("");
  const [expEnd, setExpEnd] = useState("");
  const [school, setSchool] = useState("");
  const [degree, setDegree] = useState("");
  const [eduStart, setEduStart] = useState("");
  const [languages, setLanguages] = useState("");
  const [skills, setSkills] = useState("");
  const [license, setLicense] = useState("");
  const [vacTitle, setVacTitle] = useState("");
  const [vacCompany, setVacCompany] = useState("");
  const [vacText, setVacText] = useState("");
  const [motivation, setMotivation] = useState("");
  const [outputFmt, setOutputFmt] = useState("pdf");

  const missing = useMemo(
    () =>
      ((job?.proposal as { missing_fields?: { id: string; label_de: string }[] })
        ?.missing_fields || []),
    [job],
  );

  function buildProfile() {
    const langs = languages
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .map((entry) => {
        const [language, level] = entry.split(":").map((x) => x.trim());
        return { language, level: level || null };
      });
    return {
      personal: {
        full_name: fullName || null,
        email: email || null,
        phone: phone || null,
        city: city || null,
        address: address || null,
        postal_code: postalCode || null,
      },
      experience:
        employer || title
          ? [
              {
                employer: employer || null,
                title: title || null,
                start: expStart || null,
                end: expEnd || null,
                bullets: [],
              },
            ]
          : [],
      education:
        school || degree
          ? [
              {
                school: school || null,
                degree: degree || null,
                start: eduStart || null,
                end: null,
              },
            ]
          : [],
      languages: langs,
      skills: skills
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      drivers_license: license
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      vacancy: {
        title: vacTitle || null,
        company: vacCompany || null,
        raw_text: vacText || null,
      },
      motivation: motivation || null,
      target_market: "DE",
    };
  }

  async function ensureJob(): Promise<{ jobId: string; ownerToken: string }> {
    if (job?.job_id && token) return { jobId: job.job_id, ownerToken: token };
    const created = await createOfficeJob({ service_preset: action, email: email || undefined });
    if (!created.job_id || !created.owner_token) {
      throw new Error(t("bewerbung.jobCreateFailed"));
    }
    setToken(created.owner_token);
    setJob(created);
    saveOfficeJobToken(created.job_id, created.owner_token, {
      filename: created.filename,
      status: created.status,
    });
    return { jobId: created.job_id, ownerToken: created.owner_token };
  }

  async function onPhoto(file: File | null) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const { jobId, ownerToken } = await ensureJob();
      const viewed = await attachBewerbungPhoto(jobId, ownerToken, file);
      setJob(viewed);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("bewerbung.photoError"));
    } finally {
      setBusy(false);
    }
  }

  async function onSubmitProfile() {
    setBusy(true);
    setError(null);
    try {
      const { jobId, ownerToken } = await ensureJob();
      logCommerceEvent("tier_select", action, "office_bewerbung");
      const viewed = await submitBewerbungProfile(jobId, ownerToken, {
        profile: buildProfile(),
        action_id: action,
        output_format: action === "bewerbung_paket" ? "zip" : outputFmt,
      });
      setJob(viewed);
      if (viewed.proposal?.next_step === "awaiting_stage3") {
        setPhase("ready");
      } else {
        setPhase("form");
        const miss = (viewed.proposal as { missing_fields?: { label_de: string }[] })
          ?.missing_fields;
        if (miss?.length) {
          setError(
            `${t("bewerbung.missingPrefix")} ${miss.map((m) => m.label_de).join(", ")}`,
          );
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"));
    } finally {
      setBusy(false);
    }
  }

  async function onPay() {
    if (!job?.job_id || !token) return;
    setBusy(true);
    setError(null);
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      const orderPath = `/office/order/${encodeURIComponent(job.job_id)}`;
      saveOfficeJobToken(job.job_id, token, {
        filename: job.filename,
        status: job.status,
      });
      const viewed = await checkoutOfficeJob(job.job_id, token, {
        success_url: `${origin}${orderPath}?paid=1`,
        cancel_url: `${origin}${orderPath}?cancel=1`,
        email: email || undefined,
      });
      setJob(viewed);
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
      setError(e instanceof Error ? e.message : t("bewerbung.checkoutError"));
    } finally {
      setBusy(false);
    }
  }

  async function onDownload() {
    if (!job?.job_id || !token) return;
    setBusy(true);
    try {
      await downloadOfficeArtifact(job.job_id, token);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("bewerbung.downloadFailed"));
    } finally {
      setBusy(false);
    }
  }

  const body = (
    <div className={embedded ? "" : "mx-auto max-w-3xl px-4 py-12"}>
      {embedded ? (
        <div className="mb-6 flex flex-wrap items-center gap-3 text-sm">
          <Link
            href="/office"
            className="rounded-lg border border-[var(--vo-border)] px-3 py-1.5 text-[var(--vo-ink)] hover:bg-black/[0.03]"
          >
            ← {t("back")}
          </Link>
          <Link
            href="/office"
            className="rounded-lg px-3 py-1.5 text-[var(--vo-muted)] underline-offset-2 hover:text-[var(--vo-ink)] hover:underline"
          >
            {t("cancel")}
          </Link>
          <Link
            href="/office"
            className="ml-auto text-xs text-[var(--vo-muted)] underline-offset-2 hover:underline"
          >
            {t("backHome")}
          </Link>
        </div>
      ) : null}
      <h1 className="vo-display text-3xl font-semibold tracking-tight text-[var(--vo-ink)] sm:text-4xl">
        {t("bewerbung.title")}
      </h1>
      <p className="mt-3 text-sm text-[var(--vo-muted)]">{t("bewerbung.lead")}</p>
      <p className="mt-2 text-xs text-[var(--vo-muted)]">{t("langSeparationHint")}</p>

      <div className="mt-4 rounded-xl border border-[var(--vo-border)] bg-[var(--vo-accent-soft)]/50 px-4 py-3 text-xs text-[var(--vo-ink)]">
        {t("bewerbung.honesty")}
      </div>

      <div className="mt-8 grid gap-3 sm:grid-cols-2">
        {ACTION_IDS.map((id) => (
          <button
            key={id}
            type="button"
            disabled={busy}
            onClick={() => {
              setAction(id);
              setToken(null);
              setJob(null);
              setPhase("form");
            }}
            className={`rounded-xl border px-4 py-3 text-left text-sm transition ${
              action === id
                ? "border-[var(--vo-accent)] bg-[var(--vo-accent-soft)] text-[var(--vo-ink)]"
                : "border-[var(--vo-border)] bg-[var(--vo-surface)] text-[var(--vo-muted)] hover:border-[var(--vo-accent)]/40"
            }`}
          >
            <span className="font-semibold text-[var(--vo-ink)]">
              {t(`bewerbung.actions.${id}.label`)}
            </span>
            <span className="mt-1 block text-xs text-[var(--vo-muted)]">
              {t(`bewerbung.actions.${id}.hint`)}
            </span>
          </button>
        ))}
      </div>

      <div className="mt-8 space-y-4 rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-5">
        <h2 className="text-sm font-semibold text-[var(--vo-ink)]">{t("bewerbung.profileTitle")}</h2>
        <p className="text-xs text-[var(--vo-muted)]">
          {t("cvTargetMarket")}: Deutschland · {t("documentLanguage")}: Deutsch
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label={t("bewerbung.fields.fullName")} value={fullName} onChange={setFullName} />
          <Field label={t("bewerbung.fields.email")} value={email} onChange={setEmail} />
          <Field label={t("bewerbung.fields.phone")} value={phone} onChange={setPhone} />
          <Field label={t("bewerbung.fields.city")} value={city} onChange={setCity} />
          <Field label={t("bewerbung.fields.address")} value={address} onChange={setAddress} />
          <Field label={t("bewerbung.fields.postalCode")} value={postalCode} onChange={setPostalCode} />
          <Field label={t("bewerbung.fields.employer")} value={employer} onChange={setEmployer} />
          <Field label={t("bewerbung.fields.title")} value={title} onChange={setTitle} />
          <Field
            label={t("bewerbung.fields.expStart")}
            value={expStart}
            onChange={setExpStart}
            placeholder={t("bewerbung.placeholders.expStart")}
          />
          <Field
            label={t("bewerbung.fields.expEnd")}
            value={expEnd}
            onChange={setExpEnd}
            placeholder={t("bewerbung.placeholders.expEnd")}
          />
          <Field label={t("bewerbung.fields.school")} value={school} onChange={setSchool} />
          <Field label={t("bewerbung.fields.degree")} value={degree} onChange={setDegree} />
          <Field label={t("bewerbung.fields.eduStart")} value={eduStart} onChange={setEduStart} />
          <Field
            label={t("bewerbung.fields.languages")}
            value={languages}
            onChange={setLanguages}
            placeholder={t("bewerbung.placeholders.languages")}
          />
          <Field label={t("bewerbung.fields.skills")} value={skills} onChange={setSkills} />
          <Field
            label={t("bewerbung.fields.license")}
            value={license}
            onChange={setLicense}
            placeholder={t("bewerbung.placeholders.license")}
          />
        </div>

        {(action === "bewerbungsschreiben" || action === "bewerbung_paket") && (
          <div className="grid gap-3 sm:grid-cols-2">
            <Field
              label={t("bewerbung.fields.vacancyTitle")}
              value={vacTitle}
              onChange={setVacTitle}
            />
            <Field
              label={t("bewerbung.fields.vacancyCompany")}
              value={vacCompany}
              onChange={setVacCompany}
            />
            <label className="block text-xs text-[var(--vo-muted)] sm:col-span-2">
              {t("bewerbung.fields.vacancyNotes")}
              <textarea
                className="mt-1 w-full rounded-lg border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm text-[var(--vo-ink)]"
                rows={4}
                value={vacText}
                onChange={(e) => setVacText(e.target.value)}
              />
            </label>
            <label className="block text-xs text-[var(--vo-muted)] sm:col-span-2">
              {t("bewerbung.fields.motivation")}
              <textarea
                className="mt-1 w-full rounded-lg border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm text-[var(--vo-ink)]"
                rows={3}
                value={motivation}
                onChange={(e) => setMotivation(e.target.value)}
              />
            </label>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs text-[var(--vo-muted)]">
            {t("bewerbung.photoLabel")}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="mt-1 block text-sm"
              onChange={(e) => onPhoto(e.target.files?.[0] || null)}
            />
          </label>
          <button
            type="button"
            disabled={busy}
            onClick={onSubmitProfile}
            className="rounded-xl bg-[var(--vo-accent)] px-5 py-2.5 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
          >
            {busy ? t("bewerbung.checking") : t("bewerbung.checkProfile")}
          </button>
        </div>
      </div>

      {missing.length ? (
        <ul className="mt-4 list-disc space-y-1 rounded-xl border border-amber-300 bg-amber-50 px-5 py-3 text-sm text-amber-950">
          {missing.map((m) => (
            <li key={m.id}>{m.label_de}</li>
          ))}
        </ul>
      ) : null}

      {error ? (
        <p className="mt-4 rounded-xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {error}
        </p>
      ) : null}

      {phase === "ready" || phase === "done" ? (
        <div className="mt-6 space-y-4">
          {phase === "ready" && job?.proposal?.preview ? (
            <div className="rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-bg)] p-5">
              <h3 className="vo-display text-xl font-semibold text-[var(--vo-ink)]">
                {t("preview.title")}
              </h3>
              <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-[var(--vo-muted)]">{t("preview.style")}</dt>
                  <dd className="font-medium text-[var(--vo-ink)]">
                    {job.proposal.preview.style || t("preview.styleGermanProfessional")}
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--vo-muted)]">{t("preview.language")}</dt>
                  <dd className="font-medium text-[var(--vo-ink)]">
                    {job.proposal.preview.language || "Deutsch"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--vo-muted)]">{t("preview.pages")}</dt>
                  <dd className="font-medium text-[var(--vo-ink)]">
                    {job.proposal.preview.estimated_pages ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--vo-muted)]">{t("preview.product")}</dt>
                  <dd className="font-medium text-[var(--vo-ink)]">
                    {job.proposal.preview.product || t(`bewerbung.actions.${action}.label`)}
                  </dd>
                </div>
              </dl>
              {(job.proposal.preview.structure || []).length ? (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--vo-muted)]">
                    {t("preview.structure")}
                  </p>
                  <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm text-[var(--vo-ink)]">
                    {job.proposal.preview.structure!.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {job.proposal.preview.excerpt ? (
                <pre className="mt-4 max-h-40 overflow-auto whitespace-pre-wrap rounded-xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-3 text-xs text-[var(--vo-muted)]">
                  {job.proposal.preview.excerpt}
                </pre>
              ) : null}
              <p className="mt-3 text-sm font-semibold text-[var(--vo-accent)]">
                {t("preview.fullAfterPay")}
              </p>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-3">
            {phase === "ready" ? (
              <button
                type="button"
                disabled={busy}
                onClick={onPay}
                className="rounded-xl bg-[var(--vo-accent)] px-5 py-2.5 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
              >
                {t("bewerbung.payCta")}
              </button>
            ) : null}
            {phase === "done" ? (
              <button
                type="button"
                disabled={busy}
                onClick={onDownload}
                className="rounded-xl bg-[var(--vo-accent)] px-5 py-2.5 text-sm font-semibold text-white"
              >
                {t("bewerbung.download")}
              </button>
            ) : null}
          </div>
        </div>
      ) : null}

      {!embedded ? (
        <div className="mt-10 flex flex-wrap gap-3 text-sm">
          <Link href="/office" className="text-[var(--vo-muted)] hover:text-[var(--vo-ink)]">
            ← {t("nav.home")}
          </Link>
          <Link href="/office/translate" className="text-[var(--vo-muted)] hover:text-[var(--vo-ink)]">
            {t("nav.translate")}
          </Link>
        </div>
      ) : null}
    </div>
  );

  if (embedded) return body;
  return (
    <PublicPageShell>
      <div className="vo-shell min-h-screen px-4 py-10">{body}</div>
      <PublicFunnelFooter />
    </PublicPageShell>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block text-xs text-[var(--vo-muted)]">
      {label}
      <input
        className="mt-1 w-full rounded-lg border border-[var(--vo-border)] bg-[var(--vo-bg)] px-3 py-2 text-sm text-[var(--vo-ink)]"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
