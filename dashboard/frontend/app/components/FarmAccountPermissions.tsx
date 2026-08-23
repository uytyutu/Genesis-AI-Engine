"use client";

import {
  setFarmAccountConnected,
  setFarmAccountMode,
  type FarmAccountMode,
  type FarmAccountState,
} from "../lib/farmAccountPermissions";

export function FarmAccountPermissions({
  accounts,
  onChange,
}: {
  accounts: FarmAccountState[];
  onChange: (next: FarmAccountState[]) => void;
}) {
  return (
    <section className="rounded-xl border border-white/10 bg-black/25 px-4 py-3 text-sm">
      <h2 className="text-sm font-semibold text-white">Accounts &amp; Permissions</h2>
      <p className="mt-1 text-[11px] leading-relaxed text-genesis-muted">
        Белый список площадок. Farm <strong>не</strong> входит автоматически никуда без вашего
        разрешения. Автовход = только уже подключённый токен/сессия; окно «Select an account» не
        должно открываться само.
      </p>
      <ul className="mt-3 space-y-2">
        {accounts.map((a) => (
          <li
            key={a.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2"
          >
            <div className="min-w-0">
              <p className="font-medium text-white">
                {a.label}{" "}
                <span className={a.connected ? "text-emerald-300" : "text-zinc-500"}>
                  {a.connected ? "· Подключено ✅" : "· Не подключено"}
                </span>
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
              {(["ask", "auto", "off"] as FarmAccountMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  disabled={!a.connected && m === "auto"}
                  onClick={() => onChange(setFarmAccountMode(a.id, m))}
                  className={`rounded border px-2 py-0.5 ${
                    a.mode === m
                      ? "border-sky-400/50 bg-sky-950/40 text-sky-100"
                      : "border-white/15 text-zinc-300 hover:bg-white/5"
                  } disabled:opacity-40`}
                >
                  {m === "ask" ? "Спрашивать" : m === "auto" ? "Авто" : "Выкл"}
                </button>
              ))}
              <button
                type="button"
                onClick={() => onChange(setFarmAccountConnected(a.id, !a.connected))}
                className="rounded border border-amber-400/35 px-2 py-0.5 text-amber-100"
              >
                {a.connected ? "Отключить" : "Отметить подключённым"}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
