"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { publicApiBase } from "../../lib/publicApiBase";
import {
  bridgePortalSession,
  setClientSession,
} from "../../lib/clientAuth";

type Peek = {
  ok?: boolean;
  error?: string;
  label?: string;
  banner_ru?: string;
  banner_de?: string;
  package_id?: string;
};

type ClaimResult = {
  ok?: boolean;
  email?: string;
  password?: string;
  password_generated?: boolean;
  token?: string;
  name?: string;
  order_id?: string;
  business_name?: string;
  message_ru?: string;
  workspace_path?: string;
  login_path?: string;
  status_path?: string;
  detail?: string;
};

const NICHES = [
  "Handwerk",
  "Beauty / Salon",
  "Restaurant / Café",
  "Zahnarzt / Praxis",
  "Autoreparatur",
  "Reinigung",
  "Immobilien",
  "IT / Agentur",
  "Shop / Handel",
  "Другое",
];

export default function VirtusGiftClaimPage() {
  const params = useParams();
  const code = String(params?.code || "").trim();
  const api = useMemo(() => publicApiBase(), []);

  const [peek, setPeek] = useState<Peek | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<ClaimResult | null>(null);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [city, setCity] = useState("");
  const [niche, setNiche] = useState(NICHES[0]);
  const [description, setDescription] = useState("");

  useEffect(() => {
    if (!code) return;
    void fetch(`${api}/api/public/gift/${encodeURIComponent(code)}`)
      .then((r) => r.json())
      .then((body: Peek) => setPeek(body))
      .catch(() => setPeek({ ok: false, error: "gift_unreachable" }));
  }, [api, code]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!code) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${api}/api/public/gift/${encodeURIComponent(code)}/claim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          business_name: businessName.trim(),
          city: city.trim(),
          niche,
          description: description.trim(),
          locale: "ru",
        }),
      });
      const body = (await res.json().catch(() => ({}))) as ClaimResult;
      if (!res.ok || !body.ok) {
        const detail = typeof body.detail === "string" ? body.detail : `claim_${res.status}`;
        throw new Error(
          detail === "email_already_registered"
            ? "Этот email уже зарегистрирован. Войдите в кабинет или укажите другой email."
            : detail === "gift_code_used"
              ? "Эта подарочная ссылка уже использована."
              : detail === "description_required"
                ? "Опишите подробнее, какой сайт вам нужен (минимум несколько предложений)."
                : detail,
        );
      }
      if (body.token && body.name) {
        setClientSession(body.token, body.name);
      }
      if (body.email && body.password) {
        await bridgePortalSession(body.email, body.password);
      }
      setDone(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось активировать подарок");
    } finally {
      setBusy(false);
    }
  }

  if (!code) {
    return (
      <main className="min-h-screen bg-[#0b0d12] px-4 py-16 text-center text-zinc-200">
        <p>Ссылка подарка неполная.</p>
      </main>
    );
  }

  if (peek && peek.ok === false) {
    return (
      <main className="min-h-screen bg-[#0b0d12] px-4 py-16 text-zinc-100">
        <div className="mx-auto max-w-lg rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center">
          <p className="text-xs uppercase tracking-[0.2em] text-amber-300/80">Virtus Core</p>
          <h1 className="mt-3 text-2xl font-semibold">Подарок недоступен</h1>
          <p className="mt-3 text-sm text-zinc-400">
            {peek.error === "gift_code_used"
              ? "Ссылка уже была использована."
              : peek.error === "gift_code_expired"
                ? "Срок действия ссылки истёк."
                : "Ссылка недействительна."}
          </p>
          <Link href="/client/login" className="mt-8 inline-block text-sm text-amber-200 underline">
            Войти в кабинет
          </Link>
        </div>
      </main>
    );
  }

  if (done?.ok) {
    return (
      <main className="min-h-screen bg-[#0b0d12] px-4 py-12 text-zinc-100">
        <div className="mx-auto max-w-xl space-y-6 rounded-2xl border border-emerald-400/20 bg-emerald-500/[0.06] p-8">
          <p className="text-xs uppercase tracking-[0.2em] text-emerald-300/90">Virtus Core · Подарок</p>
          <h1 className="text-2xl font-semibold">Кабинет готов</h1>
          <p className="text-sm text-zinc-300">
            {done.message_ru ||
              "Мы создали аккаунт и запускаем сайт по вашему описанию. Сохраните доступ."}
          </p>
          <div className="rounded-xl border border-white/10 bg-black/30 p-4 font-mono text-sm">
            <p>
              <span className="text-zinc-500">Логин (email): </span>
              {done.email}
            </p>
            <p className="mt-2">
              <span className="text-zinc-500">Пароль: </span>
              {done.password}
            </p>
            {done.password_generated ? (
              <p className="mt-3 text-xs text-amber-200/90">
                Пароль сгенерирован Virtus — сохраните его сейчас.
              </p>
            ) : null}
          </div>
          <p className="text-sm text-zinc-400">
            Компания: <strong className="text-zinc-200">{done.business_name}</strong>
            {done.order_id ? (
              <>
                <br />
                Заказ сайта: {done.order_id}
              </>
            ) : null}
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              href={done.workspace_path || "/client"}
              className="inline-flex justify-center rounded-xl bg-emerald-400 px-5 py-3 text-sm font-semibold text-zinc-950"
            >
              Открыть кабинет Virtus Core
            </Link>
            {done.status_path ? (
              <Link
                href={done.status_path}
                className="inline-flex justify-center rounded-xl border border-white/15 px-5 py-3 text-sm text-zinc-200"
              >
                Статус сайта
              </Link>
            ) : null}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0b0d12] px-4 py-10 text-zinc-100">
      <div className="mx-auto max-w-xl">
        <header className="mb-8">
          <p className="text-xs uppercase tracking-[0.22em] text-amber-300/85">Virtus Core</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Подарок: ваш сайт + кабинет</h1>
          <p className="mt-3 text-sm leading-relaxed text-zinc-400">
            Без оплаты. Заполните, какой бизнес и сайт вам нужны — Virtus создаст аккаунт, сгенерирует
            сайт и откроет пульт управления, где можно менять тексты, картинки и ссылки.
          </p>
          {peek?.ok ? (
            <p className="mt-2 text-xs text-zinc-500">{peek.label || "Friend gift"}</p>
          ) : (
            <p className="mt-2 text-xs text-zinc-500">Проверяем ссылку…</p>
          )}
        </header>

        <form
          onSubmit={onSubmit}
          className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-6"
        >
          <label className="block space-y-1.5 text-sm">
            <span className="text-zinc-400">Ваше имя</span>
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 outline-none focus:border-amber-300/40"
            />
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="text-zinc-400">Email (это будет логин)</span>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 outline-none focus:border-amber-300/40"
            />
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="text-zinc-400">Название компании / бренда</span>
            <input
              required
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 outline-none focus:border-amber-300/40"
            />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block space-y-1.5 text-sm">
              <span className="text-zinc-400">Город</span>
              <input
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 outline-none focus:border-amber-300/40"
              />
            </label>
            <label className="block space-y-1.5 text-sm">
              <span className="text-zinc-400">Ниша</span>
              <select
                value={niche}
                onChange={(e) => setNiche(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 outline-none focus:border-amber-300/40"
              >
                {NICHES.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="block space-y-1.5 text-sm">
            <span className="text-zinc-400">Какой сайт нужен? Опишите своими словами</span>
            <textarea
              required
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Например: сайт для салона красоты в Дрездене, услуги, цены, запись, фото работ, спокойный премиальный стиль…"
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 outline-none focus:border-amber-300/40"
            />
          </label>

          {error ? <p className="text-sm text-rose-300">{error}</p> : null}

          <button
            type="submit"
            disabled={busy || peek?.ok === false}
            className="w-full rounded-xl bg-amber-300 px-4 py-3 text-sm font-semibold text-zinc-950 disabled:opacity-50"
          >
            {busy ? "Virtus создаёт кабинет и сайт…" : "Получить сайт и кабинет Virtus"}
          </button>
          <p className="text-center text-xs text-zinc-500">
            Оплаты нет. После отправки вы получите логин и пароль.
          </p>
        </form>
      </div>
    </main>
  );
}
