"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type PendingReview = {
  review_id: string;
  order_id: string;
  stars: number;
  text: string;
  status: string;
  flags: string[];
  company_display_name?: string | null;
  created_at?: string | null;
};

export default function CeoReviewsPage() {
  const [pending, setPending] = useState<PendingReview[]>([]);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/reviews/pending`);
      if (res.ok) {
        const body = await res.json();
        setPending(Array.isArray(body.pending) ? body.pending : []);
      }
    } catch {
      setPending([]);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function moderate(reviewId: string, action: "publish" | "reject") {
    setBusy(reviewId + action);
    setMsg("");
    try {
      const res = await fetch(`${API}/api/owner/reviews/${reviewId}/moderate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMsg(body?.detail || "Ошибка модерации");
        return;
      }
      setMsg(action === "publish" ? "Опубликовано на /site" : "Отклонено");
      await refresh();
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-3xl space-y-6 px-4 pt-6">
        <header className="rounded-2xl border border-amber-500/25 bg-gradient-to-br from-amber-950/30 via-genesis-panel to-genesis-bg p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-amber-300/80">{BRAND_NAME}</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">Отзывы · модерация</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Клиент отправляет после Delivered → Pending → вы публикуете или отклоняете. Без фейковых оценок.
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-xs">
            <Link href="/site" className="text-emerald-300 hover:underline">
              /site (публичные)
            </Link>
            <Link href="/products" className="text-emerald-300 hover:underline">
              Factory / продукты
            </Link>
          </div>
        </header>

        {msg && (
          <p className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm text-white/80">
            {msg}
          </p>
        )}

        {pending.length === 0 ? (
          <p className="text-sm text-genesis-muted">Нет отзывов на проверке.</p>
        ) : (
          <ul className="space-y-4">
            {pending.map((r) => (
              <li
                key={r.review_id}
                className="rounded-2xl border border-white/10 bg-genesis-panel p-5"
              >
                <p className="text-amber-300">{"★".repeat(Math.max(1, Math.min(5, r.stars)))}</p>
                <p className="mt-1 text-xs font-medium text-emerald-300/90">✔ Проверенный заказ</p>
                <p className="mt-2 text-sm text-white/90">«{r.text}»</p>
                {r.company_display_name && (
                  <p className="mt-2 text-xs font-medium text-white/60">{r.company_display_name}</p>
                )}
                <p className="mt-2 text-[10px] text-white/40">
                  {r.review_id} · заказ {r.order_id}
                  {r.flags?.length ? ` · флаги: ${r.flags.join(", ")}` : ""}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={Boolean(busy)}
                    onClick={() => void moderate(r.review_id, "publish")}
                    className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
                  >
                    {busy === r.review_id + "publish" ? "…" : "Опубликовать"}
                  </button>
                  <button
                    type="button"
                    disabled={Boolean(busy)}
                    onClick={() => void moderate(r.review_id, "reject")}
                    className="rounded-xl border border-rose-500/40 px-4 py-2 text-sm text-rose-200 hover:bg-rose-950/40 disabled:opacity-50"
                  >
                    {busy === r.review_id + "reject" ? "…" : "Отклонить"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
