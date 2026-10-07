"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useI18n } from "@/components/I18nProvider";
import { WHEN_TRIGGERS } from "@/lib/viral/catalog";

type SpacePayload = {
  space: {
    code: string;
    kind: string;
    title: string;
    unlocked: boolean;
    isOwner: boolean;
    answerCount: number;
    config: Record<string, unknown>;
    sharePath: string;
  };
  answers: Array<Record<string, unknown>>;
  patterns: Array<{ label: string; pct: number; count: number }>;
  score: number | null;
};

export default function ViralSpacePage() {
  const { t } = useI18n();
  const params = useParams<{ code: string }>();
  const code = params.code;
  const [data, setData] = useState<SpacePayload | null>(null);
  const [error, setError] = useState("");
  const [text, setText] = useState("");
  const [words, setWords] = useState("");
  const [answers, setAnswers] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [done, setDone] = useState(false);

  const load = useCallback(async () => {
    const r = await fetch(`/api/viral/${code}`, { credentials: "include", cache: "no-store" });
    const d = await r.json();
    if (!r.ok) {
      setError(d.error || t("viral.notFound"));
      return;
    }
    setData(d);
    const qs = (d.space.config?.questions as string[]) || [];
    setAnswers(qs.map(() => ""));
  }, [code, t]);

  useEffect(() => {
    load();
  }, [load]);

  function kindHint(kind: string, config: Record<string, unknown>): string {
    if (kind === "say") {
      return String(config.message || t("viral.defaultMessage"));
    }
    if (kind === "when") {
      const triggerId = String(config.trigger || "need_it");
      const known = WHEN_TRIGGERS.find((w) => w.id === triggerId);
      const triggerLabel = known ? t(known.labelKey) : triggerId;
      return t("viral.trigger", { trigger: triggerLabel });
    }
    const key = `viral.kind.${kind}` as const;
    if (
      kind === "think" ||
      kind === "words" ||
      kind === "ask" ||
      kind === "map" ||
      kind === "duo" ||
      kind === "fragment"
    ) {
      return t(key);
    }
    return "";
  }

  async function submit() {
    if (!data) return;
    setBusy(true);
    setError("");
    const body: Record<string, unknown> = {};
    if (data.space.kind === "words") {
      body.words = words
        .split(/[,\n]/)
        .map((w) => w.trim())
        .filter(Boolean)
        .slice(0, 3);
    } else if (data.space.kind === "think" || data.space.kind === "ask" || data.space.kind === "fragment") {
      body.text = text;
      if (data.space.kind === "ask") body.question = text;
    } else if (data.space.kind === "map" || data.space.kind === "duo") {
      body.answers = answers;
    } else {
      body.text = text;
    }
    const r = await fetch(`/api/viral/${code}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const d = await r.json();
    setBusy(false);
    if (!r.ok) {
      setError(d.error || t("viral.errorSend"));
      return;
    }
    setDone(true);
    setText("");
    setWords("");
    await load();
  }

  async function unlock() {
    setBusy(true);
    const r = await fetch(`/api/viral/${code}/unlock`, { method: "POST", credentials: "include" });
    const d = await r.json();
    setBusy(false);
    if (!r.ok) {
      setError(d.error || t("viral.errorUnlock"));
      return;
    }
    if (d.checkoutUrl) window.location.href = d.checkoutUrl;
    else await load();
  }

  async function copyShare() {
    if (!data) return;
    const url = `${window.location.origin}${data.space.sharePath}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  if (error && !data) {
    return (
      <main className="anon-card mx-auto max-w-md p-6 text-center">
        <p className="text-rose-300">{error}</p>
        <Link href="/loops" className="anon-btn anon-btn-primary mt-4 inline-flex">
          {t("viral.createOwn")}
        </Link>
      </main>
    );
  }

  if (!data) {
    return <main className="p-8 text-center anon-muted">{t("viral.loading")}</main>;
  }

  const qs = (data.space.config.questions as string[]) || [];
  const isOwner = data.space.isOwner;

  return (
    <main className="anim-in mx-auto max-w-md space-y-4 pb-12">
      <section className="anon-card p-6 text-center">
        <p className="text-xs tracking-[0.3em] text-violet-200">ANON</p>
        <h1 className="mt-3 text-2xl font-semibold">{data.space.title}</h1>
        <p className="mt-2 text-sm anon-muted">{kindHint(data.space.kind, data.space.config)}</p>
        <p className="mt-3 text-xs text-violet-200">
          {t("viral.responses", { count: data.space.answerCount })}
        </p>
      </section>

      {isOwner && (
        <section className="anon-card space-y-3 p-5">
          <p className="text-sm font-medium">{t("viral.shareLink")}</p>
          <p className="break-all font-mono text-xs text-violet-200">
            {typeof window !== "undefined" ? window.location.origin : ""}
            {data.space.sharePath}
          </p>
          <button type="button" className="anon-btn anon-btn-primary w-full" onClick={copyShare}>
            {copied ? t("viral.copied") : t("viral.copyLink")}
          </button>
          {(data.space.kind === "think" || data.space.kind === "words") && !data.space.unlocked && (
            <button type="button" className="anon-btn anon-btn-ghost w-full" disabled={busy} onClick={unlock}>
              {t("viral.unlockMap")}
            </button>
          )}
        </section>
      )}

      {isOwner && (data.patterns.length > 0 || data.score != null) && (
        <section className="anon-card p-5">
          <h2 className="font-semibold">
            {data.score != null
              ? t("viral.matchScore", { score: data.score })
              : t("viral.howPeopleSee", { count: data.space.answerCount })}
          </h2>
          {!data.space.unlocked && data.space.kind !== "duo" && data.space.kind !== "map" ? (
            <p className="mt-2 text-sm anon-muted">{t("viral.unlockToSee")}</p>
          ) : (
            <ul className="mt-4 space-y-2">
              {data.patterns.map((p) => (
                <li key={p.label} className="flex justify-between text-sm">
                  <span>{p.label}</span>
                  <span className="text-violet-200">{p.pct}%</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {!isOwner && !done && (
        <section className="anon-card space-y-3 p-5">
          {(data.space.kind === "map" || data.space.kind === "duo") &&
            qs.map((q, i) => (
              <label key={q} className="block text-sm">
                {q}
                <input
                  className="anon-input mt-2"
                  value={answers[i] || ""}
                  onChange={(e) => {
                    const next = [...answers];
                    next[i] = e.target.value;
                    setAnswers(next);
                  }}
                />
              </label>
            ))}

          {data.space.kind === "words" && (
            <label className="block text-sm">
              {t("viral.threeWords")}
              <input className="anon-input mt-2" value={words} onChange={(e) => setWords(e.target.value)} />
            </label>
          )}

          {["think", "ask", "fragment", "say", "when"].includes(data.space.kind) && (
            <label className="block text-sm">
              {data.space.kind === "ask" ? t("viral.yourQuestion") : t("viral.yourAnswer")}
              <textarea
                className="anon-input mt-2 min-h-28"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </label>
          )}

          {error && <p className="text-sm text-rose-300">{error}</p>}
          <button type="button" className="anon-btn anon-btn-primary w-full" disabled={busy} onClick={submit}>
            {busy ? t("leave.busy") : t("viral.send")}
          </button>
        </section>
      )}

      {done && (
        <section className="anon-card p-6 text-center">
          <p className="text-3xl">✨</p>
          <h2 className="mt-3 text-xl font-semibold">{t("viral.leftTitle")}</h2>
          <p className="mt-2 text-sm anon-muted">{t("viral.leftSub")}</p>
          <Link href="/loops" className="anon-btn anon-btn-primary mt-5 inline-flex w-full">
            {t("viral.createAnonLink")}
          </Link>
        </section>
      )}

      {isOwner && data.space.kind === "map" && (
        <section className="anon-card p-5">
          <h2 className="font-semibold mb-3">{t("viral.ownerMapTitle")}</h2>
          {qs.map((q, i) => (
            <label key={q} className="mb-3 block text-sm">
              {q}
              <input
                className="anon-input mt-2"
                value={answers[i] || ""}
                onChange={(e) => {
                  const next = [...answers];
                  next[i] = e.target.value;
                  setAnswers(next);
                }}
              />
            </label>
          ))}
          <button
            type="button"
            className="anon-btn anon-btn-primary w-full"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              await fetch(`/api/viral/${code}`, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ side: "owner", answers }),
              });
              setBusy(false);
              await load();
            }}
          >
            {t("viral.saveMap")}
          </button>
        </section>
      )}
    </main>
  );
}
