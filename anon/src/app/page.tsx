"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AnonCharacter } from "@/components/AnonCharacter";
import { DnaVisionHome } from "@/components/DnaVision";
import { ProductOfferCard } from "@/components/ProductOfferCard";
import { useI18n } from "@/components/I18nProvider";

export default function HomePage() {
  const { t } = useI18n();
  const [loggedIn, setLoggedIn] = useState(false);
  const [unread, setUnread] = useState(0);
  const [sharePath, setSharePath] = useState<string | null>(null);
  const [demoOpen, setDemoOpen] = useState(false);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => {
        if (!r.ok) return null;
        setLoggedIn(true);
        return fetch("/api/profile").then((x) => x.json());
      })
      .then((d) => {
        if (!d?.profile) return;
        setSharePath(d.profile.sharePath);
        setUnread(d.profile.secretsReceived || 0);
      })
      .catch(() => null);
  }, []);

  return (
    <main>
      <section className="anim-in mb-8 pt-2 text-center sm:pt-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.35em] text-violet-300/90">
          ANON
        </p>
        <h1 className="mx-auto max-w-xl text-3xl font-semibold leading-tight sm:text-5xl">
          {t("brand.secretHero")}
        </h1>
        <p className="mx-auto mt-4 max-w-lg text-base anon-muted sm:text-lg">
          {t("brand.secretSub")}
        </p>
        <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
          <Link href="/loops" className="anon-btn anon-btn-primary text-base">
            ✨ {t("leave.homeCta")}
          </Link>
          <Link
            href={loggedIn ? "/secrets" : "/auth/register?next=/secrets"}
            className="anon-btn anon-btn-ghost text-base"
          >
            🔐 {t("cta.getAnon")}
          </Link>
          <Link
            href={loggedIn && sharePath ? sharePath : "/auth/register?next=/secrets"}
            className="anon-btn anon-btn-ghost text-base"
          >
            💌 {t("cta.sendSecret")}
          </Link>
        </div>
        <p className="mx-auto mt-4 max-w-md text-xs anon-muted">{t("home.freeFirst")}</p>
      </section>

      <section className="mx-auto mb-10 grid max-w-lg items-center gap-4 sm:grid-cols-[100px_1fr]">
        <div className="mx-auto">
          <AnonCharacter
            size={100}
            mood={demoOpen ? "surprised" : "secret"}
            accent="secret"
            pulse={!demoOpen}
          />
          <p className="mt-1 text-center text-[10px] tracking-[0.2em] text-violet-300/80">
            Veil
          </p>
          <p className="mt-1 text-center text-xs text-white/70">
            {demoOpen ? t("veil.heroOpen") : t("veil.heroWait")}
          </p>
        </div>
        <div className="overflow-hidden rounded-3xl border border-violet-300/20 bg-gradient-to-br from-[#3d2a68] via-[#2a1848] to-[#1a1230] p-5 text-center shadow-[0_0_60px_rgba(168,120,230,0.4)]">
          <p className="text-xs tracking-[0.3em] text-violet-200">
            🔐 {t("home.secretBadge")}
          </p>
          <h2 className="mt-3 text-xl font-semibold sm:text-2xl">{t("home.demoTitle")}</h2>
          <p className="mt-3 text-base text-white/80 italic">
            «{t("home.demoQuote")}»
          </p>
          {!demoOpen ? (
            <button
              type="button"
              className="anon-btn anon-btn-primary mt-5 w-full"
              onClick={() => setDemoOpen(true)}
            >
              {t("home.demoOpen")}
            </button>
          ) : (
            <div className="anim-in mt-5 space-y-2 rounded-2xl bg-[#2a1848]/70 p-4 text-left">
              <p className="text-sm leading-relaxed">{t("home.demoReveal")}</p>
              <p className="text-xs text-fuchsia-200">🕵️ {t("home.demoHidden")}</p>
            </div>
          )}
        </div>
      </section>

      {loggedIn && (
        <section className="mb-8 space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-[0.2em] anon-muted">
            {t("home.aroundYou")}
          </h2>
          <Link href="/secrets" className="anon-card flex items-center justify-between p-4">
            <span>🔐 {t("home.yourSecrets")}</span>
            <span className="text-violet-200">{unread}</span>
          </Link>
          {sharePath && (
            <div className="anon-card p-4 text-sm">
              <p className="anon-muted">{t("secrets.yourLink")}</p>
              <p className="mt-1 font-mono text-violet-200">
                {typeof window !== "undefined" ? window.location.origin : ""}
                {sharePath}
              </p>
            </div>
          )}
        </section>
      )}

      <section className="mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-[0.2em] anon-muted">
          {t("home.offersTitle")}
        </h2>
        <p className="mt-1 text-sm anon-muted">{t("home.offersSub")}</p>
      </section>

      <section className="mb-8 grid gap-4 sm:grid-cols-2">
        <ProductOfferCard
          emoji="🔐"
          titleKey="offer.anon.title"
          blurbKey="offer.anon.blurb"
          youGetKeys={["offer.anon.g1", "offer.anon.g2", "offer.anon.g3"]}
          forWhomKey="offer.anon.for"
          priceLabel={t("offer.free")}
          ctaHref={loggedIn ? "/secrets" : "/auth/register?next=/secrets"}
          ctaKey="offer.anon.cta"
          free
        />
        <ProductOfferCard
          emoji="💌"
          titleKey="offer.secret.title"
          blurbKey="offer.secret.blurb"
          youGetKeys={["offer.secret.g1", "offer.secret.g2", "offer.secret.g3"]}
          forWhomKey="offer.secret.for"
          recipientKeys={["offer.secret.r1", "offer.secret.r2", "offer.secret.r3"]}
          priceLabel={t("offer.free")}
          ctaHref={loggedIn && sharePath ? sharePath : "/secrets"}
          ctaKey="offer.secret.cta"
          free
        />
        <ProductOfferCard
          emoji="🔥"
          titleKey="offer.drop.title"
          blurbKey="offer.drop.blurb"
          youGetKeys={["offer.drop.g1", "offer.drop.g2", "offer.drop.g3"]}
          forWhomKey="offer.drop.for"
          recipientKeys={["offer.drop.r1", "offer.drop.r2", "offer.drop.r3", "offer.drop.r4"]}
          priceLabel="€1.99"
          ctaHref="/drop"
          ctaKey="offer.drop.ctaFull"
        />
        <ProductOfferCard
          emoji="⏳"
          titleKey="offer.openLater.title"
          blurbKey="offer.openLater.blurb"
          youGetKeys={["offer.openLater.g1", "offer.openLater.g2", "offer.openLater.g3"]}
          forWhomKey="offer.openLater.for"
          recipientKeys={["offer.openLater.r1", "offer.openLater.r2"]}
          priceLabel="€1.99"
          ctaHref="/open-when"
          ctaKey="offer.openLater.cta"
        />
        <ProductOfferCard
          emoji="💜"
          titleKey="offer.moment.title"
          blurbKey="offer.moment.blurb"
          youGetKeys={["offer.moment.g1", "offer.moment.g2", "offer.moment.g3"]}
          forWhomKey="offer.moment.for"
          priceLabel="€2.49+"
          ctaHref="/moments"
          ctaKey="offer.moment.cta"
        />
        <ProductOfferCard
          emoji="✨"
          titleKey="offer.plus.title"
          blurbKey="offer.plus.blurb"
          youGetKeys={["offer.plus.g1", "offer.plus.g2", "offer.plus.g3"]}
          forWhomKey="offer.plus.for"
          priceLabel="€4.99/mo"
          ctaHref="/plus"
          ctaKey="offer.plus.cta"
        />
      </section>

      <section className="anon-card mb-8 p-5 text-center">
        <AnonCharacter size={64} mood="curious" className="mx-auto" />
        <h2 className="mt-2 font-semibold">{t("home.loopTitle")}</h2>
        <p className="mx-auto mt-2 max-w-md text-sm anon-muted">{t("home.loopSub")}</p>
        <ol className="mx-auto mt-4 max-w-sm space-y-2 text-left text-sm anon-muted">
          <li>1. {t("home.loop.1")}</li>
          <li>2. {t("home.loop.2")}</li>
          <li>3. {t("home.loop.3")}</li>
          <li>4. {t("home.loop.4")}</li>
          <li>5. {t("home.loop.5")}</li>
        </ol>
        <Link
          href={loggedIn ? "/settings" : "/auth/register?next=/settings"}
          className="anon-btn anon-btn-primary mt-5 inline-flex"
        >
          {t("cta.getAnon")}
        </Link>
      </section>

      <section className="mb-8 text-center">
        <Link href="/games" className="anon-card inline-flex flex-col items-center gap-1 px-8 py-5">
          <AnonCharacter size={48} mood="happy" accent="games" showGlow={false} />
          <span className="font-semibold">{t("home.card.games")}</span>
          <span className="text-sm anon-muted">{t("home.card.games.desc")}</span>
        </Link>
      </section>

      {/* Future vision — after Live product, never the first promise */}
      <DnaVisionHome />
    </main>
  );
}
