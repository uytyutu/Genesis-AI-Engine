"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import OracleSupportDesk from "../support/OracleSupportDesk";

const ORACLE = process.env.NEXT_PUBLIC_ORACLE_URL || "http://127.0.0.1:4173";
const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

type OracleUser = {
  virtusId?: string;
  name?: string;
  email?: string;
  registered?: string;
  lastSeen?: string;
  balance?: number;
  received?: number;
  spent?: number;
  readings?: number;
};

type LedgerRow = {
  created_at?: string;
  type?: string;
  amount?: number;
  reference?: string;
  reason?: string;
  virtusId?: string;
  id?: string;
  transaction_id?: string;
};

type TopupRow = {
  transaction_id?: string;
  virtus_id?: string;
  user_id?: string;
  name?: string;
  amount?: number;
  reason?: string;
  created_at?: string;
  created_by?: string;
  status?: string;
  type?: string;
  balance_before?: number;
  balance_after?: number;
};

type OwnerBundle = {
  dashboard?: {
    today?: Record<string, number>;
    funnel?: Record<string, number>;
    gifted?: number;
    spent?: number;
    users?: number;
    services?: { id: string; title: string; views: number; started: number; completed: number }[];
  };
  users?: OracleUser[];
  audit?: LedgerRow[];
  ledger?: LedgerRow[];
  topups?: TopupRow[];
  readings?: { title?: string; service_id?: string; question?: string; created_at?: string; resultLocale?: string; cost?: number; who?: string }[];
  error?: string;
};

const AMOUNTS = [100, 200, 500, 1000, 1500];

const visibleName = (name?: string) => (name && !/^liveprobe$/i.test(name) && !/^test/i.test(name) ? name : "—");

const stamp = (value?: string) => (value || "").slice(0, 16).replace("T", " ") || "—";

export default function OracleControl() {
  const [key, setKey] = useState("");
  const [data, setData] = useState<OwnerBundle | null>(null);
  const [virtusId, setVirtusId] = useState("");
  const [picked, setPicked] = useState<OracleUser | null>(null);
  const [amount, setAmount] = useState(100);
  const [customAmount, setCustomAmount] = useState(false);
  const [reason, setReason] = useState("Подарок пользователю");
  const [confirming, setConfirming] = useState(false);
  const [success, setSuccess] = useState<{ amount: number; virtusId: string; balance: number; transaction_id: string } | null>(null);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [filterId, setFilterId] = useState("");
  const [filterDate, setFilterDate] = useState("");
  const [filterOwner, setFilterOwner] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [detail, setDetail] = useState<TopupRow | null>(null);
  const [supportKpi, setSupportKpi] = useState({ neu: 0, open: 0, waiting: 0 });
  const path = usePathname() || "";
  const tab = path.includes("/support")
    ? "support"
    : path.includes("/top-up") || path.includes("/wallet")
      ? "wallet"
      : path.includes("/users")
        ? "users"
        : path.includes("/registrations")
          ? "registrations"
          : path.includes("/readings")
            ? "readings"
            : path.includes("/payments")
              ? "payments"
              : path.includes("/ledger")
                ? "ledger"
                : path.includes("/services")
                  ? "services"
                  : path.includes("/analytics")
                    ? "analytics"
                    : "overview";
  const booted = useRef(false);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? sessionStorage.getItem("ORACLE_OWNER_KEY") : "";
    if (saved) setKey(saved);
  }, []);

  const headers = useMemo(
    () => ({
      "content-type": "application/json",
      "x-oracle-owner": key,
    }),
    [key]
  );

  const loadSupport = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/support/threads`);
      if (!res.ok) return;
      const body = await res.json();
      const items = (body.items || []) as { ui_status?: string; status?: string }[];
      setSupportKpi({
        neu: items.filter((row) => row.ui_status === "NEW").length,
        open: items.filter((row) => row.ui_status === "OPEN").length,
        waiting: items.filter((row) => row.ui_status === "WAITING").length,
      });
    } catch {
      /* honest empty — no mock inbox */
    }
  }, []);

  const load = useCallback(async () => {
    if (!key) {
      setStatus("Введи owner key.");
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(`${ORACLE}/oracle/owner`, { headers });
      const body = (await res.json()) as OwnerBundle;
      if (body.error) {
        setStatus(body.error === "OWNER_REQUIRED" ? "Ключ не принят." : body.error);
        setData(null);
        return;
      }
      setData(body);
      setStatus("");
      sessionStorage.setItem("ORACLE_OWNER_KEY", key);
      void loadSupport();
    } catch {
      setStatus("Oracle недоступен. Запусти web-server на :4173.");
    } finally {
      setBusy(false);
    }
  }, [headers, key, loadSupport]);

  useEffect(() => {
    if (!key || booted.current) return;
    if (sessionStorage.getItem("ORACLE_OWNER_KEY") !== key) return;
    booted.current = true;
    void load();
  }, [key, load]);

  const findUser = async (event: FormEvent) => {
    event.preventDefault();
    if (!key) return;
    setBusy(true);
    setSuccess(null);
    setConfirming(false);
    try {
      const res = await fetch(`${ORACLE}/oracle/owner`, {
        method: "POST",
        headers,
        body: JSON.stringify({ action: "find_user", virtusId }),
      });
      const body = await res.json();
      if (!body.ok || !body.user) {
        setPicked(null);
        setStatus("Пользователь с таким Virtus ID не найден.");
        return;
      }
      setPicked(body.user);
      setStatus("");
    } finally {
      setBusy(false);
    }
  };

  const gift = async () => {
    if (!picked?.virtusId) {
      setStatus("Сначала найди Virtus ID.");
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(`${ORACLE}/oracle/owner`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          action: "admin_gift",
          virtusId: picked.virtusId,
          amount,
          reason,
          created_by: "owner",
        }),
      });
      const body = await res.json();
      if (!body.ok) {
        setStatus(body.error === "USER_NOT_FOUND" ? "Пользователь с таким Virtus ID не найден." : body.error || "Не удалось начислить.");
        return;
      }
      const nextBalance = Number(body.balance ?? body.balance_after ?? 0);
      setSuccess({
        amount: Number(body.amount || amount),
        virtusId: body.virtusId || picked.virtusId,
        balance: nextBalance,
        transaction_id: body.transaction_id || body.entry?.transaction_id || body.entry?.id || "",
      });
      setConfirming(false);
      setStatus("");
      if (body.owner) setData(body.owner);
      const next = (body.owner?.users || []).find((user: OracleUser) => user.virtusId === picked.virtusId);
      if (next) setPicked(next);
      else setPicked({ ...picked, balance: nextBalance, received: Number(picked.received || 0) + amount });
    } finally {
      setBusy(false);
    }
  };

  const today = data?.dashboard?.today || {};
  const funnel = data?.dashboard?.funnel || {};
  const gifted = Number(data?.dashboard?.gifted ?? today.virtGifted ?? 0);
  const spent = Number(data?.dashboard?.spent ?? today.virtSpent ?? 0);
  const usersCount = Number(data?.dashboard?.users ?? data?.users?.length ?? 0);
  const topups = (data?.topups || []).filter((row) => {
    if (filterId && !(row.virtus_id || "").toUpperCase().includes(filterId.toUpperCase())) return false;
    if (filterDate && !(row.created_at || "").startsWith(filterDate)) return false;
    if (filterOwner && !(row.created_by || "").toLowerCase().includes(filterOwner.toLowerCase())) return false;
    if (filterStatus && (row.status || "").toUpperCase() !== filterStatus.toUpperCase()) return false;
    return true;
  });

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8 text-zinc-100">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-zinc-500">Mission Control · Virtus Oracle</p>
          <h1 className="mt-1 text-2xl font-semibold text-white">Virtus Oracle · Owner</h1>
          <p className="mt-1 text-sm text-zinc-400">Пульт владельца: Virtus ID, внутренние монеты, ledger и входящая почта. Не публичная витрина.</p>
        </div>
        <Link href="/executive" className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5">
          Назад в MC
        </Link>
      </header>

      <section className="rounded-xl border border-amber-400/20 bg-amber-950/20 p-4">
        <form
          className="flex flex-wrap gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            void load();
          }}
        >
          <input
            className="min-w-[180px] flex-1 rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
            type="password"
            placeholder="ORACLE_OWNER_KEY"
            value={key}
            onChange={(event) => setKey(event.target.value)}
          />
          <button type="submit" disabled={busy} className="rounded-lg border border-amber-400/40 bg-amber-950/40 px-3 py-2 text-sm text-amber-100">
            Открыть пульт
          </button>
        </form>
      </section>

      {data ? (
        <>
          <nav className="flex flex-wrap gap-2 text-xs">
            {[
              ["overview", "Overview", "/executive/oracle"],
              ["users", "Users", "/executive/oracle/users"],
              ["registrations", "Registrations", "/executive/oracle/registrations"],
              ["readings", "Readings", "/executive/oracle/readings"],
              ["payments", "Payments", "/executive/oracle/payments"],
              ["ledger", "VIRT Ledger", "/executive/oracle/ledger"],
              ["services", "Services", "/executive/oracle/services"],
              ["analytics", "Analytics", "/executive/oracle/analytics"],
              ["wallet", "Top-up", "/executive/oracle/top-up"],
              ["support", "Support", "/executive/oracle/support"],
            ].map(([id, label, href]) => (
              <Link
                key={id}
                href={href}
                className={`rounded-lg border px-3 py-1.5 ${tab === id ? "border-amber-400/50 text-amber-100" : "border-white/15 text-zinc-400"}`}
              >
                {label}
              </Link>
            ))}
          </nav>

          {tab === "overview" || tab === "analytics" ? (
            <section className="grid gap-2 sm:grid-cols-4">
              {[
                ["Users", usersCount, "/executive/oracle/users"],
                ["Registrations", today.registrations, "/executive/oracle/registrations"],
                ["Readings", today.oracleReadings || today.started, "/executive/oracle/readings"],
                ["Revenue", today.purchases || 0, "/executive/oracle/payments"],
                ["VIRT Spent", spent, "/executive/oracle/ledger"],
                ["VIRT Gifted", gifted, "/executive/oracle/top-up"],
                ["Support", supportKpi.neu, "/executive/oracle/support"],
              ].map(([label, value, href]) => (
                <Link key={String(label)} href={String(href)} className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3 hover:bg-white/5">
                  <p className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</p>
                  <p className="mt-1 text-xl text-white">{value || 0}</p>
                </Link>
              ))}
            </section>
          ) : null}

          {tab === "overview" ? (
            <section className="grid gap-2 sm:grid-cols-3">
              <Link href="/executive/support" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3 hover:bg-white/5">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">New messages</p>
                <p className="mt-1 text-xl text-white">{supportKpi.neu}</p>
              </Link>
              <Link href="/executive/support" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3 hover:bg-white/5">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">Open</p>
                <p className="mt-1 text-xl text-white">{supportKpi.open}</p>
              </Link>
              <Link href="/executive/support" className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3 hover:bg-white/5">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">Waiting</p>
                <p className="mt-1 text-xl text-white">{supportKpi.waiting}</p>
              </Link>
            </section>
          ) : null}

          {tab === "overview" ? (
            <p className="text-sm text-zinc-400">
              Воронка сегодня: {funnel.visitors || 0} → рег. {funnel.register || 0} → старт {funnel.startOracle || 0} → чтение {funnel.reading || 0}
            </p>
          ) : null}

          {tab === "wallet" ? (
            <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <h2 className="text-sm font-semibold text-white">Пополнение пользователя</h2>
              <form className="mt-3 flex flex-wrap gap-2" onSubmit={(event) => void findUser(event)}>
                <input
                  className="min-w-[200px] flex-1 rounded-lg border border-white/10 bg-black/40 px-3 py-2 font-mono text-sm"
                  value={virtusId}
                  onChange={(event) => setVirtusId(event.target.value.toUpperCase())}
                  placeholder="VRT-________"
                />
                <button type="submit" className="rounded-lg border border-white/15 px-3 py-2 text-sm">
                  Найти пользователя
                </button>
              </form>
              {picked ? (
                <div className="mt-4 grid gap-1 rounded-lg border border-white/10 bg-black/20 px-3 py-3 text-sm text-zinc-300">
                  <p>Virtus ID: {picked.virtusId}</p>
                  <p>Имя: {visibleName(picked.name)}</p>
                  <p>Email: {picked.email || "—"}</p>
                  <p>Дата регистрации: {stamp(picked.registered)}</p>
                  <p>Последняя активность: {stamp(picked.lastSeen)}</p>
                  <p>Баланс: {picked.balance || 0} VIRT</p>
                  <p>Всего получено: {picked.received || 0} VIRT</p>
                  <p>Потрачено: {picked.spent || 0} VIRT</p>
                  <p>Количество раскладов: {picked.readings || 0}</p>
                </div>
              ) : null}

              {picked && !confirming && !success ? (
                <div className="mt-4 space-y-3">
                  <h3 className="text-sm font-semibold text-white">Начислить монеты</h3>
                  <div className="flex flex-wrap gap-2">
                    {AMOUNTS.map((value) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => {
                          setAmount(value);
                          setCustomAmount(false);
                        }}
                        className={`rounded-lg border px-3 py-2 text-sm ${!customAmount && amount === value ? "border-amber-400/50 text-amber-100" : "border-white/15 text-zinc-300"}`}
                      >
                        +{value}
                      </button>
                    ))}
                    <button
                      type="button"
                      onClick={() => setCustomAmount(true)}
                      className={`rounded-lg border px-3 py-2 text-sm ${customAmount ? "border-amber-400/50 text-amber-100" : "border-white/15 text-zinc-300"}`}
                    >
                      Другое
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <input
                      className="w-28 rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
                      type="number"
                      min={1}
                      value={amount}
                      onChange={(event) => {
                        setAmount(Number(event.target.value));
                        setCustomAmount(true);
                      }}
                    />
                    <input
                      className="min-w-[200px] flex-1 rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                      placeholder="Подарок пользователю"
                    />
                    <button
                      type="button"
                      disabled={busy || !amount}
                      onClick={() => setConfirming(true)}
                      className="rounded-lg border border-amber-400/40 bg-amber-950/30 px-3 py-2 text-sm text-amber-100"
                    >
                      Начислить
                    </button>
                  </div>
                </div>
              ) : null}

              {picked && confirming ? (
                <div className="mt-4 space-y-2 rounded-lg border border-amber-400/30 bg-amber-950/20 px-3 py-3 text-sm">
                  <p>Пользователь: {visibleName(picked.name)}</p>
                  <p>Virtus ID: {picked.virtusId}</p>
                  <p>Текущий баланс: {picked.balance || 0} VIRT</p>
                  <p>Начисление: +{amount} VIRT</p>
                  <p>Новый баланс: {(picked.balance || 0) + amount} VIRT</p>
                  <p>Причина: {reason || "Подарок пользователю"}</p>
                  <div className="flex gap-2 pt-2">
                    <button type="button" disabled={busy} onClick={() => void gift()} className="rounded-lg border border-amber-400/50 bg-amber-950/40 px-3 py-2 text-sm text-amber-50">
                      Подтвердить начисление
                    </button>
                    <button type="button" onClick={() => setConfirming(false)} className="rounded-lg border border-white/15 px-3 py-2 text-sm">
                      Отмена
                    </button>
                  </div>
                </div>
              ) : null}

              {success ? (
                <div className="mt-4 space-y-1 rounded-lg border border-emerald-400/30 bg-emerald-950/20 px-3 py-3 text-sm text-emerald-100">
                  <p>✓ {success.amount} VIRT начислено</p>
                  <p>Virtus ID: {success.virtusId}</p>
                  <p>Новый баланс: {success.balance} VIRT</p>
                  <p>Transaction ID: {success.transaction_id || "—"}</p>
                </div>
              ) : null}
            </section>
          ) : null}

          {tab === "wallet" || tab === "ledger" ? (
            <section className="overflow-x-auto rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
              <h2 className="text-sm font-semibold text-white">Top-up History</h2>
              <p className="mt-1 text-xs text-zinc-500">Внутренние монеты Oracle · тип admin_gift · не on-chain ERC-20</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <input className="rounded-lg border border-white/10 bg-black/40 px-2 py-1.5 text-xs" placeholder="Virtus ID" value={filterId} onChange={(event) => setFilterId(event.target.value)} />
                <input className="rounded-lg border border-white/10 bg-black/40 px-2 py-1.5 text-xs" type="date" value={filterDate} onChange={(event) => setFilterDate(event.target.value)} />
                <input className="rounded-lg border border-white/10 bg-black/40 px-2 py-1.5 text-xs" placeholder="Owner" value={filterOwner} onChange={(event) => setFilterOwner(event.target.value)} />
                <input className="rounded-lg border border-white/10 bg-black/40 px-2 py-1.5 text-xs" placeholder="Status" value={filterStatus} onChange={(event) => setFilterStatus(event.target.value)} />
              </div>
              <table className="mt-3 w-full text-left">
                <thead className="text-[10px] uppercase tracking-wide text-zinc-500">
                  <tr>
                    <th className="py-1">Дата</th>
                    <th>Virtus ID</th>
                    <th>Пользователь</th>
                    <th>Сумма</th>
                    <th>Причина</th>
                    <th>Owner</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {topups.length ? (
                    topups.map((row) => (
                      <tr key={row.transaction_id || `${row.virtus_id}-${row.created_at}`} className="cursor-pointer border-t border-white/5 hover:bg-white/5" onClick={() => setDetail(row)}>
                        <td className="py-1">{stamp(row.created_at)}</td>
                        <td className="font-mono text-xs">{row.virtus_id || "—"}</td>
                        <td>{visibleName(row.name)}</td>
                        <td>+{row.amount || 0}</td>
                        <td>{row.reason || "—"}</td>
                        <td>{row.created_by || "owner"}</td>
                        <td>{row.status || "CONFIRMED"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="py-4 text-zinc-500">
                        Начислений ещё нет.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
              {detail ? (
                <div className="mt-4 space-y-1 rounded-lg border border-white/10 bg-black/20 px-3 py-3 text-xs text-zinc-300">
                  <p>Transaction ID: {detail.transaction_id}</p>
                  <p>user_id: {detail.user_id || detail.virtus_id}</p>
                  <p>virtus_id: {detail.virtus_id}</p>
                  <p>type: {detail.type || "admin_gift"}</p>
                  <p>amount: {detail.amount}</p>
                  <p>balance_before: {detail.balance_before}</p>
                  <p>balance_after: {detail.balance_after}</p>
                  <p>reason: {detail.reason}</p>
                  <p>created_at: {detail.created_at}</p>
                  <p>created_by: {detail.created_by}</p>
                  <p>status: {detail.status}</p>
                  <button type="button" className="mt-2 rounded border border-white/15 px-2 py-1" onClick={() => setDetail(null)}>
                    Закрыть
                  </button>
                </div>
              ) : null}
            </section>
          ) : null}

          {tab === "support" ? <OracleSupportDesk oracleUsers={data.users || []} /> : null}

          {tab === "overview" || tab === "services" ? (
            <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <h2 className="text-sm font-semibold text-white">Услуги</h2>
              <div className="mt-3 overflow-x-auto text-sm">
                {(data.dashboard?.services || []).length ? (
                  <table className="w-full text-left">
                    <thead className="text-[10px] uppercase tracking-wide text-zinc-500">
                      <tr>
                        <th className="py-1">Услуга</th>
                        <th>Просмотры</th>
                        <th>Начато</th>
                        <th>Завершено</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(data.dashboard?.services || []).map((row) => (
                        <tr key={row.id} className="border-t border-white/5">
                          <td className="py-1">{row.title}</td>
                          <td>{row.views}</td>
                          <td>{row.started}</td>
                          <td>{row.completed}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-zinc-500">Пока нет событий по услугам.</p>
                )}
              </div>
            </section>
          ) : null}

          {tab === "users" || tab === "registrations" ? (
            <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <h2 className="text-sm font-semibold text-white">Пользователи</h2>
              <div className="mt-3 overflow-x-auto text-sm">
                <table className="w-full text-left">
                  <thead className="text-[10px] uppercase tracking-wide text-zinc-500">
                    <tr>
                      <th className="py-1">Virtus ID</th>
                      <th>Имя</th>
                      <th>Email</th>
                      <th>Регистрация</th>
                      <th className="text-right">Монеты</th>
                      <th className="text-right">Потрачено</th>
                      <th className="text-right">Раскладов</th>
                      <th>Активность</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data.users || []).map((user) => (
                      <tr
                        key={user.virtusId}
                        className="cursor-pointer border-t border-white/5 hover:bg-white/5"
                        onClick={() => {
                          setPicked(user);
                          setVirtusId(user.virtusId || "");
                        }}
                      >
                        <td className="py-1 font-mono text-xs">{user.virtusId}</td>
                        <td>{visibleName(user.name)}</td>
                        <td>{user.email || "—"}</td>
                        <td>{(user.registered || "").slice(0, 10)}</td>
                        <td className="text-right">{user.balance || 0}</td>
                        <td className="text-right">{user.spent || 0}</td>
                        <td className="text-right">{user.readings || 0}</td>
                        <td>{stamp(user.lastSeen)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {tab === "readings" ? (
            <section className="overflow-x-auto rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm">
              <h2 className="text-sm font-semibold text-white">Расклады</h2>
              <table className="mt-3 w-full text-left">
                <thead className="text-[10px] uppercase tracking-wide text-zinc-500">
                  <tr>
                    <th className="py-1">User</th>
                    <th>Service</th>
                    <th>Language</th>
                    <th>Cost</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.readings || []).length ? (
                    (data.readings || []).map((row, index) => (
                      <tr key={`${row.created_at}-${index}`} className="border-t border-white/5">
                        <td className="py-1">{row.who || "—"}</td>
                        <td>{row.title || row.service_id}</td>
                        <td>{row.resultLocale || "—"}</td>
                        <td>{row.cost || 0}</td>
                        <td>{stamp(row.created_at)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-4 text-zinc-500">
                        Раскладов пока нет.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>
          ) : null}

          {tab === "payments" ? (
            <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm text-zinc-400">
              Stripe выключен. Покупки фиатом не идут. Owner начисляет внутренние монеты через Top-up.
            </section>
          ) : null}

          {tab === "analytics" && data.dashboard ? (
            <p className="text-sm text-zinc-400">Revenue stays 0 € until a real fiat purchase. Gifted coins are internal ledger only.</p>
          ) : null}
        </>
      ) : null}

      {status ? <p className="text-sm text-amber-200">{status}</p> : null}
    </main>
  );
}
