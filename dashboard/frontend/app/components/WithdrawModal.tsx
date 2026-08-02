"use client";

import { useState } from "react";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Wallet = { id: string; label: string; icon: string; connected: boolean };

type Props = {
  open: boolean;
  onClose: () => void;
  amount: number;
  wallets: Wallet[];
  onDone?: () => void;
};

export function WithdrawModal({ open, onClose, amount, wallets, onDone }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [resultMsg, setResultMsg] = useState("");

  if (!open) return null;

  const connected = wallets.filter((w) => w.connected);

  const handleConfirm = async () => {
    if (!selected || amount <= 0) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/engine/withdraw`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount_eur: amount, wallet_id: selected }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(String(body.detail || body.message || "Вывод не выполнен"));
        return;
      }
      setResultMsg(
        body.message ||
          "Заявка отправлена. Перевод выполнит платёжная система — Virtus Core не хранит средства.",
      );
      setConfirmed(true);
      onDone?.();
      window.setTimeout(() => {
        setConfirmed(false);
        setSelected(null);
        setResultMsg("");
        onClose();
      }, 2200);
    } catch {
      setError("Сеть / backend недоступен");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md animate-fade-up rounded-2xl border border-genesis-border bg-genesis-panel p-6 shadow-glow">
        {confirmed ? (
          <div className="text-center">
            <p className="text-3xl">✔</p>
            <p className="mt-3 font-semibold">Запрос отправлен</p>
            <p className="mt-2 text-sm text-genesis-muted">{resultMsg}</p>
          </div>
        ) : (
          <>
            <p className="genesis-label">Подтвердить вывод</p>
            <p className="mt-2 text-3xl font-bold tabular-nums">{formatEur(amount)}</p>
            <p className="mt-2 text-xs text-genesis-muted">
              Только confirmed available у Earn-источника (обычно Stripe). Не Toloka / LLM.
            </p>
            <p className="mt-4 text-sm text-genesis-muted">Получатель</p>
            <ul className="mt-2 space-y-2">
              {connected.length === 0 ? (
                <li className="text-sm text-amber-300/90">
                  Сначала подключите кошелёк в Payment Hub / Финансы.
                </li>
              ) : (
                connected.map((w) => (
                  <li key={w.id}>
                    <button
                      type="button"
                      onClick={() => setSelected(w.id)}
                      className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-sm transition-colors ${
                        selected === w.id
                          ? "border-genesis-accent bg-genesis-accent/10"
                          : "border-genesis-border hover:border-genesis-accent/50"
                      }`}
                    >
                      <span>{w.icon}</span>
                      <span>{w.label}</span>
                      {selected === w.id && <span className="ml-auto text-emerald-400">✔</span>}
                    </button>
                  </li>
                ))
              )}
            </ul>
            {error ? <p className="mt-3 text-xs text-rose-300">{error}</p> : null}
            <div className="mt-6 flex gap-2">
              <button
                type="button"
                disabled={!selected || busy || amount <= 0}
                onClick={() => void handleConfirm()}
                className="flex-1 rounded-xl bg-genesis-accent py-2.5 text-sm font-semibold text-white disabled:opacity-40 hover:bg-genesis-accent-soft"
              >
                {busy ? "Отправка…" : "Подтвердить"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-genesis-border px-4 py-2.5 text-sm hover:bg-genesis-elevated"
              >
                Отмена
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
