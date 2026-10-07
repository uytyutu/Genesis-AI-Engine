"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AnonMark } from "@/components/AnonCharacter";
import { AnonSpeak } from "@/components/AnonSpeak";
import { useI18n } from "@/components/I18nProvider";
import { THEME_TOKENS, type ThemeId } from "@/lib/themes";

type Profile = {
  username: string;
  displayName: string;
  bio: string;
  theme: string;
  allowAnon: boolean;
  secretsReceived: number;
};

const KINDS = [
  "secret",
  "confession",
  "admirer",
  "question",
  "compliment",
  "mystery",
] as const;

export default function PublicProfilePage() {
  const { t } = useI18n();
  const { username } = useParams<{ username: string }>();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [clue, setClue] = useState("");
  const [kind, setKind] = useState<(typeof KINDS)[number]>("secret");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch(`/api/profile/${encodeURIComponent(username)}`)
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || "fail");
        setProfile(d.profile);
      })
      .catch((e) => setError(e.message || t("error.generic")));
  }, [username, t]);

  const themeKey = (profile?.theme || "secret") as ThemeId;
  const theme = THEME_TOKENS[themeKey] || THEME_TOKENS.secret;

  async function sendSecret() {
    if (!message.trim()) {
      setError(t("secret.needMessage"));
      return;
    }
    setBusy(true);
    setError("");
    const r = await fetch(`/api/profile/${encodeURIComponent(username)}/secret`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        kind,
        clue: clue || undefined,
        theme: profile?.theme || "secret",
      }),
    });
    const d = await r.json();
    setBusy(false);
    if (!r.ok) {
      setError(d.error || t("error.generic"));
      return;
    }
    setSent(true);
    setMessage("");
  }

  function share() {
    const url =
      typeof window !== "undefined"
        ? `${window.location.origin}/u/${username}`
        : `/u/${username}`;
    const text = t("secret.shareText", { name: profile?.displayName || username });
    if (navigator.share) {
      navigator.share({ title: "ANON", text, url }).catch(() => null);
    } else {
      navigator.clipboard.writeText(`${text}\n${url}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }

  if (error && !profile) {
    return (
      <main className="anon-card mx-auto mt-16 max-w-md p-8 text-center">
        <p>{error}</p>
        <Link href="/" className="anon-btn anon-btn-primary mt-4 inline-flex">
          ANON
        </Link>
      </main>
    );
  }

  if (!profile) {
    return <main className="p-8 text-center anim-pulse">{t("secret.loading")}</main>;
  }

  return (
    <main className="anim-in mx-auto max-w-lg space-y-5">
      <section
        className={`rounded-3xl border border-white/10 bg-gradient-to-br p-6 text-center ${theme.gradient}`}
        style={{ boxShadow: `0 0 50px ${theme.glow}` }}
      >
        <div className="mx-auto flex justify-center">
          <AnonMark size={56} />
        </div>
        <h1 className="mt-4 text-2xl font-semibold">{profile.displayName}</h1>
        <p className="text-sm" style={{ color: theme.accent }}>
          @{profile.username}
        </p>
        {profile.bio && <p className="mt-3 text-sm text-white/75">{profile.bio}</p>}
        <p className="mt-4 text-xs anon-muted">
          🔐 {t("secret.receivedCount", { n: profile.secretsReceived })}
        </p>
        <button type="button" className="anon-btn anon-btn-ghost mt-4" onClick={share}>
          🔗 {copied ? t("room.copied") : t("secret.shareProfile")}
        </button>
      </section>

      {!profile.allowAnon ? (
        <section className="anon-card p-5 text-center text-sm anon-muted">
          {t("secret.closed")}
        </section>
      ) : sent ? (
        <section className="anon-card space-y-3 p-6 text-center">
          <AnonSpeak lineKey="veil.sent" mood="happy" align="center" size={72} />
          <h2 className="text-xl font-semibold">{t("secret.sentTitle")}</h2>
          <p className="text-sm anon-muted">{t("secret.sentSub")}</p>
          <Link href="/auth/register" className="anon-btn anon-btn-primary w-full">
            {t("secret.getYourAnon")}
          </Link>
          <button type="button" className="anon-btn anon-btn-ghost w-full" onClick={() => setSent(false)}>
            {t("secret.sendAnother")}
          </button>
        </section>
      ) : (
        <section className="anon-card space-y-4 p-5">
          <AnonSpeak lineKey="veil.write" mood="curious" size={56} />
          <h2 className="text-lg font-semibold">💌 {t("secret.writeTitle")}</h2>
          <p className="text-sm anon-muted">{t("secret.writeSub")}</p>
          <div className="flex flex-wrap gap-2">
            {KINDS.map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setKind(k)}
                className={`rounded-full px-3 py-1 text-xs ${
                  kind === k ? "bg-violet-500/30 text-violet-100" : "bg-white/5 anon-muted"
                }`}
              >
                {t(`secret.kind.${k}`)}
              </button>
            ))}
          </div>
          <textarea
            className="anon-input min-h-28"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={t("secret.messagePh")}
          />
          <input
            className="anon-input"
            value={clue}
            onChange={(e) => setClue(e.target.value)}
            placeholder={t("secret.cluePh")}
          />
          <p className="text-xs anon-muted">{t("secret.clueHint")}</p>
          {error && <p className="text-sm text-rose-300">{error}</p>}
          <button
            type="button"
            disabled={busy}
            onClick={sendSecret}
            className="anon-btn anon-btn-primary w-full disabled:opacity-50"
          >
            {busy ? "…" : t("secret.sendCta")}
          </button>
        </section>
      )}
    </main>
  );
}
