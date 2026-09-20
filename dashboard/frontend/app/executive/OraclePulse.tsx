"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const ORACLE = process.env.NEXT_PUBLIC_ORACLE_URL || "http://127.0.0.1:4173";

type Pulse = {
  registrations?: number;
  visitors?: number;
  oracleReadings?: number;
  virtGifted?: number;
  activeUsers?: number;
};

export default function OraclePulse() {
  const [today, setToday] = useState<Pulse | null>(null);
  const [note, setNote] = useState("");

  useEffect(() => {
    const key = sessionStorage.getItem("ORACLE_OWNER_KEY") || "";
    if (!key) {
      setNote("Открой пульт и введи owner key — цифры подтянутся с :4173.");
      return;
    }
    fetch(`${ORACLE}/oracle/owner`, { headers: { "x-oracle-owner": key } })
      .then((res) => res.json())
      .then((body) => {
        if (body.error) {
          setNote(body.error === "OWNER_REQUIRED" ? "Ключ не принят." : body.error);
          return;
        }
        setToday(body.dashboard?.today || {});
      })
      .catch(() => setNote("Oracle недоступен на :4173."));
  }, []);

  return (
    <section className="rounded-xl border border-amber-400/25 bg-amber-950/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-wide text-amber-200/70">Virtus Oracle · owner only</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Эфир Oracle</h2>
          <p className="mt-1 text-xs text-zinc-400">Живые цифры с Oracle backend. Не витрина /site.</p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <Link href="/executive/oracle" className="rounded-lg border border-amber-400/40 px-3 py-1.5 text-amber-100">
            Обзор
          </Link>
          <Link href="/executive/oracle/users" className="rounded-lg border border-white/15 px-3 py-1.5">
            Пользователи
          </Link>
          <Link href="/executive/oracle/wallet" className="rounded-lg border border-white/15 px-3 py-1.5">
            Начислить
          </Link>
        </div>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-5">
        {[
          ["Регистрации", today?.registrations],
          ["Посещения", today?.visitors],
          ["Чтения", today?.oracleReadings],
          ["Выдано", today?.virtGifted],
          ["Активные", today?.activeUsers],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-lg border border-white/10 bg-black/20 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</p>
            <p className="mt-1 text-lg text-white">{value ?? "—"}</p>
          </div>
        ))}
      </div>
      {note ? <p className="mt-2 text-xs text-amber-100/80">{note}</p> : null}
    </section>
  );
}
