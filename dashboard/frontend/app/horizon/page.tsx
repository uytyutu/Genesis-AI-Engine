"use client";

/**
 * Horizon Studio — Internal-only Creative Director shell (Phase D).
 * Structure + Creative Bible only; no live video generation.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Platform = {
  id: string;
  label: string;
  aspect?: string;
  durations_sec?: number[];
};

type Manifest = {
  ok?: boolean;
  product?: string;
  brand_line_ru?: string;
  stage?: string;
  stage_ru?: string;
  client_sales?: boolean;
  video_generation_enabled?: boolean;
  note_ru?: string;
  platforms?: Platform[];
  goals?: string[];
  genres?: string[];
  quality_targets?: { id: string; label: string; retries?: number }[];
  product_tiers?: { id: string; label: string; detail_ru?: string }[];
  studio_steps?: { id: string; label_ru: string }[];
  creative_bible?: {
    positioning_ru?: string;
    principles?: string[];
    hook_seconds?: number;
    pipeline?: string[];
    quality_gate?: string[];
    commercial_ready_checks?: string[];
    knowledge_domains?: string[];
    orchestrator_engines_planned?: string[];
  };
  related?: { tiktok_horizon?: string };
};

const GOAL_LABELS: Record<string, string> = {
  sell: "Продать продукт",
  lead: "Получить заявку",
  brand: "Узнаваемость",
  company_story: "История компании",
  product: "Презентация продукта",
  education: "Обучение",
  case_study: "Кейс клиента",
  promo: "Акция",
};

export default function HorizonStudioPage() {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [step, setStep] = useState(0);
  const [platform, setPlatform] = useState<string>("tiktok");
  const [goal, setGoal] = useState("lead");
  const [duration, setDuration] = useState(30);
  const [genre, setGenre] = useState("commercial");
  const [quality, setQuality] = useState("premium");
  const [voice, setVoice] = useState("male_calm");
  const [music, setMusic] = useState("corporate");
  const [prompt, setPrompt] = useState("");

  const load = useCallback(async () => {
    setErr(null);
    try {
      const res = await fetch(`${API}/api/owner/horizon`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setManifest(await res.json());
    } catch (e) {
      setErr(e instanceof Error ? e.message : "load failed");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const platforms = manifest?.platforms || [];
  const selectedPlatform = useMemo(
    () => platforms.find((p) => p.id === platform) || platforms[0],
    [platforms, platform],
  );
  const steps = manifest?.studio_steps || [];
  const bible = manifest?.creative_bible;

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 text-zinc-100">
      <header className="space-y-2">
        <p className="text-[10px] uppercase tracking-widest text-amber-400/90">
          Internal Only · Phase D Proof
        </p>
        <h1 className="text-2xl font-semibold text-white">
          {manifest?.product || "Horizon Media Engine"}
        </h1>
        <p className="text-sm text-zinc-400">
          {manifest?.brand_line_ru || "AI Creative Director"}
        </p>
        <p className="rounded-lg border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-xs text-amber-100/90">
          {manifest?.stage_ru || "Internal Only"}
          {manifest?.video_generation_enabled
            ? ""
            : " · Video generation выключена — оболочка и Creative Bible."}
        </p>
        {manifest?.note_ru ? (
          <p className="text-[11px] text-zinc-500">{manifest.note_ru}</p>
        ) : null}
        <div className="flex flex-wrap gap-3 text-xs">
          <Link href="/tiktok-horizon" className="text-sky-300 hover:underline">
            TikTok Horizon (publish pipeline)
          </Link>
          <Link href="/executive" className="text-zinc-400 hover:underline">
            CEO Dashboard
          </Link>
        </div>
      </header>

      {err ? (
        <p className="text-sm text-rose-300">API: {err}</p>
      ) : null}

      {manifest?.product_tiers?.length ? (
        <section className="grid gap-2 sm:grid-cols-3">
          {manifest.product_tiers.map((t) => (
            <div
              key={t.id}
              className="rounded-xl border border-white/10 bg-zinc-900/50 px-3 py-3"
            >
              <p className="text-sm font-semibold text-white">{t.label}</p>
              <p className="mt-1 text-[11px] text-zinc-400">{t.detail_ru}</p>
            </div>
          ))}
        </section>
      ) : null}

      {bible?.positioning_ru ? (
        <section className="rounded-xl border border-white/10 bg-black/30 p-4">
          <h2 className="text-sm font-semibold text-white">Creative Bible</h2>
          <p className="mt-2 text-sm text-zinc-300">{bible.positioning_ru}</p>
          {bible.principles?.length ? (
            <ul className="mt-3 space-y-1 text-[11px] text-zinc-400">
              {bible.principles.map((p) => (
                <li key={p}>· {p}</li>
              ))}
            </ul>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2">
            {(bible.quality_gate || []).slice(0, 8).map((q) => (
              <span
                key={q}
                className="rounded border border-white/10 px-2 py-0.5 text-[10px] text-zinc-400"
              >
                {q}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      <section className="rounded-xl border border-white/10 bg-zinc-950/60 p-4">
        <div className="mb-4 flex flex-wrap gap-1">
          {steps.map((s, i) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setStep(i)}
              className={`rounded px-2 py-1 text-[10px] ${
                i === step
                  ? "bg-white/15 text-white"
                  : i < step
                    ? "text-emerald-300/80"
                    : "text-zinc-500"
              }`}
            >
              {i + 1}. {s.label_ru}
            </button>
          ))}
        </div>

        {step === 0 ? (
          <div className="grid gap-2 sm:grid-cols-2">
            {platforms.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  setPlatform(p.id);
                  if (p.durations_sec?.[0]) setDuration(p.durations_sec[0]);
                }}
                className={`rounded-lg border px-3 py-2 text-left text-sm ${
                  platform === p.id
                    ? "border-amber-400/50 bg-amber-950/30"
                    : "border-white/10 bg-black/20"
                }`}
              >
                <span className="font-medium text-white">{p.label}</span>
                <span className="mt-0.5 block text-[10px] text-zinc-500">
                  {p.aspect} · {(p.durations_sec || []).join(" / ")}s
                </span>
              </button>
            ))}
          </div>
        ) : null}

        {step === 1 ? (
          <div className="flex flex-wrap gap-2">
            {(manifest?.goals || []).map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => setGoal(g)}
                className={`rounded-lg border px-3 py-2 text-xs ${
                  goal === g
                    ? "border-amber-400/50 bg-amber-950/30 text-white"
                    : "border-white/10 text-zinc-300"
                }`}
              >
                {GOAL_LABELS[g] || g}
              </button>
            ))}
          </div>
        ) : null}

        {step === 2 ? (
          <p className="text-sm text-zinc-400">
            Аудитория (возраст / страна / ниша) — поля появятся при подключении Campaign Builder.
            Сейчас зафиксируйте нишу в Prompt Director.
          </p>
        ) : null}

        {step === 3 ? (
          <div className="flex flex-wrap gap-2">
            {(selectedPlatform?.durations_sec || [15, 30, 60]).map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDuration(d)}
                className={`rounded-lg border px-3 py-2 text-xs ${
                  duration === d
                    ? "border-amber-400/50 bg-amber-950/30 text-white"
                    : "border-white/10 text-zinc-300"
                }`}
              >
                {d >= 120 ? `${d / 60} мин` : `${d} сек`}
              </button>
            ))}
          </div>
        ) : null}

        {step === 4 ? (
          <div className="flex flex-wrap gap-2">
            {(manifest?.genres || []).map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => setGenre(g)}
                className={`rounded-lg border px-3 py-1.5 text-[11px] capitalize ${
                  genre === g
                    ? "border-amber-400/50 bg-amber-950/30 text-white"
                    : "border-white/10 text-zinc-300"
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        ) : null}

        {step === 5 ? (
          <p className="text-sm text-zinc-400">
            Стиль монтажа: TikTok / Reels / YouTube / медленный / динамичный / Premium — выбор
            сохранится в brief при генерации.
          </p>
        ) : null}

        {step === 6 ? (
          <div className="flex flex-wrap gap-2">
            {["male_calm", "male_business", "female_calm", "female_confident"].map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setVoice(v)}
                className={`rounded-lg border px-3 py-2 text-xs ${
                  voice === v
                    ? "border-amber-400/50 bg-amber-950/30 text-white"
                    : "border-white/10 text-zinc-300"
                }`}
              >
                {v.replace("_", " · ")}
              </button>
            ))}
          </div>
        ) : null}

        {step === 7 ? (
          <div className="flex flex-wrap gap-2">
            {["corporate", "luxury", "cinematic", "electronic", "emotional", "ambient", "none"].map(
              (m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMusic(m)}
                  className={`rounded-lg border px-3 py-2 text-xs capitalize ${
                    music === m
                      ? "border-amber-400/50 bg-amber-950/30 text-white"
                      : "border-white/10 text-zinc-300"
                  }`}
                >
                  {m}
                </button>
              ),
            )}
          </div>
        ) : null}

        {step === 8 ? (
          <p className="text-sm text-zinc-400">
            AI Mode / User Assets — загрузка фото, видео, логотипа появится после Orchestrator.
            Сейчас: структура brief only.
          </p>
        ) : null}

        {step === 9 ? (
          <p className="text-sm text-zinc-400">
            Брендинг Virtus Core по умолчанию (логотип, цвета, virtuscore.de, CTA). Клиентский
            брендинг — после открытия коммерческой услуги.
          </p>
        ) : null}

        {step === 10 ? (
          <div className="space-y-3">
            <label className="block text-xs text-zinc-400">
              Prompt Director — опишите ролик своими словами (последний шаг)
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={5}
              className="w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-sm text-white outline-none focus:border-amber-400/40"
              placeholder="Создай кинематографичный рекламный ролик 30 сек для стоматологии…"
            />
            <div className="flex flex-wrap gap-2">
              {(manifest?.quality_targets || []).map((q) => (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => setQuality(q.id)}
                  className={`rounded border px-2 py-1 text-[10px] ${
                    quality === q.id
                      ? "border-emerald-400/50 text-emerald-200"
                      : "border-white/10 text-zinc-400"
                  }`}
                >
                  Quality: {q.label}
                </button>
              ))}
            </div>
            <button
              type="button"
              disabled
              className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-500"
              title="Video generation disabled in Phase D"
            >
              Generate — Commercial Ready (скоро)
            </button>
            <p className="text-[11px] text-zinc-500">
              Brief: {selectedPlatform?.label} · {GOAL_LABELS[goal] || goal} · {duration}s ·{" "}
              {genre} · {voice} · {music} · {quality}
            </p>
          </div>
        ) : null}

        <div className="mt-4 flex justify-between">
          <button
            type="button"
            disabled={step <= 0}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            className="text-xs text-zinc-400 disabled:opacity-30"
          >
            ← Назад
          </button>
          <button
            type="button"
            disabled={step >= steps.length - 1}
            onClick={() => setStep((s) => Math.min(steps.length - 1, s + 1))}
            className="text-xs text-amber-200 disabled:opacity-30"
          >
            Далее →
          </button>
        </div>
      </section>

      {bible?.pipeline?.length ? (
        <section className="rounded-xl border border-dashed border-white/15 p-4">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            AI Director pipeline (planned)
          </h2>
          <p className="mt-2 font-mono text-[11px] text-zinc-400">
            {bible.pipeline.join(" → ")}
          </p>
          <p className="mt-2 text-[11px] text-zinc-500">
            Orchestrator engines:{" "}
            {(bible.orchestrator_engines_planned || []).join(", ") || "—"}
          </p>
        </section>
      ) : null}
    </div>
  );
}
