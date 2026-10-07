"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useI18n } from "@/components/I18nProvider";
import { translateGiftType, translateStatus } from "@/lib/i18n/dictionaries";

export default function InboxPage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [items, setItems] = useState<
    { id: string; token: string; type: string; status: string; anonymous: number; created_at: string }[]
  >([]);

  useEffect(() => {
    (async () => {
      const me = await fetch("/api/auth/me");
      if (!me.ok) {
        router.replace("/auth/login?next=/inbox");
        return;
      }
      const g = await fetch("/api/gifts").then((r) => r.json());
      setItems(g.received || []);
    })();
  }, [router]);

  return (
    <main className="anim-in">
      <h1 className="text-2xl font-semibold">🎁 {t("inbox.title")}</h1>
      <div className="mt-6 space-y-3">
        {items.length === 0 && (
          <div className="anon-card p-6 text-center">
            <p>💌</p>
            <p className="mt-3">{t("inbox.empty")}</p>
          </div>
        )}
        {items.map((g) => (
          <Link
            key={g.id}
            href={`/open/${g.token}`}
            className="anon-card flex items-center justify-between p-4"
          >
            <span>
              {translateGiftType(locale, g.type)}
              {g.anonymous ? ` · 🕵️ ${t("product.anon")}` : ""}
            </span>
            <span className="text-xs anon-muted">{translateStatus(locale, g.status)}</span>
          </Link>
        ))}
      </div>
    </main>
  );
}
