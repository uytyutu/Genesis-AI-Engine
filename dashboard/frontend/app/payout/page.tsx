"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  PayoutManagerPanel,
  type PayoutManagerData,
} from "../components/PayoutManagerPanel";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function PayoutPage() {
  const [data, setData] = useState<PayoutManagerData | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/farm/payout-manager`);
      if (!res.ok) throw new Error("payout");
      setData(await res.json());
      setError("");
    } catch {
      setError("Backend недоступен — запустите Genesis.exe");
      setData(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 15_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  return (
    <main className="mx-auto max-w-3xl space-y-5 px-4 py-8">
      <header className="text-center">
        <p className="text-xs uppercase tracking-widest text-genesis-muted">CEO · Farm</p>
        <h1 className="mt-2 text-2xl font-bold text-white">Вывод · Payout Manager</h1>
        <p className="mt-2 text-sm text-genesis-muted">
          Где лежат REAL-деньги и официальные способы выплаты по каждому Earn-источнику.
        </p>
        <div className="mt-3 flex flex-wrap justify-center gap-2 text-xs">
          <Link href="/" className="rounded-lg border border-white/15 px-3 py-1.5 hover:bg-white/5">
            Ферма
          </Link>
          <Link
            href="/finance"
            className="rounded-lg border border-white/15 px-3 py-1.5 hover:bg-white/5"
          >
            Финансы
          </Link>
          <Link
            href="/revenue"
            className="rounded-lg border border-white/15 px-3 py-1.5 hover:bg-white/5"
          >
            Доход
          </Link>
        </div>
      </header>

      {error ? (
        <p className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-sm text-amber-100">
          {error}
        </p>
      ) : null}

      <PayoutManagerPanel data={data} onWithdrawDone={() => void refresh()} />
    </main>
  );
}
