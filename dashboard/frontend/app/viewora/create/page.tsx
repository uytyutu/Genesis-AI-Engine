"use client";

import Link from "next/link";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  createStudio,
  fetchAccount,
  fetchCatalog,
  type VieworaCatalog,
} from "../lib/api";

type Package = {
  mode?: string;
  title?: string;
  hooks?: string[];
  captions?: string[];
  script?: Array<{ role: string; text: string }>;
  storyboard?: Array<{ t: string; label: string; visual: string; line: string }>;
  visual_dna?: Record<string, string>;
  watchability?: {
    label?: string;
    scores: Record<string, number>;
    overall: number;
    weakest: string;
    optimize_hint?: string;
    optimized?: boolean;
  };
  viral_score?: {
    label?: string;
    scores: Record<string, number>;
    overall: number;
    weakest: string;
    optimize_hint?: string;
    optimized?: boolean;
  };
  render?: { note?: string; status?: string; mp4_available?: boolean };
  version_label?: string;
  pipeline?: string[];
};

function CreateStudioInner() {
  const params = useSearchParams();
  const [catalog, setCatalog] = useState<VieworaCatalog | null>(null);
  const [brief, setBrief] = useState("");
  const [creationType, setCreationType] = useState("viral_short");
  const [mode, setMode] = useState<string>("");
  const [dna, setDna] = useState<Record<string, string>>({});
  const [productStyle, setProductStyle] = useState("TikTok style");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [accountLabel, setAccountLabel] = useState("…");
  const [pkg, setPkg] = useState<Package | null>(null);
  const [versions, setVersions] = useState<Package[]>([]);
  const [hooks, setHooks] = useState<string[]>([]);
  const [plan30, setPlan30] = useState<Array<Record<string, unknown>> | null>(null);
  const [rationale, setRationale] = useState("");
  const [dubTracks, setDubTracks] = useState<Array<Record<string, unknown>> | null>(null);
  const [creatorBatch, setCreatorBatch] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const b = params.get("brief");
    if (b) setBrief(b);
    fetchCatalog().then(setCatalog).catch(() => undefined);
    fetchAccount()
      .then((a) => {
        const free = a.account.free_creations_left;
        const credits = a.account.credits;
        setAccountLabel(
          a.account.plan_id === "free"
            ? `FREE · ${free} creations left`
            : `${a.plan.name} · ${credits} credits`
        );
      })
      .catch(() => setAccountLabel("Guest"));
  }, [params]);

  const dnaKeys = useMemo(() => Object.keys(catalog?.visual_dna || {}), [catalog]);

  async function run(action: string) {
    if (!brief.trim()) {
      setError("Опишите, что создать — или вставьте тему / ссылку / товар.");
      return;
    }
    setBusy(action);
    setError("");
    try {
      const out = await createStudio({
        brief: brief.trim(),
        creation_type: creationType,
        mode: mode || null,
        visual_dna: Object.keys(dna).length ? dna : null,
        product_style: productStyle,
        action,
      });
      const acc = out.account;
      setAccountLabel(
        acc.plan_id === "free"
          ? `FREE · ${acc.free_creations_left} creations left`
          : `${acc.plan_id.toUpperCase()} · ${acc.credits} credits`
      );
      const r = out.result || {};
      if (r.suggestion && typeof r.suggestion === "object") {
        const s = r.suggestion as { mode?: string; visual_dna?: Record<string, string>; rationale?: string };
        if (s.mode) setMode(s.mode);
        if (s.visual_dna) setDna(s.visual_dna);
        if (s.rationale) setRationale(s.rationale);
      }
      if (r.package) setPkg(r.package as Package);
      if (r.versions) {
        setVersions(r.versions as Package[]);
        setPkg((r.versions as Package[])[0] || null);
      }
      if (r.lab && r.versions) {
        setVersions(r.versions as Package[]);
        setPkg((r.versions as Package[])[0] || null);
      }
      if (r.hooks) setHooks(r.hooks as string[]);
      if (r.visual_dna) setDna(r.visual_dna as Record<string, string>);
      if (r.days) setPlan30(r.days as Array<Record<string, unknown>>);
      if (r.tracks) setDubTracks(r.tracks as Array<Record<string, unknown>>);
      if (r.creator) setCreatorBatch(r as Record<string, unknown>);
      if (r.shorts) {
        setVersions(
          (r.shorts as Array<Record<string, unknown>>).map((s) => ({
            title: String(s.title || ""),
            hooks: [String(s.hook || "")],
            captions: (s.captions as string[]) || [],
            mode: String(s.mode || ""),
            version_label: `#${s.index}`,
          }))
        );
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка";
      setError(msg);
    } finally {
      setBusy("");
    }
  }

  const scoreBlock = pkg?.watchability || pkg?.viral_score;
  const scores = scoreBlock?.scores;

  return (
    <div className="viewora-studio">
      <div className="viewora-panel">
        <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
          <h2>Studio</h2>
          <span className="viewora-muted" style={{ fontSize: "0.85rem" }}>
            {accountLabel} · <Link href="/viewora/pricing">Upgrade</Link>
          </span>
        </div>

        <label className="viewora-label" htmlFor="brief">
          What do you want to create?
        </label>
        <textarea
          id="brief"
          className="viewora-textarea"
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          placeholder="Сделай эмоциональный TikTok о новом треке…"
        />

        <div style={{ marginTop: "1rem" }}>
          <span className="viewora-label">Тип</span>
          <div className="viewora-chip-row" style={{ marginTop: 0 }}>
            {(catalog?.creation_types || []).map((t) => (
              <button
                key={t.id}
                type="button"
                className={`viewora-chip${creationType === t.id ? " is-active" : ""}`}
                onClick={() => setCreationType(t.id)}
              >
                {t.emoji} {t.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginTop: "1rem" }}>
          <span className="viewora-label">Режим</span>
          <div className="viewora-chip-row" style={{ marginTop: 0 }}>
            {(catalog?.modes || []).map((m) => (
              <button
                key={m.id}
                type="button"
                className={`viewora-chip${mode === m.id ? " is-active" : ""}`}
                onClick={() => setMode(m.id)}
                title={m.blurb}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginTop: "1rem" }}>
          <span className="viewora-label">Visual DNA</span>
          <div style={{ display: "grid", gap: "0.65rem" }}>
            {dnaKeys.map((key) => (
              <div key={key}>
                <label className="viewora-label" htmlFor={`dna-${key}`}>
                  {key}
                </label>
                <select
                  id={`dna-${key}`}
                  className="viewora-select"
                  value={dna[key] || ""}
                  onChange={(e) =>
                    setDna((prev) => ({ ...prev, [key]: e.target.value }))
                  }
                >
                  <option value="">Auto</option>
                  {(catalog?.visual_dna?.[key] || []).map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>

        {creationType === "product_video" ? (
          <div style={{ marginTop: "1rem" }}>
            <label className="viewora-label" htmlFor="pstyle">
              Product style
            </label>
            <select
              id="pstyle"
              className="viewora-select"
              value={productStyle}
              onChange={(e) => setProductStyle(e.target.value)}
            >
              {(catalog?.product_ad_styles || []).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        <div className="viewora-actions">
          <button
            type="button"
            className="viewora-btn viewora-btn-primary"
            disabled={!!busy}
            onClick={() => run("create")}
          >
            {busy === "create" ? "…" : "✨ CREATE"}
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-gold"
            disabled={!!busy}
            onClick={() => run("make_it_better")}
          >
            {busy === "make_it_better" ? "…" : "✨ MAKE IT BETTER"}
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("random_style")}
          >
            RANDOM STYLE
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("generate_10")}
          >
            CREATE 10 VERSIONS
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("viral_lab")}
          >
            VIRAL LAB
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("hook_lab")}
          >
            HOOK LAB
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("optimize")}
          >
            ✨ OPTIMIZE
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("product_video")}
          >
            PRODUCT MODE
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("podcast_shorts")}
          >
            PODCAST → 20
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("content_machine")}
          >
            30-DAY MACHINE
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("dubbing")}
          >
            DUBBING ×7
          </button>
          <button
            type="button"
            className="viewora-btn viewora-btn-ghost"
            disabled={!!busy}
            onClick={() => run("ai_creator_batch")}
          >
            AI CREATOR ×5
          </button>
        </div>

        {error ? (
          <div className="viewora-toast">
            {error}{" "}
            {error.toLowerCase().includes("кредит") ||
            error.toLowerCase().includes("free") ||
            error.toLowerCase().includes("plan") ? (
              <Link href="/viewora/pricing"> → Pricing</Link>
            ) : null}
          </div>
        ) : null}
        {rationale ? <div className="viewora-toast viewora-ok">{rationale}</div> : null}
      </div>

      <div className="viewora-panel">
        <h2>Preview</h2>
        <div className="viewora-phone" style={{ marginBottom: "1.25rem" }}>
          <div className="viewora-phone-screen">
            <div className="viewora-phone-caption">
              {pkg?.hooks?.[0] || "Ваш hook появится здесь"}
            </div>
            <div className="viewora-phone-meta">
              {(pkg?.mode || mode || "mode").toUpperCase()}
              {scoreBlock ? ` · WATCHABILITY ${scoreBlock.overall}` : ""}
            </div>
          </div>
        </div>

        {pkg?.title ? (
          <p>
            <strong>{pkg.title}</strong>
          </p>
        ) : (
          <p className="viewora-muted">Создайте ролик — справа появится пакет: hook, captions, score, storyboard.</p>
        )}

        {scores && scoreBlock ? (
          <div style={{ marginTop: "1rem" }}>
            <span className="viewora-label">
              WATCHABILITY · {scoreBlock.overall}/100
            </span>
            <div className="viewora-score-row">
              {Object.entries(scores).map(([k, v]) => (
                <div key={k} className="viewora-score-bar">
                  <span>{k.toUpperCase()}</span>
                  <div className="viewora-score-track">
                    <div className="viewora-score-fill" style={{ width: `${v}%` }} />
                  </div>
                  <span>{v}</span>
                </div>
              ))}
            </div>
            {scoreBlock.optimize_hint ? (
              <p className="viewora-muted" style={{ marginTop: "0.65rem", fontSize: "0.85rem" }}>
                {scoreBlock.optimize_hint}
              </p>
            ) : null}
          </div>
        ) : null}

        {pkg?.storyboard?.length ? (
          <div style={{ marginTop: "1.25rem" }}>
            <span className="viewora-label">Storyboard</span>
            {pkg.storyboard.map((b) => (
              <div key={`${b.t}-${b.label}`} className="viewora-beat">
                <strong>
                  {b.t} · {b.label}
                </strong>
                <span className="viewora-muted">
                  {b.visual} — {b.line}
                </span>
              </div>
            ))}
          </div>
        ) : null}

        {pkg?.captions?.length ? (
          <div style={{ marginTop: "1.25rem" }}>
            <span className="viewora-label">Captions</span>
            <ul className="viewora-muted" style={{ margin: 0, paddingLeft: "1.1rem" }}>
              {pkg.captions.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {pkg?.visual_dna ? (
          <div style={{ marginTop: "1.25rem" }}>
            <span className="viewora-label">Applied DNA</span>
            <div className="viewora-chip-row" style={{ marginTop: 0 }}>
              {Object.entries(pkg.visual_dna).map(([k, v]) => (
                <span key={k} className="viewora-chip is-active">
                  {k}: {v}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {pkg?.pipeline ? (
          <p className="viewora-muted" style={{ marginTop: "1rem" }}>
            Pipeline: {pkg.pipeline.join(" → ")}
          </p>
        ) : null}

        {pkg?.render?.note ? (
          <div className="viewora-toast" style={{ marginTop: "1rem" }}>
            {pkg.render.note}
          </div>
        ) : null}

        {hooks.length ? (
          <div style={{ marginTop: "1.25rem" }}>
            <span className="viewora-label">Hook Lab · {hooks.length}</span>
            <ol className="viewora-muted" style={{ paddingLeft: "1.2rem" }}>
              {hooks.map((h) => (
                <li key={h} style={{ marginBottom: "0.35rem" }}>
                  {h}
                </li>
              ))}
            </ol>
          </div>
        ) : null}

        {versions.length ? (
          <div style={{ marginTop: "1.25rem" }}>
            <span className="viewora-label">Versions</span>
            <div className="viewora-chip-row" style={{ marginTop: 0 }}>
              {versions.map((v, i) => (
                <button
                  key={`${v.version_label || i}`}
                  type="button"
                  className={`viewora-chip${pkg === v ? " is-active" : ""}`}
                  onClick={() => setPkg(v)}
                >
                  {v.version_label || `#${i + 1}`} {v.mode || ""}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {plan30 ? (
          <div style={{ marginTop: "1.25rem" }}>
            <span className="viewora-label">30-Day Content Machine</span>
            <div style={{ maxHeight: 280, overflow: "auto" }}>
              {plan30.slice(0, 10).map((d) => (
                <div key={String(d.day)} className="viewora-beat">
                  <strong>
                    Day {String(d.day)}
                    {d.status === "today" ? " · TODAY" : ""}
                  </strong>
                  <span className="viewora-muted">
                    {String(d.hook)} — {String(d.idea)}
                  </span>
                </div>
              ))}
              <p className="viewora-muted">…и ещё {Math.max(0, plan30.length - 10)} дней в плане</p>
            </div>
          </div>
        ) : null}

        {dubTracks ? (
          <div style={{ marginTop: "1.25rem" }}>
            <span className="viewora-label">Dubbing</span>
            {dubTracks.map((t) => (
              <div key={String(t.code)} className="viewora-beat">
                <strong>
                  {String(t.flag)} {String(t.label)}
                </strong>
                <span className="viewora-muted">{String(t.adapted_hook)}</span>
              </div>
            ))}
          </div>
        ) : null}

        {creatorBatch ? (
          <div style={{ marginTop: "1.25rem" }}>
            <span className="viewora-label">AI Creator · 5 videos</span>
            <p className="viewora-muted" style={{ fontSize: "0.85rem" }}>
              {(creatorBatch.creator as { name?: string; style?: string } | undefined)?.name} ·{" "}
              {(creatorBatch.creator as { style?: string } | undefined)?.style}
            </p>
            <ol className="viewora-muted" style={{ paddingLeft: "1.2rem" }}>
              {((creatorBatch.videos as Array<Record<string, unknown>>) || []).map((v) => (
                <li key={String(v.index)}>
                  #{String(v.index)} {String(v.hook)}
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function VieworaCreatePage() {
  return (
    <Suspense fallback={<div className="viewora-panel">Loading studio…</div>}>
      <CreateStudioInner />
    </Suspense>
  );
}
