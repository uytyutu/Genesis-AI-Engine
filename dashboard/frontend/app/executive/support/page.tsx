"use client";

import { useEffect, useState } from "react";
import OracleSupportDesk from "./OracleSupportDesk";

const ORACLE = process.env.NEXT_PUBLIC_ORACLE_URL || "http://127.0.0.1:4173";

type OracleUser = {
  virtusId?: string;
  name?: string;
  email?: string;
  lastSeen?: string;
  balance?: number;
  spent?: number;
  readings?: number;
};

export default function SupportPage() {
  const [users, setUsers] = useState<OracleUser[]>([]);

  useEffect(() => {
    const key = typeof window !== "undefined" ? sessionStorage.getItem("ORACLE_OWNER_KEY") : "";
    if (!key) return;
    void fetch(`${ORACLE}/oracle/owner`, { headers: { "x-oracle-owner": key } })
      .then((res) => res.json())
      .then((body) => setUsers(body.users || []))
      .catch(() => setUsers([]));
  }, []);

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8 text-zinc-100">
      <header>
        <p className="text-[11px] uppercase tracking-wide text-zinc-500">Communication</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Support</h1>
        <p className="mt-1 text-sm text-zinc-400">Входящие письма клиентов с подключённой почты. Пользователь не создаётся из письма.</p>
      </header>
      <OracleSupportDesk oracleUsers={users} />
    </main>
  );
}
