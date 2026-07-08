"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TYPES = [
  { id: "landing-page", label: "Landing Page", enabled: true },
  { id: "telegram-bot", label: "Telegram Bot", enabled: false },
  { id: "shop", label: "Интернет-магазин", enabled: false },
  { id: "crm", label: "CRM", enabled: false },
] as const;

type Step = 1 | 2 | 3 | 4;

export default function CreateProductPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [type, setType] = useState("landing-page");
  const [description, setDescription] = useState("");
  const [audience, setAudience] = useState("");
  const [goal, setGoal] = useState("");
  const [priceEur, setPriceEur] = useState("");
  const [deadline, setDeadline] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState("");

  async function create() {
    setBusy(true);
    setResult("");
    try {
      const price = priceEur.trim() ? Number(priceEur.replace(",", ".")) : null;
      const res = await fetch(`${API}/api/factory/intent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_type: type,
          description,
          audience: audience.trim() || null,
          goal: goal.trim() || null,
          price_eur: price !== null && !Number.isNaN(price) ? price : null,
          deadline: deadline.trim() || null,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setResult(body.detail ?? "Ошибка");
      } else {
        setResult(body.message);
        if (body.product_id) {
          router.push(`/products/${body.product_id}`);
        }
      }
    } catch {
      setResult(`${BRAND_NAME} не запущен. Откройте приложение с рабочего стола.`);
    } finally {
      setBusy(false);
    }
  }

  const canNext =
    step === 1 ||
    (step === 2 && description.trim().length >= 3) ||
    (step === 3 && goal.trim().length >= 2);

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-lg space-y-6">
        <header className="text-center">
          <h1 className="text-2xl font-bold">Создать продукт</h1>
          <p className="mt-1 text-sm text-genesis-muted">
            Отдел создания продуктов · Factory · шаг {step} из 4
          </p>
        </header>

        {step === 1 && (
          <section className="space-y-3 rounded-xl border border-genesis-border bg-genesis-panel p-6">
            <p className="font-medium">Что создать?</p>
            {TYPES.map((t) => (
              <label
                key={t.id}
                className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 ${
                  type === t.id ? "border-genesis-accent bg-genesis-accent/10" : "border-genesis-border"
                } ${!t.enabled ? "opacity-50" : ""}`}
              >
                <input
                  type="radio"
                  name="type"
                  value={t.id}
                  disabled={!t.enabled}
                  checked={type === t.id}
                  onChange={() => setType(t.id)}
                />
                <span>{t.label}</span>
                {!t.enabled && <span className="ml-auto text-xs text-genesis-muted">скоро</span>}
              </label>
            ))}
          </section>
        )}

        {step === 2 && (
          <section className="space-y-4 rounded-xl border border-genesis-border bg-genesis-panel p-6">
            <p className="font-medium">Опишите продукт</p>
            <label className="block text-sm text-genesis-muted">
              Что именно нужно сделать?
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder="Например: сайт стоматологии в Москве, запись на приём, спокойные цвета…"
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white outline-none focus:border-genesis-accent"
              />
            </label>
            <label className="block text-sm text-genesis-muted">
              Для кого? (аудитория)
              <input
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                placeholder="Семьи с детьми, владельцы авто, B2B…"
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white outline-none focus:border-genesis-accent"
              />
            </label>
          </section>
        )}

        {step === 3 && (
          <section className="space-y-4 rounded-xl border border-genesis-border bg-genesis-panel p-6">
            <p className="font-medium">Цель и сроки</p>
            <label className="block text-sm text-genesis-muted">
              Цель продукта
              <input
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Записи на приём, заявки, продажи…"
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white outline-none focus:border-genesis-accent"
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm text-genesis-muted">
                Цена (€, опционально)
                <input
                  value={priceEur}
                  onChange={(e) => setPriceEur(e.target.value)}
                  inputMode="decimal"
                  placeholder="49"
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white outline-none focus:border-genesis-accent"
                />
              </label>
              <label className="block text-sm text-genesis-muted">
                Дедлайн (опционально)
                <input
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                  placeholder="15 июля"
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white outline-none focus:border-genesis-accent"
                />
              </label>
            </div>
          </section>
        )}

        {step === 4 && (
          <section className="space-y-3 rounded-xl border border-genesis-border bg-genesis-panel p-6 text-sm">
            <p className="font-medium">Подтверждение</p>
            <SummaryRow label="Тип" value={TYPES.find((t) => t.id === type)?.label ?? type} />
            <SummaryRow label="Описание" value={description} />
            {audience.trim() && <SummaryRow label="Аудитория" value={audience} />}
            <SummaryRow label="Цель" value={goal} />
            {priceEur.trim() && <SummaryRow label="Цена" value={`${priceEur} €`} />}
            {deadline.trim() && <SummaryRow label="Дедлайн" value={deadline} />}
            <p className="pt-2 text-xs text-genesis-muted">
              Factory создаст лендинг, проверит качество и откроет превью — обычно ~1 минута.
            </p>
          </section>
        )}

        <div className="flex gap-3">
          {step > 1 && (
            <button
              type="button"
              onClick={() => setStep((s) => (s - 1) as Step)}
              className="flex-1 rounded-xl border border-genesis-border py-3"
            >
              Назад
            </button>
          )}
          {step < 4 ? (
            <button
              type="button"
              disabled={!canNext}
              onClick={() => setStep((s) => (s + 1) as Step)}
              className="flex-1 rounded-xl bg-genesis-accent py-3 font-semibold disabled:opacity-50"
            >
              Далее
            </button>
          ) : (
            <button
              type="button"
              disabled={busy}
              onClick={create}
              className="flex-1 rounded-xl bg-genesis-accent py-3 font-semibold disabled:opacity-50"
            >
              {busy ? "Factory работает…" : "Создать продукт"}
            </button>
          )}
        </div>

        {result && (
          <p className="rounded-lg bg-genesis-bg p-3 text-sm text-genesis-muted">{result}</p>
        )}

        <p className="text-center">
          <Link href="/" className="text-sm text-genesis-muted hover:text-white">
            ← {BRAND_NAME}
          </Link>
        </p>
      </div>
    </main>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-genesis-border/50 py-2 last:border-0">
      <span className="text-genesis-muted">{label}</span>
      <span className="max-w-[60%] text-right font-medium">{value}</span>
    </div>
  );
}
