"use client";

/**
 * Dedicated AI Bot order wizard — not the website /order form.
 * Website and AI Bot are separate products.
 * Extra channels expand the same bot later («Добавить канал») — each costs setup.
 */

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PublicPageShell } from "../../components/PublicPageShell";
import { BRAND_NAME } from "../../lib/brand";
import { formatApiDetail } from "../../lib/formatApiError";
import { startOrderCheckout } from "../../lib/orderCheckout";
import { publicApiBase } from "../../lib/publicApiBase";
import { getVisitorId } from "../../lib/visitorId";

const API = publicApiBase();

type BotOffer = {
  package_id: string;
  name: string;
  setup_amount: number;
  monthly_amount: number;
  setup_label: string;
  monthly_label: string;
  price_label: string;
  currency: string;
  symbol: string;
  market_code: string;
};

type ChannelId =
  | "telegram"
  | "website_chat"
  | "whatsapp"
  | "instagram"
  | "facebook_messenger";

const CHANNELS: {
  id: ChannelId;
  label: string;
  available: boolean;
  addonEur: number;
}[] = [
  { id: "telegram", label: "Telegram", available: true, addonEur: 0 },
  { id: "website_chat", label: "Website Chat", available: true, addonEur: 149 },
  { id: "whatsapp", label: "WhatsApp", available: false, addonEur: 199 },
  { id: "instagram", label: "Instagram", available: false, addonEur: 199 },
  {
    id: "facebook_messenger",
    label: "Facebook Messenger",
    available: false,
    addonEur: 199,
  },
];

const CAPABILITIES: { id: string; label: string }[] = [
  { id: "consult", label: "Консультировать клиентов" },
  { id: "faq", label: "Отвечать на вопросы" },
  { id: "leads", label: "Принимать заявки" },
  { id: "booking", label: "Записывать клиентов" },
  { id: "handoff", label: "Передавать диалог сотруднику" },
  { id: "always_on", label: "Работать 24/7" },
];

const KNOWLEDGE: { id: string; label: string }[] = [
  { id: "website", label: "Мой сайт" },
  { id: "pdf", label: "PDF-документы" },
  { id: "faq", label: "FAQ" },
  { id: "word", label: "Документы Word" },
  { id: "manual_text", label: "Текст вручную" },
  { id: "later", label: "Пока не загружать" },
];

const HANDOFF: { id: string; label: string }[] = [
  { id: "when_asks_manager", label: "Когда клиент просит менеджера" },
  { id: "when_unknown", label: "Когда бот не знает ответ" },
  { id: "after_lead", label: "После заявки" },
  { id: "never", label: "Никогда" },
];

const LANGUAGES: { id: string; label: string }[] = [
  { id: "de", label: "Немецкий" },
  { id: "ru", label: "Русский" },
  { id: "en", label: "Английский" },
  { id: "uk", label: "Украинский" },
  { id: "other", label: "Другой" },
];

const EXTRAS: { id: string; label: string }[] = [
  { id: "ai_enabled", label: "Подключение AI" },
  { id: "company_training", label: "Обучение на информации компании" },
  { id: "website_integration", label: "Интеграция с сайтом" },
];

const STEPS = [
  "Интеграции",
  "Компания",
  "Задачи",
  "Knowledge Base",
  "Языки и эскалация",
  "Итог",
] as const;

function normalizePackageId(raw: string | null): string {
  const p = (raw || "bot_business").trim().toLowerCase();
  if (p.startsWith("bot_")) return p;
  if (p === "starter") return "bot_starter";
  if (p === "professional" || p === "pro") return "bot_professional";
  if (p === "business") return "bot_business";
  return "bot_business";
}

export default function BotOrderPage() {
  return (
    <PublicPageShell>
      <div className="relative mx-auto max-w-2xl space-y-8 py-8 pb-28 animate-fade-up">
        <Suspense fallback={<p className="text-center text-genesis-muted">Загрузка…</p>}>
          <BotOrderWizard />
        </Suspense>
      </div>
    </PublicPageShell>
  );
}

function BotOrderWizard() {
  const search = useSearchParams();
  const [step, setStep] = useState(1);
  const [market, setMarket] = useState("DE");
  const [packageId, setPackageId] = useState("bot_business");
  const [offers, setOffers] = useState<BotOffer[]>([]);
  const [loadingOffers, setLoadingOffers] = useState(true);

  const [channels, setChannels] = useState<ChannelId[]>(["telegram"]);
  const [channelInterest, setChannelInterest] = useState<ChannelId[]>([]);

  const [businessName, setBusinessName] = useState("");
  const [activity, setActivity] = useState("");
  const [website, setWebsite] = useState("");
  const [country, setCountry] = useState("");

  const [capabilities, setCapabilities] = useState<string[]>([
    "consult",
    "leads",
    "always_on",
  ]);
  const [knowledge, setKnowledge] = useState<string[]>(["website"]);
  const [handoff, setHandoff] = useState<string[]>([
    "when_asks_manager",
    "when_unknown",
  ]);
  const [languages, setLanguages] = useState<string[]>(["de", "ru"]);
  const [extras, setExtras] = useState<string[]>(["ai_enabled", "company_training"]);

  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState<{
    order_id: string;
    package_name: string;
    price_label?: string;
    price_eur?: number;
  } | null>(null);

  useEffect(() => {
    const pkg = normalizePackageId(search.get("package"));
    const m = (search.get("market") || "DE").toUpperCase();
    setPackageId(pkg);
    setMarket(m);
    setCountry(m);
  }, [search]);

  useEffect(() => {
    let cancelled = false;
    setLoadingOffers(true);
    fetch(`${API}/api/public/bots/pricing?market=${encodeURIComponent(market)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        if (cancelled || !body) return;
        const list = (body.packages || body.items || []) as BotOffer[];
        setOffers(Array.isArray(list) ? list : []);
      })
      .catch(() => {
        if (!cancelled) setOffers([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingOffers(false);
      });
    return () => {
      cancelled = true;
    };
  }, [market]);

  const selected = useMemo(() => {
    return (
      offers.find((o) => o.package_id === packageId) ||
      offers.find((o) => o.package_id === "bot_business") ||
      offers[0] ||
      null
    );
  }, [offers, packageId]);

  const channelAddonEur = useMemo(() => {
    if (channels.length <= 1) return 0;
    return channels.slice(1).reduce((sum, id) => {
      const meta = CHANNELS.find((c) => c.id === id);
      return sum + (meta?.addonEur || 149);
    }, 0);
  }, [channels]);

  const toggleChannel = useCallback((id: ChannelId, available: boolean) => {
    if (!available) {
      setChannelInterest((prev) =>
        prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
      );
      return;
    }
    setChannels((prev) => {
      if (prev.includes(id)) {
        if (prev.length === 1) return prev;
        return prev.filter((x) => x !== id);
      }
      return [...prev, id];
    });
  }, []);

  const toggleList = useCallback(
    (id: string, list: string[], setList: (v: string[]) => void) => {
      setList(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
    },
    [],
  );

  const toggleKnowledge = useCallback((id: string) => {
    setKnowledge((prev) => {
      if (id === "later") return ["later"];
      const withoutLater = prev.filter((x) => x !== "later");
      if (withoutLater.includes(id)) {
        const next = withoutLater.filter((x) => x !== id);
        return next.length ? next : ["later"];
      }
      return [...withoutLater, id];
    });
  }, []);

  const toggleHandoff = useCallback((id: string) => {
    setHandoff((prev) => {
      if (id === "never") return ["never"];
      const withoutNever = prev.filter((x) => x !== "never");
      if (withoutNever.includes(id)) {
        const next = withoutNever.filter((x) => x !== id);
        return next.length ? next : ["when_asks_manager"];
      }
      return [...withoutNever, id];
    });
  }, []);

  function validateStep(s: number): string {
    if (s === 1 && channels.length < 1) {
      return "Выберите хотя бы одну доступную интеграцию (Telegram или Website Chat).";
    }
    if (s === 2) {
      if (!businessName.trim()) return "Укажите название компании.";
      if (!activity.trim()) return "Укажите вид деятельности.";
    }
    if (s === 3 && capabilities.length < 1) {
      return "Выберите хотя бы одну задачу бота.";
    }
    if (s === 4 && knowledge.length < 1) {
      return "Укажите источник знаний или «Пока не загружать».";
    }
    if (s === 5) {
      if (languages.length < 1) return "Выберите хотя бы один язык.";
      if (handoff.length < 1) return "Укажите правила передачи оператору.";
    }
    if (s === 6 && !email.trim()) return "Укажите email для заказа и оплаты.";
    return "";
  }

  async function goNext() {
    const err = validateStep(step);
    if (err) {
      setError(err);
      return;
    }
    setError("");
    setStep((x) => Math.min(6, x + 1));
  }

  async function submit() {
    const err = validateStep(6);
    if (err) {
      setError(err);
      return;
    }
    if (!selected) {
      setError("Пакет бота не загружен. Обновите страницу.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/sales/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: businessName.trim(),
          description: activity.trim() || "AI Business Bot",
          company_website: website.trim() || null,
          email: email.trim(),
          phone: phone.trim() || null,
          package_id: selected.package_id,
          purchase_type: "subscription",
          product_kind: "bot",
          market_code: market,
          visitor_id: getVisitorId("public"),
          niche: activity.trim() || null,
          bot_config: {
            channels,
            channels_interest: channelInterest,
            capabilities,
            extras,
            knowledge_sources: knowledge,
            handoff_rules: handoff,
            languages,
            activity: activity.trim(),
            country: country.trim() || market,
            reply_language: languages[0],
          },
          extra_wishes: [
            `Channels: ${channels.join(", ")}`,
            channelInterest.length
              ? `Interest (Coming Soon): ${channelInterest.join(", ")}`
              : "",
            `Capabilities: ${capabilities.join(", ")}`,
            `Knowledge: ${knowledge.join(", ")}`,
            `Handoff: ${handoff.join(", ")}`,
            `Languages: ${languages.join(", ")}`,
            `Extras: ${extras.join(", ")}`,
          ]
            .filter(Boolean)
            .join("\n"),
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(formatApiDetail(body.detail) || "Не удалось создать заказ бота");
        return;
      }
      setDone({
        order_id: body.order_id,
        package_name: body.package_name,
        price_label: body.price_label,
        price_eur: body.price_eur,
      });
    } catch {
      setError("Сеть недоступна. Попробуйте ещё раз.");
    } finally {
      setBusy(false);
    }
  }

  async function pay() {
    if (!done?.order_id) return;
    setBusy(true);
    setError("");
    try {
      const url = await startOrderCheckout(done.order_id);
      window.location.href = url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Оплата недоступна");
      setBusy(false);
    }
  }

  return (
    <>
      <header className="space-y-2 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-300/90">
          {BRAND_NAME} · AI Bot
        </p>
        <h1 className="text-3xl font-bold text-white">Заказ AI Business Bot</h1>
        <p className="text-sm text-genesis-muted">
          Отдельный продукт — не форма заказа сайта. Первый канал входит в тариф; каждый
          дополнительный — отдельная оплата. Позже: «Добавить канал» к этому же боту, без
          нового проекта.
        </p>
        <p className="text-sm">
          <Link href="/site?service=bots" className="text-emerald-300 hover:underline">
            ← К пакетам ботов
          </Link>
          {" · "}
          <Link href="/order" className="text-zinc-400 hover:underline">
            Нужен сайт?
          </Link>
        </p>
      </header>

      {!done ? (
        <>
          <nav className="flex flex-wrap gap-2 justify-center">
            {STEPS.map((label, i) => {
              const n = i + 1;
              const active = step === n;
              return (
                <button
                  key={label}
                  type="button"
                  disabled={n > step}
                  onClick={() => n <= step && setStep(n)}
                  className={`rounded-full px-3 py-1 text-xs ${
                    active
                      ? "bg-emerald-500 text-black"
                      : n < step
                        ? "border border-emerald-500/40 text-emerald-200"
                        : "border border-white/10 text-zinc-500"
                  }`}
                >
                  {n}. {label}
                </button>
              );
            })}
          </nav>

          {error ? (
            <p className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              {error}
            </p>
          ) : null}

          <section className="rounded-2xl border border-white/10 bg-black/30 p-5 space-y-4">
            {step === 1 && (
              <>
                <h2 className="text-lg font-semibold text-white">Подключить</h2>
                <p className="text-sm text-genesis-muted">
                  Доступные каналы можно заказать сейчас. Coming Soon — интерес на будущее;
                  когда откроются, добавите к этому же AI Bot кнопкой «Добавить канал».
                </p>
                <ul className="space-y-2">
                  {CHANNELS.map((ch) => {
                    const checked = ch.available
                      ? channels.includes(ch.id)
                      : channelInterest.includes(ch.id);
                    const isExtra =
                      ch.available &&
                      channels.includes(ch.id) &&
                      channels[0] !== ch.id &&
                      channels.length > 1;
                    return (
                      <li key={ch.id}>
                        <label
                          className={`flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-3 ${
                            checked
                              ? "border-emerald-400/50 bg-emerald-500/10"
                              : "border-white/10"
                          } ${!ch.available ? "opacity-80" : ""}`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleChannel(ch.id, ch.available)}
                          />
                          <span className="text-white">{ch.label}</span>
                          {ch.available && channels.includes(ch.id) && channels[0] === ch.id ? (
                            <span className="ml-auto text-xs text-emerald-200">✔ в тарифе</span>
                          ) : null}
                          {isExtra ? (
                            <span className="ml-auto text-xs text-amber-200">
                              +{ch.addonEur} € setup
                            </span>
                          ) : null}
                          {!ch.available ? (
                            <span className="ml-auto text-xs text-amber-200/90">
                              Coming Soon · ➕ позже
                            </span>
                          ) : null}
                        </label>
                      </li>
                    );
                  })}
                </ul>
                {channelAddonEur > 0 ? (
                  <p className="text-sm text-amber-100">
                    Доп. каналы сейчас: +{channelAddonEur} € к setup (каждый канал платный).
                  </p>
                ) : null}
              </>
            )}

            {step === 2 && (
              <>
                <h2 className="text-lg font-semibold text-white">Информация о компании</h2>
                <label className="block text-sm text-genesis-muted">
                  Название компании *
                  <input
                    className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                    value={businessName}
                    onChange={(e) => setBusinessName(e.target.value)}
                  />
                </label>
                <label className="block text-sm text-genesis-muted">
                  Вид деятельности *
                  <input
                    className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                    value={activity}
                    onChange={(e) => setActivity(e.target.value)}
                    placeholder="автосервис, клиника, салон…"
                  />
                </label>
                <label className="block text-sm text-genesis-muted">
                  Сайт (если есть)
                  <input
                    className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://"
                  />
                </label>
                <label className="block text-sm text-genesis-muted">
                  Страна
                  <input
                    className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                  />
                </label>
              </>
            )}

            {step === 3 && (
              <>
                <h2 className="text-lg font-semibold text-white">Что должен делать бот?</h2>
                <ul className="space-y-2">
                  {CAPABILITIES.map((c) => (
                    <li key={c.id}>
                      <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 px-3 py-3">
                        <input
                          type="checkbox"
                          checked={capabilities.includes(c.id)}
                          onChange={() =>
                            toggleList(c.id, capabilities, setCapabilities)
                          }
                        />
                        <span className="text-white">{c.label}</span>
                      </label>
                    </li>
                  ))}
                </ul>
                <h3 className="pt-2 text-sm font-medium text-zinc-300">Дополнительно</h3>
                <ul className="space-y-2">
                  {EXTRAS.map((c) => (
                    <li key={c.id}>
                      <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 px-3 py-3">
                        <input
                          type="checkbox"
                          checked={extras.includes(c.id)}
                          onChange={() => toggleList(c.id, extras, setExtras)}
                        />
                        <span className="text-white">{c.label}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </>
            )}

            {step === 4 && (
              <>
                <h2 className="text-lg font-semibold text-white">Knowledge Base</h2>
                <p className="text-sm text-genesis-muted">
                  Откуда бот должен получать информацию?
                </p>
                <ul className="space-y-2">
                  {KNOWLEDGE.map((c) => (
                    <li key={c.id}>
                      <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 px-3 py-3">
                        <input
                          type="checkbox"
                          checked={knowledge.includes(c.id)}
                          onChange={() => toggleKnowledge(c.id)}
                        />
                        <span className="text-white">{c.label}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </>
            )}

            {step === 5 && (
              <>
                <h2 className="text-lg font-semibold text-white">Языки</h2>
                <ul className="space-y-2">
                  {LANGUAGES.map((c) => (
                    <li key={c.id}>
                      <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 px-3 py-3">
                        <input
                          type="checkbox"
                          checked={languages.includes(c.id)}
                          onChange={() => toggleList(c.id, languages, setLanguages)}
                        />
                        <span className="text-white">{c.label}</span>
                      </label>
                    </li>
                  ))}
                </ul>
                <h2 className="pt-4 text-lg font-semibold text-white">
                  Передача оператору
                </h2>
                <p className="text-sm text-genesis-muted">
                  Когда бот должен передавать разговор человеку?
                </p>
                <ul className="space-y-2">
                  {HANDOFF.map((c) => (
                    <li key={c.id}>
                      <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 px-3 py-3">
                        <input
                          type="checkbox"
                          checked={handoff.includes(c.id)}
                          onChange={() => toggleHandoff(c.id)}
                        />
                        <span className="text-white">{c.label}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </>
            )}

            {step === 6 && (
              <>
                <h2 className="text-lg font-semibold text-white">Итог заказа</h2>
                {loadingOffers ? (
                  <p className="text-sm text-genesis-muted">Загрузка тарифа…</p>
                ) : (
                  <div className="space-y-3 text-sm text-zinc-200">
                    <p>
                      <strong className="text-white">Тариф:</strong>{" "}
                      {selected?.name || packageId} · {selected?.price_label || "—"}
                      {channelAddonEur > 0
                        ? ` + ${channelAddonEur} € доп. каналы`
                        : ""}
                    </p>
                    <p>
                      <strong className="text-white">Интеграции:</strong>{" "}
                      {channels
                        .map((id) => CHANNELS.find((c) => c.id === id)?.label || id)
                        .join(", ")}
                    </p>
                    {channelInterest.length > 0 ? (
                      <p className="text-amber-200/90">
                        Интерес (➕ позже):{" "}
                        {channelInterest
                          .map((id) => CHANNELS.find((c) => c.id === id)?.label || id)
                          .join(", ")}
                      </p>
                    ) : null}
                    <p>
                      <strong className="text-white">Knowledge:</strong>{" "}
                      {knowledge
                        .map((id) => KNOWLEDGE.find((c) => c.id === id)?.label || id)
                        .join("; ")}
                    </p>
                    <p>
                      <strong className="text-white">Языки:</strong>{" "}
                      {languages
                        .map((id) => LANGUAGES.find((c) => c.id === id)?.label || id)
                        .join(", ")}
                    </p>
                    <p>
                      <strong className="text-white">Эскалация:</strong>{" "}
                      {handoff
                        .map((id) => HANDOFF.find((c) => c.id === id)?.label || id)
                        .join("; ")}
                    </p>
                    <p>
                      <strong className="text-white">Задачи:</strong>{" "}
                      {capabilities
                        .map((id) => CAPABILITIES.find((c) => c.id === id)?.label || id)
                        .join("; ")}
                    </p>
                    <p>
                      <strong className="text-white">Компания:</strong> {businessName} ·{" "}
                      {activity}
                    </p>
                    <label className="block text-sm text-genesis-muted pt-2">
                      Тариф
                      <select
                        className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                        value={packageId}
                        onChange={(e) => setPackageId(e.target.value)}
                      >
                        {(offers.length
                          ? offers
                          : [
                              {
                                package_id: "bot_starter",
                                name: "AI Bot Starter",
                                price_label: "—",
                              },
                              {
                                package_id: "bot_business",
                                name: "AI Bot Business",
                                price_label: "—",
                              },
                              {
                                package_id: "bot_professional",
                                name: "AI Bot Professional",
                                price_label: "—",
                              },
                            ]
                        ).map((o) => (
                          <option key={o.package_id} value={o.package_id}>
                            {o.name} · {o.price_label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block text-sm text-genesis-muted">
                      Email *
                      <input
                        type="email"
                        className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                    </label>
                    <label className="block text-sm text-genesis-muted">
                      Телефон
                      <input
                        className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                      />
                    </label>
                  </div>
                )}
              </>
            )}

            <div className="flex flex-wrap gap-3 pt-2">
              {step > 1 ? (
                <button
                  type="button"
                  className="rounded-xl border border-white/20 px-4 py-2 text-sm text-white"
                  onClick={() => {
                    setError("");
                    setStep((s) => Math.max(1, s - 1));
                  }}
                >
                  Назад
                </button>
              ) : null}
              {step < 6 ? (
                <button
                  type="button"
                  className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
                  onClick={() => void goNext()}
                >
                  Далее
                </button>
              ) : (
                <button
                  type="button"
                  disabled={busy}
                  className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-60"
                  onClick={() => void submit()}
                >
                  {busy ? "Создаём…" : "Подтвердить заказ"}
                </button>
              )}
            </div>
          </section>
        </>
      ) : (
        <section className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6 space-y-4 text-center">
          <h2 className="text-xl font-semibold text-white">Заказ бота создан</h2>
          <p className="text-sm text-zinc-200">
            {done.package_name} · {done.price_label || `${done.price_eur} €`}
          </p>
          <p className="text-xs text-genesis-muted">
            ID: {done.order_id} · позже: добавить канал к этому же боту (платно)
          </p>
          <button
            type="button"
            disabled={busy}
            className="rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-black"
            onClick={() => void pay()}
          >
            Перейти к оплате
          </button>
          <p>
            <Link
              href={`/order/status/${done.order_id}`}
              className="text-sm text-emerald-300 hover:underline"
            >
              Статус заказа
            </Link>
          </p>
        </section>
      )}
    </>
  );
}
