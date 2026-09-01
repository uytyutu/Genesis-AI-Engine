"use client";

import { useState } from "react";

type Props = {
  planId: string;
  netOutputSats: number;
  destinationAddress: string;
  open: boolean;
  onCancel: () => void;
  onConfirm: (okPhrase: string) => void;
};

/**
 * Двухшаговое OK-подтверждение перед локальной подписью своей консолидации.
 */
export function OkProtocolModal({
  planId,
  netOutputSats,
  destinationAddress,
  open,
  onCancel,
  onConfirm,
}: Props) {
  const [step, setStep] = useState<1 | 2>(1);
  const [phrase, setPhrase] = useState("");

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-950 p-5 shadow-xl">
        <h2 className="text-lg font-semibold text-emerald-400">Протокол подтверждения OK</h2>
        <p className="mt-1 text-xs text-zinc-400">
          Подтверждает консолидацию только <span className="text-zinc-200">ваших</span> UTXO. Чужие источники
          исключены.
        </p>

        {step === 1 ? (
          <div className="mt-4 space-y-3 font-mono text-xs text-zinc-300">
            <p>
              План: <span className="text-cyan-300">{planId}</span>
            </p>
            <p>
              Чистый выход:{" "}
              <span className="text-emerald-300">{netOutputSats.toLocaleString("ru-RU")} sats</span>
            </p>
            <p className="break-all">
              Vault: <span className="text-cyan-300">{destinationAddress}</span>
            </p>
            <button
              type="button"
              className="mt-2 w-full rounded-lg bg-cyan-600 py-2 text-sm font-bold text-zinc-950 hover:bg-cyan-500"
              onClick={() => setStep(2)}
            >
              Проверено — продолжить
            </button>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            <label className="block text-xs text-zinc-400">
              Введите <span className="font-mono text-emerald-400">OK</span>, чтобы разрешить подготовку локальной
              подписи
            </label>
            <input
              value={phrase}
              onChange={(e) => setPhrase(e.target.value)}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-sm text-zinc-100"
              placeholder="OK"
              autoFocus
            />
            <button
              type="button"
              className="w-full rounded-lg bg-emerald-600 py-2 text-sm font-bold text-zinc-950 hover:bg-emerald-500 disabled:opacity-40"
              disabled={phrase.trim() !== "OK"}
              onClick={() => onConfirm(phrase)}
            >
              Подтвердить OK Protocol
            </button>
          </div>
        )}

        <button
          type="button"
          className="mt-3 w-full rounded-lg border border-zinc-700 py-2 text-sm text-zinc-300 hover:bg-zinc-900"
          onClick={() => {
            setStep(1);
            setPhrase("");
            onCancel();
          }}
        >
          Отмена
        </button>
      </div>
    </div>
  );
}
