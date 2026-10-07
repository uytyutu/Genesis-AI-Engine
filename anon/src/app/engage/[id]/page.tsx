"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AnonSpeak } from "@/components/AnonSpeak";
import { useI18n } from "@/components/I18nProvider";

type EngageView = {
  giftId: string;
  token: string;
  role: "sender" | "recipient";
  engage: {
    hintRequest: string;
    revealRequest: string;
    senderHint: string | null;
  };
};

export default function EngageSenderPage() {
  const { t } = useI18n();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<EngageView | null>(null);
  const [hint, setHint] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState("");

  async function load() {
    const r = await fetch(`/api/gifts/${id}/engage`);
    const d = await r.json();
    if (r.status === 401) {
      router.replace(`/auth/login?next=/engage/${id}`);
      return;
    }
    if (!r.ok) {
      setError(d.error || t("error.generic"));
      return;
    }
    setData(d);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function act(action: string, message?: string) {
    setBusy(true);
    setError("");
    const r = await fetch(`/api/gifts/${id}/engage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, message }),
    });
    const d = await r.json();
    setBusy(false);
    if (!r.ok) {
      setError(d.error || t("error.generic"));
      return;
    }
    setDone(action);
    await load();
  }

  if (error && !data) {
    return (
      <main className="anon-card mx-auto mt-16 max-w-md p-6 text-center">
        <p>{error}</p>
        <Link href="/secrets" className="anon-btn anon-btn-primary mt-4 inline-flex">
          {t("nav.secrets")}
        </Link>
      </main>
    );
  }

  if (!data) {
    return <main className="p-8 text-center anim-pulse">{t("loading.pack")}</main>;
  }

  if (data.role !== "sender") {
    return (
      <main className="anon-card mx-auto mt-16 max-w-md space-y-4 p-6 text-center">
        <p className="font-semibold">{t("engage.recipientRedirect")}</p>
        <Link href={`/open/${data.token}`} className="anon-btn anon-btn-primary w-full">
          {t("cta.open")}
        </Link>
      </main>
    );
  }

  const hintPending = data.engage.hintRequest === "pending";
  const revealPending = data.engage.revealRequest === "pending";

  return (
    <main className="anim-in mx-auto max-w-md space-y-5">
      <section>
        <p className="text-xs tracking-[0.3em] text-violet-300">ANON</p>
        <h1 className="mt-2 text-2xl font-semibold">{t("engage.title")}</h1>
        <p className="mt-1 text-sm anon-muted">{t("engage.sub")}</p>
      </section>

      <section className="anon-card p-4">
        <AnonSpeak lineKey="veil.reveal" mood="curious" size={64} />
      </section>

      {!hintPending && !revealPending && (
        <section className="anon-card p-5 text-sm anon-muted">
          {done ? t("engage.done") : t("engage.quiet")}
          <Link href="/dashboard" className="mt-4 anon-btn anon-btn-ghost w-full">
            {t("nav.cabinet")}
          </Link>
        </section>
      )}

      {hintPending && (
        <section className="anon-card space-y-3 p-5">
          <h2 className="font-semibold">💡 {t("engage.hintAsk")}</h2>
          <p className="text-sm anon-muted">{t("engage.hintAskSub")}</p>
          <textarea
            className="anon-input min-h-24"
            value={hint}
            onChange={(e) => setHint(e.target.value)}
            placeholder={t("engage.hintPh")}
            maxLength={200}
          />
          <button
            type="button"
            disabled={busy}
            className="anon-btn anon-btn-primary w-full"
            onClick={() => act("send_hint", hint)}
          >
            {t("engage.sendHint")}
          </button>
          <button
            type="button"
            disabled={busy}
            className="anon-btn anon-btn-ghost w-full"
            onClick={() => act("decline_hint")}
          >
            {t("engage.stayAnon")}
          </button>
        </section>
      )}

      {revealPending && (
        <section className="anon-card space-y-3 p-5">
          <h2 className="font-semibold">👀 {t("engage.revealAsk")}</h2>
          <p className="text-sm anon-muted">{t("engage.revealAskSub")}</p>
          <button
            type="button"
            disabled={busy}
            className="anon-btn anon-btn-primary w-full"
            onClick={() => act("consent_reveal")}
          >
            {t("engage.agreeReveal")}
          </button>
          <button
            type="button"
            disabled={busy}
            className="anon-btn anon-btn-ghost w-full"
            onClick={() => act("decline_reveal")}
          >
            {t("engage.stayAnon")}
          </button>
          <p className="text-xs anon-muted">{t("engage.revealNote")}</p>
        </section>
      )}

      {error && <p className="text-sm text-rose-300">{error}</p>}

      <Link href={`/open/${data.token}`} className="block text-center text-sm underline anon-muted">
        {t("engage.viewMessage")}
      </Link>
    </main>
  );
}
