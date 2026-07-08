"use client";

import { useState } from "react";
import { formatEur } from "../lib/formatEur";
import { BRAND_NAME } from "../lib/publicBrand";

type Wallet = { id: string; label: string; icon: string; connected: boolean };

type Props = {
  open: boolean;
  onClose: () => void;
  amount: number;
  wallets: Wallet[];
};

export function WithdrawModal({ open, onClose, amount, wallets }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  if (!open) return null;

  const connected = wallets.filter((w) => w.connected);

  const handleConfirm = () => {
    if (!selected) return;
    setConfirmed(true);
    setTimeout(() => {
      setConfirmed(false);
      setSelected(null);
      onClose();
    }, 2200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md animate-fade-up rounded-2xl border border-genesis-border bg-genesis-panel p-6 shadow-glow">
        {confirmed ? (
          <div className="text-center">
            <p className="text-3xl">✔</p>
            <p className="mt-3 font-semibold">Запрос отправлен</p>
            <p className="mt-2 text-sm text-genesis-muted">
              Перевод выполнит платёжная система — Virtus Core не хранит и не переводит средства.
            </p>
          </div>
        ) : (
          <>
            <p className="genesis-label">Подтвердить вывод</p>
            <p className="mt-2 text-3xl font-bold tabular-nums">{formatEur(amount)}</p>
            <p className="mt-4 text-sm text-genesis-muted">Получатель</p>
            <ul className="mt-2 space-y-2">
              {connected.length === 0 ? (
                <li className="text-sm text-amber-300/90">Сначала подключите кошелёк в Payment Hub.</li>
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
            <div className="mt-6 flex gap-2">
              <button
                type="button"
                disabled={!selected}
                onClick={handleConfirm}
                className="flex-1 rounded-xl bg-genesis-accent py-2.5 text-sm font-semibold text-white disabled:opacity-40 hover:bg-genesis-accent-soft"
              >
                Подтвердить
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-genesis-border px-4 py-2.5 text-sm hover:bg-genesis-elevated"
              >
                Отмена
              </button>
            </div>
            <p className="mt-4 text-center text-[11px] text-genesis-muted">
              Деньги переводит Stripe, PayPal или ваш банк — не {BRAND_NAME}.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
