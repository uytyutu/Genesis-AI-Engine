"use client";

import Link from "next/link";
import { AnonCharacter } from "./AnonCharacter";
import { useI18n } from "./I18nProvider";

const MECHANICS: Array<{
  emoji: string;
  titleKey: string;
  blurbKey: string;
  status: "seed" | "coming";
  href?: string;
}> = [
  {
    emoji: "🕰️",
    titleKey: "dna.m.living.title",
    blurbKey: "dna.m.living.blurb",
    status: "seed",
    href: "/open-when",
  },
  {
    emoji: "🧩",
    titleKey: "dna.m.assemble.title",
    blurbKey: "dna.m.assemble.blurb",
    status: "coming",
  },
  {
    emoji: "👀",
    titleKey: "dna.m.know.title",
    blurbKey: "dna.m.know.blurb",
    status: "coming",
  },
  {
    emoji: "🎭",
    titleKey: "dna.m.director.title",
    blurbKey: "dna.m.director.blurb",
    status: "coming",
  },
  {
    emoji: "🪄",
    titleKey: "dna.m.spoiler.title",
    blurbKey: "dna.m.spoiler.blurb",
    status: "seed",
    href: "/drop",
  },
  {
    emoji: "🧠",
    titleKey: "dna.m.memory.title",
    blurbKey: "dna.m.memory.blurb",
    status: "coming",
  },
  {
    emoji: "🔀",
    titleKey: "dna.m.swap.title",
    blurbKey: "dna.m.swap.blurb",
    status: "coming",
  },
  {
    emoji: "🌎",
    titleKey: "dna.m.future.title",
    blurbKey: "dna.m.future.blurb",
    status: "seed",
    href: "/open-when",
  },
];

function StatusPill({ status }: { status: "seed" | "coming" }) {
  const { t } = useI18n();
  const label = status === "seed" ? t("dna.status.seed") : t("dna.status.coming");
  const cls =
    status === "seed" ? "bg-sky-500/15 text-sky-200" : "bg-white/10 text-white/55";
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] ${cls}`}
    >
      {label}
    </span>
  );
}

/**
 * Homepage: quiet future teaser — never the first product promise.
 * Live offers stay above this.
 */
export function DnaVisionHome() {
  const { t } = useI18n();

  return (
    <section className="mb-10 rounded-2xl border border-dashed border-white/15 bg-black/20 px-5 py-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-white/45">
            {t("dna.home.eyebrow")}
          </p>
          <p className="mt-1 text-sm font-medium text-white/85">{t("dna.home.line")}</p>
          <p className="mt-1 text-xs anon-muted">{t("dna.honest")}</p>
        </div>
        <Link href="/dna" className="anon-btn anon-btn-ghost shrink-0 text-xs">
          {t("dna.cta.explore")}
        </Link>
      </div>
    </section>
  );
}

/** Full DNA + mechanics page — clearly labeled Coming / Seed */
export function DnaVisionFull() {
  const { t } = useI18n();

  return (
    <main className="anim-in mx-auto max-w-lg space-y-8 pb-16 sm:max-w-3xl">
      <header className="relative overflow-hidden rounded-[2rem] border border-white/10 px-6 py-10 text-center sm:px-10">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(800px 400px at 50% 0%, rgba(168,120,230,0.45), transparent 55%), radial-gradient(600px 300px at 80% 80%, rgba(224,160,200,0.22), transparent 50%), #1a1230",
          }}
        />
        <div className="relative">
          <p className="inline-flex rounded-full bg-white/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/70">
            {t("dna.status.coming")}
          </p>
          <AnonCharacter size={88} mood="secret" accent="secret" className="mx-auto mt-4" />
          <p className="mt-4 text-[10px] font-semibold uppercase tracking-[0.4em] text-sky-300/80">
            {t("dna.eyebrow")}
          </p>
          <h1 className="mt-3 text-3xl font-semibold leading-tight sm:text-4xl">
            {t("dna.hero")}
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base text-white/70">{t("dna.heroSub")}</p>
          <p className="mx-auto mt-3 max-w-md text-sm italic text-fuchsia-200/80">
            «{t("dna.quote")}»
          </p>
          <p className="mx-auto mt-4 max-w-md text-xs text-amber-200/90">{t("dna.honest")}</p>
        </div>
      </header>

      <section className="anon-card space-y-3 p-5 text-center">
        <h2 className="font-semibold">{t("dna.liveNowTitle")}</h2>
        <p className="text-sm anon-muted">{t("dna.liveNowSub")}</p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:justify-center">
          <Link href="/secrets" className="anon-btn anon-btn-primary">
            {t("cta.getAnon")}
          </Link>
          <Link href="/drop" className="anon-btn anon-btn-ghost">
            {t("offer.drop.ctaFull")}
          </Link>
          <Link href="/open-when" className="anon-btn anon-btn-ghost">
            {t("dna.cta.livingSeed")}
          </Link>
        </div>
      </section>

      <section className="anon-card space-y-4 p-6">
        <h2 className="text-lg font-semibold">{t("dna.notTitle")}</h2>
        <p className="text-sm anon-muted">{t("dna.notSub")}</p>
        <ul className="grid gap-2 text-sm sm:grid-cols-2">
          {["dna.not.1", "dna.not.2", "dna.not.3", "dna.not.4"].map((k) => (
            <li key={k} className="rounded-xl bg-black/30 px-3 py-2 anon-muted">
              ✕ {t(k)}
            </li>
          ))}
        </ul>
        <p className="text-sm font-medium text-emerald-200/90">✓ {t("dna.yes")}</p>
      </section>

      <section className="anon-card space-y-3 p-6">
        <h2 className="text-lg font-semibold">{t("dna.strandsTitle")}</h2>
        <p className="text-sm anon-muted">{t("dna.strandsSub")}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {[
            "dna.strand.voice",
            "dna.strand.stories",
            "dna.strand.photos",
            "dna.strand.answers",
            "dna.strand.favorites",
            "dna.strand.memories",
            "dna.strand.advice",
            "dna.strand.secrets",
            "dna.strand.thoughts",
          ].map((k) => (
            <span
              key={k}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/60"
            >
              {t(k)}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-[0.22em] anon-muted">
          {t("dna.mechanicsTitle")}
        </h2>
        <p className="mt-1 text-sm anon-muted">{t("dna.mechanicsSub")}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {MECHANICS.map((m) => {
            const body = (
              <>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-2xl opacity-90">{m.emoji}</span>
                  <StatusPill status={m.status} />
                </div>
                <h3 className="mt-3 font-semibold">{t(m.titleKey)}</h3>
                <p className="mt-1.5 text-sm leading-relaxed anon-muted">{t(m.blurbKey)}</p>
                {m.status === "seed" && m.href && (
                  <p className="mt-3 text-xs text-sky-300">{t("dna.trySeed")}</p>
                )}
              </>
            );
            return m.href ? (
              <Link
                key={m.titleKey}
                href={m.href}
                className="anon-card block p-5 transition hover:border-white/20"
              >
                {body}
              </Link>
            ) : (
              <article key={m.titleKey} className="anon-card p-5 opacity-80">
                {body}
              </article>
            );
          })}
        </div>
      </section>

      <section className="rounded-[1.75rem] border border-white/10 bg-black/30 p-6 text-center sm:p-8">
        <p className="text-xs uppercase tracking-[0.3em] text-white/50">{t("dna.orbitTitle")}</p>
        <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-white/75">
          {t("dna.orbitSub")}
        </p>
        <Link href="/" className="anon-btn anon-btn-primary mt-6 inline-flex">
          {t("dna.cta.backLive")}
        </Link>
      </section>
    </main>
  );
}
