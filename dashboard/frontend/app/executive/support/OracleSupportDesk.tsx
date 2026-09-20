"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

type OracleUser = {
  virtusId?: string;
  name?: string;
  email?: string;
  lastSeen?: string;
  balance?: number;
  spent?: number;
  readings?: number;
};

type SupportMessage = {
  id?: string;
  direction?: string;
  from?: string;
  text?: string;
  subject?: string;
  created_at?: string;
};

type SupportThread = {
  id: string;
  from: string;
  subject: string;
  status: string;
  ui_status?: string;
  updated_at?: string;
  created_at?: string;
  messages?: SupportMessage[];
};

const STATUSES = ["NEW", "OPEN", "WAITING", "REPLIED", "CLOSED"] as const;

function senderEmail(from: string) {
  const match = String(from || "").match(/<([^>]+)>/);
  return (match?.[1] || from || "").trim().toLowerCase();
}

function stamp(value?: string) {
  return (value || "").slice(0, 16).replace("T", " ") || "—";
}

export default function OracleSupportDesk({ oracleUsers = [] }: { oracleUsers?: OracleUser[] }) {
  const [threads, setThreads] = useState<SupportThread[]>([]);
  const [filter, setFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const res = await fetch(`${API}/api/support/threads`);
      if (!res.ok) {
        setError("Почтовый inbox недоступен. Нужен backend :8000 с подключённой почтой.");
        setThreads([]);
        return;
      }
      const body = await res.json();
      setThreads(body.items || []);
    } catch {
      setError("Нет связи с API поддержки. Сообщения не подставляются из демо.");
      setThreads([]);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const selected = useMemo(() => threads.find((row) => row.id === selectedId) || null, [threads, selectedId]);

  const linked = useMemo(() => {
    if (!selected) return null;
    const email = senderEmail(selected.from);
    return oracleUsers.find((user) => (user.email || "").trim().toLowerCase() === email) || null;
  }, [oracleUsers, selected]);

  const openThread = async (thread: SupportThread) => {
    setSelectedId(thread.id);
    setReply("");
    setNote("");
    if (thread.ui_status === "NEW") {
      try {
        await fetch(`${API}/api/support/threads/${thread.id}/status`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ status: "OPEN" }),
        });
        void load();
      } catch {
        /* keep the letter visible even if status write fails */
      }
    }
  };

  const setStatus = async (status: string) => {
    if (!selected) return;
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/support/threads/${selected.id}/status`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        setNote("Не удалось изменить статус.");
        return;
      }
      setNote("Статус обновлён.");
      void load();
    } finally {
      setBusy(false);
    }
  };

  const sendReply = async () => {
    if (!selected || reply.trim().length < 2) return;
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/support/threads/${selected.id}/reply`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: reply, save_as_template: false, create_auto_rule: false }),
      });
      const body = await res.json();
      if (!res.ok || body.ok === false) {
        setNote(body.detail || "Ответ не отправлен. Проверь почтовый connector.");
        return;
      }
      setReply("");
      setNote(body.thread?.status === "waiting" ? "Ответ отправлен через подключённую почту." : "Письмо сохранено, но отправка не подтверждена.");
      void load();
    } finally {
      setBusy(false);
    }
  };

  const visible = threads.filter((row) => !filter || row.ui_status === filter || row.status === filter);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap gap-2 text-xs">
        <button type="button" onClick={() => setFilter("")} className={`rounded-lg border px-3 py-1.5 ${!filter ? "border-amber-400/50 text-amber-100" : "border-white/15 text-zinc-400"}`}>
          Все
        </button>
        {STATUSES.map((status) => (
          <button
            key={status}
            type="button"
            onClick={() => setFilter(status)}
            className={`rounded-lg border px-3 py-1.5 ${filter === status ? "border-amber-400/50 text-amber-100" : "border-white/15 text-zinc-400"}`}
          >
            {status}
          </button>
        ))}
        <button type="button" onClick={() => void load()} className="rounded-lg border border-white/15 px-3 py-1.5 text-zinc-400">
          Обновить
        </button>
      </div>

      {error ? <p className="text-sm text-amber-200">{error}</p> : null}

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="overflow-x-auto rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
          <table className="w-full text-left">
            <thead className="text-[10px] uppercase tracking-wide text-zinc-500">
              <tr>
                <th className="py-1">From</th>
                <th>Subject</th>
                <th>Date</th>
                <th>Status</th>
                <th>Virtus ID</th>
                <th>Customer</th>
              </tr>
            </thead>
            <tbody>
              {visible.length ? (
                visible.map((thread) => {
                  const user = oracleUsers.find((row) => (row.email || "").trim().toLowerCase() === senderEmail(thread.from));
                  return (
                    <tr
                      key={thread.id}
                      className={`cursor-pointer border-t border-white/5 hover:bg-white/5 ${selectedId === thread.id ? "bg-white/5" : ""}`}
                      onClick={() => void openThread(thread)}
                    >
                      <td className="py-2">{thread.from}</td>
                      <td>{thread.subject || "(no subject)"}</td>
                      <td>{stamp(thread.updated_at || thread.created_at)}</td>
                      <td>{thread.ui_status || thread.status}</td>
                      <td className="font-mono text-xs">{user?.virtusId || "—"}</td>
                      <td>{user?.name || "Customer not linked"}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="py-6 text-zinc-500">
                    Нет входящих писем. Список берётся только из подключённой почты — тестовые обращения не создаются.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
          {selected ? (
            <div className="space-y-3">
              <p>Customer: {linked?.name || "Customer not linked"}</p>
              <p>Virtus ID: {linked?.virtusId || "—"}</p>
              <p>Email: {selected.from}</p>
              <p>Subject: {selected.subject}</p>
              <p>Received: {stamp(selected.created_at || selected.updated_at)}</p>
              <p>Status: {selected.ui_status || selected.status}</p>
              <div className="max-h-56 space-y-2 overflow-y-auto rounded-lg border border-white/10 bg-black/20 p-3 text-zinc-300">
                {(selected.messages || []).map((message) => (
                  <p key={message.id || message.created_at}>
                    <span className="text-[10px] uppercase text-zinc-500">{message.direction} · {stamp(message.created_at)}</span>
                    <br />
                    {message.text || message.subject || "—"}
                  </p>
                ))}
              </div>
              <div className="rounded-lg border border-white/10 bg-black/20 px-3 py-3 text-xs text-zinc-400">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">Oracle Account</p>
                {linked ? (
                  <>
                    <p>Balance: {linked.balance || 0} VIRT</p>
                    <p>Readings: {linked.readings || 0}</p>
                    <p>Spent: {linked.spent || 0} VIRT</p>
                    <p>Last activity: {stamp(linked.lastSeen)}</p>
                  </>
                ) : (
                  <p>Customer not linked</p>
                )}
              </div>
              <textarea
                className="min-h-[90px] w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
                value={reply}
                onChange={(event) => setReply(event.target.value)}
                placeholder="Ответ через подключённую почту"
              />
              <div className="flex flex-wrap gap-2">
                <button type="button" disabled={busy} onClick={() => void sendReply()} className="rounded-lg border border-amber-400/40 px-3 py-2 text-xs text-amber-100">
                  Ответить
                </button>
                <button type="button" disabled={busy} onClick={() => void setStatus("OPEN")} className="rounded-lg border border-white/15 px-3 py-2 text-xs">
                  Пометить как прочитанное
                </button>
                <button type="button" disabled={busy} onClick={() => void setStatus("CLOSED")} className="rounded-lg border border-white/15 px-3 py-2 text-xs">
                  Закрыть
                </button>
              </div>
              {note ? <p className="text-xs text-amber-200">{note}</p> : null}
            </div>
          ) : (
            <p className="text-zinc-500">Выбери письмо, чтобы открыть обращение и Oracle-профиль, если email совпадает.</p>
          )}
        </div>
      </div>
    </section>
  );
}
