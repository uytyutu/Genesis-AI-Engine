"use client";

import { useEffect, useRef, useState } from "react";
import { BRAND_NAME } from "./lib/publicBrand";
import { fetchApi } from "./lib/fetchApi";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Segment error UI — remounts the *current* route only.
 * Never navigates to home (/) so CEO/buyer keep their place in the app.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [seconds, setSeconds] = useState(5);
  const resetRef = useRef(reset);
  resetRef.current = reset;

  useEffect(() => {
    console.error(error);
  }, [error]);

  useEffect(() => {
    let cancelled = false;
    let countdown = 5;

    const countdownId = window.setInterval(() => {
      countdown -= 1;
      if (countdown <= 0) countdown = 5;
      if (!cancelled) setSeconds(countdown);
    }, 1_000);

    const retryId = window.setInterval(() => {
      void (async () => {
        try {
          const res = await fetchApi(`${API}/api/status`, { timeoutMs: 2_500 });
          if (cancelled) return;
          if (res.ok) {
            resetRef.current();
            return;
          }
        } catch {
          /* still down */
        }
        // Remount this segment in place — do not router.push("/")
        if (!cancelled) resetRef.current();
      })();
    }, 5_000);

    return () => {
      cancelled = true;
      window.clearInterval(countdownId);
      window.clearInterval(retryId);
    };
  }, [error]);

  return (
    <div className="mx-auto flex min-h-[40vh] max-w-lg flex-col items-center justify-center px-6 py-16 text-center">
      <p className="text-xs uppercase tracking-[0.2em] text-amber-300/80">Связь</p>
      <h1 className="mt-2 text-xl font-semibold text-white">Переподключаю этот экран…</h1>
      <p className="mt-3 text-sm leading-relaxed text-genesis-muted">
        Остаётесь на той же странице — {BRAND_NAME} обновит её в фоне через ~{seconds} с. Браузер и
        другие вкладки трогать не нужно.
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-8 inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-genesis-accent to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-glow"
      >
        Повторить сейчас
      </button>
      <p className="mt-6 text-[11px] text-genesis-muted/70">
        Если минута без ответа: Genesis.exe → Остановить → Запустить (после этого экран сам
        поднимется здесь).
      </p>
    </div>
  );
}
