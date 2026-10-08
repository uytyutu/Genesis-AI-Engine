"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

const CHIPS = [
  "Viral",
  "Cinematic",
  "UGC",
  "Ad",
  "Story",
  "Product",
  "Creator",
  "Remix",
];

const TYPES = [
  ["🔥", "Viral Short"],
  ["📢", "Реклама"],
  ["👤", "AI Creator"],
  ["🛍", "Product Video"],
  ["🎙", "Podcast → Shorts"],
  ["🔗", "Link → Video"],
  ["📸", "Photo → Video"],
  ["🎵", "Music Video"],
  ["📖", "Story"],
  ["🎥", "Cinematic"],
  ["📱", "TikTok / Reels"],
];

const MODES = [
  ["VIRAL", "Hook, pacing, captions, CTA"],
  ["CINEMATIC", "Camera, depth, dramatic light"],
  ["UGC", "Как обычная съёмка человека"],
  ["LUXURY", "Премиальный рекламный стиль"],
  ["DARK", "Драматичный свет"],
  ["FUN", "Яркая динамика"],
  ["NEWS", "Headline → факт → вывод"],
  ["STORY", "Сюжет с развитием"],
  ["DOCUMENTARY", "Спокойный голос + атмосфера"],
];

export default function VieworaHomePage() {
  const router = useRouter();
  const [brief, setBrief] = useState("");

  function goCreate(preset?: string) {
    const q = new URLSearchParams();
    if (brief.trim()) q.set("brief", brief.trim());
    if (preset) q.set("chip", preset);
    router.push(`/viewora/create${q.toString() ? `?${q}` : ""}`);
  }

  return (
    <>
      <section className="viewora-hero">
        <div>
          <div className="viewora-kicker">Virtus Video AI · Professional Studio</div>
          <h1>CREATE SOMETHING THAT GETS WATCHED.</h1>
          <p className="viewora-hero-lead">
            Describe it. Upload it. Remix it.
            <br />
            We&apos;ll turn it into a real MP4 you can download.
          </p>
          <div className="viewora-prompt-row">
            <input
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="What do you want to create?"
              aria-label="What do you want to create?"
              onKeyDown={(e) => {
                if (e.key === "Enter") goCreate();
              }}
            />
            <button
              type="button"
              className="viewora-btn viewora-btn-primary"
              onClick={() => goCreate()}
            >
              ✨ CREATE
            </button>
          </div>
          <div className="viewora-chip-row">
            {CHIPS.map((c) => (
              <button
                key={c}
                type="button"
                className="viewora-chip"
                onClick={() => goCreate(c)}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
        <div className="viewora-phone" aria-hidden>
          <div className="viewora-phone-screen">
            <div className="viewora-phone-caption">Ты зря делаешь это каждый день…</div>
            <div className="viewora-phone-meta">WATCHABILITY 91 · HOOK 96 · VIRAL</div>
          </div>
        </div>
      </section>

      <section className="viewora-section" id="create-types">
        <h2>Что создаём?</h2>
        <p className="lead">
          Не заставляем собирать видео. Вы выбираете, каким оно должно быть — оркестратор
          сам подбирает pipeline.
        </p>
        <div className="viewora-grid">
          {TYPES.map(([emoji, label]) => (
            <button
              key={label}
              type="button"
              className="viewora-card"
              style={{ textAlign: "left", cursor: "pointer", width: "100%" }}
              onClick={() => goCreate(label)}
            >
              <h3>
                {emoji} {label}
              </h3>
              <p>Один клик → готовый пакет контента</p>
            </button>
          ))}
        </div>
      </section>

      <section className="viewora-section" id="features">
        <h2>Режимы — вау-часть</h2>
        <p className="lead">
          VIRAL строит удержание. CINEMATIC — киношную камеру. UGC — будто снял человек.
          AI сам предложит лучший режим кнопкой Make it Better.
        </p>
        <div className="viewora-grid">
          {MODES.map(([name, blurb]) => (
            <div key={name} className="viewora-card">
              <h3>{name}</h3>
              <p>{blurb}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="viewora-section">
        <h2>Почему платят</h2>
        <div className="viewora-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
          <div className="viewora-card">
            <h3>✨ Make it Better</h3>
            <p>AI сам выбирает mode + Visual DNA под ваш исходник.</p>
          </div>
          <div className="viewora-card">
            <h3>GENERATE 10</h3>
            <p>Десять версий одного ролика — сравните и выберите.</p>
          </div>
          <div className="viewora-card">
            <h3>HOOK LAB</h3>
            <p>20 hooks + тест первых секунд.</p>
          </div>
          <div className="viewora-card">
            <h3>WATCHABILITY</h3>
            <p>Hook · Pacing · Visual · Emotion · CTA — и Optimize.</p>
          </div>
          <div className="viewora-card">
            <h3>VIRAL LAB</h3>
            <p>Один ролик → A–H версии рядом. CREATE 10 VERSIONS.</p>
          </div>
          <div className="viewora-card">
            <h3>PRODUCT MODE</h3>
            <p>Фото товара → сцена → голос → CTA.</p>
          </div>
          <div className="viewora-card">
            <h3>CONTENT MACHINE</h3>
            <p>30 дней контента для TikTok магазина.</p>
          </div>
        </div>
        <div className="viewora-actions" style={{ marginTop: "1.5rem" }}>
          <Link href="/viewora/create" className="viewora-btn viewora-btn-primary">
            Открыть Studio
          </Link>
          <Link href="/viewora/pricing" className="viewora-btn viewora-btn-ghost">
            Цены от €12.99
          </Link>
        </div>
      </section>
    </>
  );
}
