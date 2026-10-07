"use client";

import Link from "next/link";
import { AnonSpeak } from "@/components/AnonSpeak";
import { useI18n } from "@/components/I18nProvider";

const PRESETS = [
  { emoji: "❤️", key: "miss" },
  { emoji: "🥺", key: "sad" },
  { emoji: "😂", key: "laugh" },
  { emoji: "🌙", key: "sleep" },
  { emoji: "🎂", key: "bday" },
  { emoji: "🤝", key: "fight" },
  { emoji: "🔥", key: "motivation" },
  { emoji: "💭", key: "remember" },
] as const;

const PRESET_LABEL: Record<(typeof PRESETS)[number]["key"], string> = {
  miss: "openWhen.p.miss",
  sad: "openWhen.p.sad",
  laugh: "openWhen.p.laugh",
  sleep: "openWhen.p.sleep",
  bday: "openWhen.p.bday",
  fight: "openWhen.p.fight",
  motivation: "openWhen.p.motivation",
  remember: "openWhen.p.remember",
};

export default function OpenWhenPage() {
  const { t } = useI18n();
  return (
    <main className="anim-in space-y-5">
      <div>
        <h1 className="text-3xl font-semibold">🔒 {t("openWhen.title")}</h1>
        <p className="mt-2 max-w-lg anon-muted">{t("openWhen.sub")}</p>
      </div>
      <section className="anon-card p-4">
        <AnonSpeak lineKey="veil.later" mood="waiting" accent="later" size={72} />
      </section>
      <div className="grid gap-3 sm:grid-cols-2">
        {PRESETS.map((p) => (
          <Link
            key={p.key}
            href={`/create?pillar=open_when&preset=${encodeURIComponent(t(PRESET_LABEL[p.key]))}`}
            className="anon-card flex items-center gap-3 p-4 transition hover:border-white/20"
          >
            <span className="text-2xl">{p.emoji}</span>
            <span className="text-sm font-medium">{t(PRESET_LABEL[p.key])}</span>
          </Link>
        ))}
      </div>
      <Link href="/create?pillar=open_when" className="anon-btn anon-btn-primary mt-8">
        {t("openWhen.create")}
      </Link>
    </main>
  );
}
