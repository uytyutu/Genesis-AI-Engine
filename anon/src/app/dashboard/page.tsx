"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useI18n } from "@/components/I18nProvider";
import { translateGiftType, translateStatus } from "@/lib/i18n/dictionaries";

type GiftLite = {
  id: string;
  token: string;
  type: string;
  status: string;
  anonymous: number;
  opened_at: string | null;
  created_at: string;
  recipient_label: string | null;
};

export default function DashboardPage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [name, setName] = useState("");
  const [sent, setSent] = useState<GiftLite[]>([]);
  const [received, setReceived] = useState<GiftLite[]>([]);
  const [notifs, setNotifs] = useState<
    { id: string; title: string; body: string; href: string | null }[]
  >([]);

  useEffect(() => {
    (async () => {
      const me = await fetch("/api/auth/me");
      if (!me.ok) {
        router.replace("/auth/login?next=/dashboard");
        return;
      }
      const u = await me.json();
      setName(u.user.displayName);
      const g = await fetch("/api/gifts").then((r) => r.json());
      setSent(g.sent || []);
      setReceived(g.received || []);
      const n = await fetch("/api/notifications").then((r) => r.json());
      setNotifs(n.items || []);
    })();
  }, [router]);

  const anonCount = sent.filter((g) => g.anonymous).length;

  return (
    <main className="anim-in space-y-6">
      <section>
        <p className="text-xs uppercase tracking-[0.25em] text-violet-300">ANON</p>
        <h1 className="mt-2 text-2xl font-semibold">
          {name ? `${name}, ` : ""}
          {t("dash.hello")}
        </h1>
      </section>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: t("dash.sent"), value: sent.length, emoji: "💌" },
          { label: t("dash.received"), value: received.length, emoji: "🎁" },
          { label: t("dash.anon"), value: anonCount, emoji: "🕵️" },
          {
            label: t("dash.hearts"),
            value: sent.filter((g) => g.type.includes("MOMENT")).length,
            emoji: "❤️",
          },
        ].map((s) => (
          <div key={s.label} className="anon-card p-4">
            <div className="text-xl">{s.emoji}</div>
            <div className="mt-2 text-2xl font-semibold">{s.value}</div>
            <div className="text-xs anon-muted">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <Link href="/play" className="anon-btn anon-btn-primary">
          🎮 {t("nav.play")}
        </Link>
        <Link href="/create" className="anon-btn anon-btn-ghost">
          💌 {t("cta.sendMoment")}
        </Link>
        <Link href="/inbox" className="anon-btn anon-btn-ghost">
          🎁 {t("nav.inbox")}
        </Link>
        <Link href="/settings" className="anon-btn anon-btn-ghost">
          ⚙️
        </Link>
      </div>

      <section className="anon-card p-5">
        <h2 className="font-semibold">{t("dash.sentList")}</h2>
        <div className="mt-3 space-y-2">
          {sent.length === 0 && <p className="text-sm anon-muted">{t("anon.empty")}</p>}
          {sent.map((g) => (
            <div
              key={g.id}
              className="flex items-center justify-between rounded-xl bg-black/20 px-3 py-2 text-sm"
            >
              <span>
                {translateGiftType(locale, g.type)} · {translateStatus(locale, g.status)}
                {g.anonymous ? " · 🕵️" : ""}
              </span>
              {["paid", "sent", "opened", "replied"].includes(g.status) && (
                <Link className="text-sky-300 underline" href={`/open/${g.token}`}>
                  {t("cta.open")}
                </Link>
              )}
              {g.anonymous && g.status !== "awaiting_payment" && (
                <RevealButton giftId={g.id} />
              )}
            </div>
          ))}
        </div>
      </section>

      {notifs.length > 0 && (
        <section className="anon-card p-5">
          <h2 className="font-semibold">{t("dash.notifications")}</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {notifs.slice(0, 8).map((n) => (
              <li key={n.id}>
                <strong>{n.title}</strong>
                <span className="anon-muted"> — {n.body}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}

function RevealButton({ giftId }: { giftId: string }) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);
  async function reveal() {
    setBusy(true);
    await fetch(`/api/anonymous/${giftId}/reveal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "consent" }),
    });
    const r = await fetch(`/api/anonymous/${giftId}/reveal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "checkout" }),
    });
    const d = await r.json();
    setBusy(false);
    if (d.url) window.location.href = d.url;
    else if (d.revealed || d.alreadyRevealed) window.location.reload();
    else alert(d.error || t("reveal.consentNeed"));
  }
  return (
    <button
      type="button"
      disabled={busy}
      onClick={reveal}
      className="ml-2 text-xs text-fuchsia-300 underline"
    >
      {t("reveal.moment")}
    </button>
  );
}
