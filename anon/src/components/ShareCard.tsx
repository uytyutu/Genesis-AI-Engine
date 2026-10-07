"use client";

import { AnonCharacter } from "./AnonCharacter";
import { useI18n } from "./I18nProvider";

/** Visual share card for Stories / TikTok — character + intrigue copy. */
export function ShareCard({
  username,
  displayName,
}: {
  username: string;
  displayName?: string;
}) {
  const { t } = useI18n();
  return (
    <div className="relative overflow-hidden rounded-[1.75rem] border border-white/10 bg-gradient-to-br from-[#1a1228] via-[#2a1f45] to-[#120e1c] p-6 text-center shadow-[0_0_48px_rgba(184,160,224,0.28)]">
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-fuchsia-500/20 blur-2xl" />
      <div className="pointer-events-none absolute -bottom-10 -left-6 h-28 w-28 rounded-full bg-violet-500/25 blur-2xl" />
      <p className="text-[10px] font-bold tracking-[0.35em] text-violet-200">ANON</p>
      <div className="mx-auto mt-3 flex justify-center">
        <AnonCharacter size={96} mood="curious" accent="secret" pulse />
      </div>
      <p className="mx-auto mt-4 max-w-[16rem] text-base font-semibold leading-snug">
        {t("share.cardLine")}
      </p>
      <p className="mt-3 font-mono text-sm text-violet-200">@{username}</p>
      {displayName ? <p className="mt-1 text-xs anon-muted">{displayName}</p> : null}
      <p className="mt-5 inline-flex rounded-full bg-white/10 px-4 py-2 text-xs font-semibold text-white">
        {t("share.cardCta")}
      </p>
    </div>
  );
}
