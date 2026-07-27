"use client";

/**
 * AI Digital Employee order wizard:
 * Package → Register → Company/AI → Channels → Pay → Connect (Dashboard).
 */

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PublicPageShell } from "../../components/PublicPageShell";
import { BRAND_NAME } from "../../lib/publicBrand";
import {
  clientAuthHeaders,
  getClientToken,
  setClientSession,
} from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { startOrderCheckout } from "../../lib/orderCheckout";
import { publicApiBase } from "../../lib/publicApiBase";
import { getVisitorId } from "../../lib/visitorId";
import { BotChannelIconRow } from "../../components/ChannelBrandIcons";
import {
  IconInstagram,
  IconMessenger,
  IconTelegram,
  IconWebsite,
  IconWhatsApp,
} from "../../components/ChannelBrandIcons";

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
  includes_ru?: string[];
  max_bots?: number | null;
  max_bots_label?: string;
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
  note: string;
  Icon: typeof IconTelegram;
}[] = [
  {
    id: "website_chat",
    label: "Website Chat",
    available: true,
    note: "Connect after pay",
    Icon: IconWebsite,
  },
  {
    id: "telegram",
    label: "Telegram",
    available: true,
    note: "Own bot token after pay",
    Icon: IconTelegram,
  },
  {
    id: "whatsapp",
    label: "WhatsApp",
    available: false,
    note: "Meta OAuth after pay",
    Icon: IconWhatsApp,
  },
  {
    id: "instagram",
    label: "Instagram",
    available: false,
    note: "Meta OAuth after pay",
    Icon: IconInstagram,
  },
  {
    id: "facebook_messenger",
    label: "Messenger",
    available: false,
    note: "Meta OAuth after pay",
    Icon: IconMessenger,
  },
];

const STEPS = [
  "Пакет",
  "Аккаунт",
  "Компания и AI",
  "Каналы",
  "Оплата",
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

  const [channels, setChannels] = useState<ChannelId[]>(["telegram", "website_chat"]);
  const [channelInterest, setChannelInterest] = useState<ChannelId[]>([]);

  const [businessName, setBusinessName] = useState("");
  const [activity, setActivity] = useState("");
  const [services, setServices] = useState("");
  const [faq, setFaq] = useState("");
  const [aiInstructions, setAiInstructions] = useState("");
  const [botDisplayName, setBotDisplayName] = useState("");
  const [tone, setTone] = useState("friendly");
  const [languages, setLanguages] = useState<string[]>(["de", "ru"]);
  const [website, setWebsite] = useState("");
  const [country, setCountry] = useState("");

  const [authMode, setAuthMode] = useState<"login" | "register">("register");
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authCode, setAuthCode] = useState("");
  const [awaitingCode, setAwaitingCode] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [clientEmail, setClientEmail] = useState("");

  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState<{
    order_id: string;
    package_name: string;
    price_label?: string;
  } | null>(null);

  useEffect(() => {
    const pkg = normalizePackageId(search.get("package"));
    const m = (search.get("market") || "DE").toUpperCase();
    setPackageId(pkg);
    setMarket(m);
    setCountry(m);
    setLoggedIn(Boolean(getClientToken()));
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

  // Restore Workspace draft when authenticated
  useEffect(() => {
    if (!getClientToken()) return;
    let cancelled = false;
    fetch(`${API}/api/client/bots/order-draft`, {
      headers: { ...clientAuthHeaders() },
      cache: "no-store",
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        if (cancelled || !body?.draft) return;
        const d = body.draft as Record<string, unknown>;
        if (typeof d.package_id === "string") setPackageId(normalizePackageId(d.package_id));
        if (typeof d.business_name === "string") setBusinessName(d.business_name);
        if (typeof d.activity === "string") setActivity(d.activity);
        if (typeof d.services === "string") setServices(d.services);
        if (typeof d.faq === "string") setFaq(d.faq);
        if (typeof d.ai_instructions === "string") setAiInstructions(d.ai_instructions);
        if (typeof d.bot_display_name === "string") setBotDisplayName(d.bot_display_name);
        if (typeof d.tone === "string") setTone(d.tone);
        if (typeof d.website === "string") setWebsite(d.website);
        if (typeof d.email === "string") setEmail(d.email);
        if (typeof d.phone === "string") setPhone(d.phone);
        if (Array.isArray(d.languages)) setLanguages(d.languages.map(String));
        if (Array.isArray(d.channels)) {
          setChannels(d.channels.filter((c): c is ChannelId =>
            CHANNELS.some((m) => m.id === c && m.available),
          ) as ChannelId[]);
        }
        if (Array.isArray(d.channel_interest)) {
          setChannelInterest(d.channel_interest.map(String) as ChannelId[]);
        }
        if (typeof d.step === "number" && d.step >= 1 && d.step <= 5) setStep(d.step);
        setLoggedIn(true);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(() => {
    return (
      offers.find((o) => o.package_id === packageId) ||
      offers.find((o) => o.package_id === "bot_business") ||
      offers[0] ||
      null
    );
  }, [offers, packageId]);

  const draftPayload = useCallback(() => {
    return {
      step,
      package_id: packageId,
      market,
      business_name: businessName,
      activity,
      services,
      faq,
      ai_instructions: aiInstructions,
      bot_display_name: botDisplayName,
      tone,
      languages,
      website,
      email,
      phone,
      channels: [...channels, ...channelInterest],
      channel_interest: channelInterest,
      country,
    };
  }, [
    step,
    packageId,
    market,
    businessName,
    activity,
    services,
    faq,
    aiInstructions,
    botDisplayName,
    tone,
    languages,
    website,
    email,
    phone,
    channels,
    channelInterest,
    country,
  ]);

  const persistDraft = useCallback(async () => {
    if (!getClientToken()) return;
    try {
      await fetch(`${API}/api/client/bots/order-draft`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...clientAuthHeaders(),
        },
        body: JSON.stringify({ draft: draftPayload() }),
      });
    } catch {
      /* best-effort */
    }
  }, [draftPayload]);

  useEffect(() => {
    if (!loggedIn || step < 2) return;
    const t = setTimeout(() => {
      void persistDraft();
    }, 600);
    return () => clearTimeout(t);
  }, [loggedIn, step, persistDraft]);

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

  function validateStep(s: number): string {
    if (s === 1 && !packageId) return "Выберите пакет.";
    if (s === 2 && !getClientToken()) {
      return "Войдите или зарегистрируйте Workspace — оплата только для аккаунта.";
    }
    if (s === 3) {
      if (!businessName.trim()) return "Укажите название компании.";
      if (!activity.trim()) return "Укажите нишу / вид деятельности.";
      if (!botDisplayName.trim()) return "Укажите имя цифрового сотрудника.";
      if (languages.length < 1) return "Выберите хотя бы один язык.";
    }
    if (s === 4 && channels.length < 1) {
      return "Выберите хотя бы один доступный канал.";
    }
    if (s === 5) {
      const mail = (email || clientEmail || authEmail).trim();
      if (!mail.includes("@")) return "Укажите email для чека.";
    }
    return "";
  }

  async function goNext() {
    const err = validateStep(step);
    if (err) {
      setError(err);
      return;
    }
    setError("");
    await persistDraft();
    setStep((s) => Math.min(5, s + 1));
  }

  async function handleRegisterStart() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/client/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: authName.trim(),
          email: authEmail.trim(),
          password: authPassword,
          locale: "ru",
          country: country || market,
          visitor_id: getVisitorId(),
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Не удалось начать регистрацию");
      }
      setAwaitingCode(true);
      setClientEmail(authEmail.trim());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка регистрации");
    } finally {
      setBusy(false);
    }
  }

  async function handleRegisterConfirm() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/client/register/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail.trim(), code: authCode.trim() }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Неверный код");
      }
      const token = String(body.token || body.access_token || "");
      if (!token) throw new Error("Нет токена сессии");
      setClientSession(token, body.name || authName);
      setLoggedIn(true);
      setEmail(authEmail.trim());
      setAwaitingCode(false);
      await persistDraft();
      setStep(3);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка подтверждения");
    } finally {
      setBusy(false);
    }
  }

  async function handleLogin() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/client/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: authEmail.trim(),
          password: authPassword,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Не удалось войти");
      }
      const token = String(body.token || body.access_token || "");
      if (!token) throw new Error("Нет токена сессии");
      setClientSession(token, body.name);
      setLoggedIn(true);
      setClientEmail(authEmail.trim());
      setEmail(authEmail.trim());
      await persistDraft();
      setStep(3);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка входа");
    } finally {
      setBusy(false);
    }
  }

  async function submitAndPay() {
    const err = validateStep(5);
    if (err) {
      setError(err);
      return;
    }
    if (!getClientToken()) {
      setError("Сначала войдите в Workspace.");
      setStep(2);
      return;
    }
    setBusy(true);
    setError("");
    try {
      await persistDraft();
      const allChannels = [...new Set([...channels, ...channelInterest])];
      const description = [
        activity.trim(),
        services.trim() && `Услуги: ${services.trim()}`,
        aiInstructions.trim() && `Задачи бота: ${aiInstructions.trim()}`,
      ]
        .filter(Boolean)
        .join(". ")
        .slice(0, 2000);

      const res = await fetch(`${API}/api/sales/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...clientAuthHeaders(),
        },
        body: JSON.stringify({
          business_name: businessName.trim(),
          description: description || activity.trim() || "AI Digital Employee",
          email: (email || clientEmail || authEmail).trim(),
          phone: phone.trim() || undefined,
          company_website: website.trim() || undefined,
          package_id: packageId,
          product_kind: "bot",
          market_code: market,
          ui_lang: "ru",
          visitor_id: getVisitorId(),
          bot_config: {
            channels: allChannels,
            languages,
            tone,
            bot_display_name: botDisplayName.trim(),
            faq: faq.trim(),
            ai_instructions: aiInstructions.trim(),
            activity: activity.trim(),
            country: country || market,
            capabilities: ["consult", "faq", "leads", "always_on"],
            extras: ["ai_enabled", "company_training"],
            knowledge_sources: website.trim() ? ["website", "faq"] : ["faq", "manual_text"],
            handoff_rules: ["when_asks_manager", "when_unknown"],
          },
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Не удалось создать заказ");
      }
      const orderId = String(body.order_id || "");
      setDone({
        order_id: orderId,
        package_name: String(body.package_name || selected?.name || "AI Digital Employee"),
        price_label: body.price_label,
      });
      const url = await startOrderCheckout(orderId, {
        successPath: `/client/bots/setup?order=${encodeURIComponent(orderId)}&paid=1`,
        cancelPath: `/order/bot?package=${encodeURIComponent(packageId)}&canceled=1`,
      });
      window.location.href = url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка оплаты");
      setBusy(false);
    }
  }

  return (
    <>
      <header className="space-y-2 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-200/90">
          {BRAND_NAME}
        </p>
        <h1 className="text-3xl font-semibold text-white">AI Digital Employee</h1>
        <p className="text-sm text-genesis-muted">
          AI Sales Assistant for your company. Package → Workspace → setup → pay →
          connect your own channels.
        </p>
      </header>

      <ol className="flex flex-wrap justify-center gap-2 text-xs">
        {STEPS.map((label, i) => {
          const n = i + 1;
          const active = step === n;
          return (
            <li
              key={label}
              className={`rounded-full px-3 py-1 ${
                active
                  ? "bg-emerald-500/20 text-emerald-200"
                  : n < step
                    ? "bg-white/10 text-zinc-300"
                    : "bg-white/5 text-zinc-500"
              }`}
            >
              {n}. {label}
            </li>
          );
        })}
      </ol>

      {error ? (
        <p className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
          {error}
        </p>
      ) : null}

      {done ? (
        <div className="space-y-3 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6 text-center">
          <p className="text-lg font-semibold text-white">Переход к оплате…</p>
          <p className="text-sm text-zinc-300">
            Заказ {done.order_id} · {done.package_name}
            {done.price_label ? ` · ${done.price_label}` : ""}
          </p>
          <Link href={`/client/bots/setup?order=${done.order_id}`} className="text-emerald-300 underline">
            Открыть кабинет ботов
          </Link>
        </div>
      ) : null}

      {!done && step === 1 ? (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-white">1. Выберите пакет</h2>
          <p className="text-sm text-zinc-400">
            Лимит тарифа — число независимых AI-ботов, не каналов. Как это работает: после оплаты
            подключите свои Telegram / Meta аккаунты в личном кабинете.
          </p>
          <BotChannelIconRow />
          <label className="block text-sm text-zinc-400">
            Рынок
            <select
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
              value={market}
              onChange={(e) => setMarket(e.target.value.toUpperCase())}
            >
              {["DE", "AT", "CH", "US", "GB", "UA", "RU"].map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          {loadingOffers ? (
            <p className="text-sm text-zinc-500">Загрузка пакетов…</p>
          ) : (
            <div className="grid gap-3">
              {offers.map((pkg) => {
                const active = pkg.package_id === packageId;
                return (
                  <button
                    key={pkg.package_id}
                    type="button"
                    onClick={() => setPackageId(pkg.package_id)}
                    className={`rounded-2xl border p-4 text-left transition ${
                      active
                        ? "border-emerald-400/50 bg-emerald-500/10"
                        : "border-white/10 bg-white/[0.03] hover:border-white/25"
                    }`}
                  >
                    <p className="font-semibold text-white">{pkg.name}</p>
                    <p className="mt-1 text-emerald-200">
                      {pkg.setup_label || pkg.price_label}
                      {pkg.monthly_label ? ` · затем ${pkg.monthly_label}/мес` : ""}
                    </p>
                    {pkg.max_bots_label ? (
                      <p className="mt-2 text-xs text-zinc-400">{pkg.max_bots_label}</p>
                    ) : null}
                    <ul className="mt-2 space-y-1 text-xs text-zinc-500">
                      {(pkg.includes_ru || []).slice(0, 4).map((line) => (
                        <li key={line}>• {line}</li>
                      ))}
                    </ul>
                  </button>
                );
              })}
            </div>
          )}
        </section>
      ) : null}

      {!done && step === 2 ? (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-white">2. Workspace</h2>
          <p className="text-sm text-zinc-400">
            Регистрация до оплаты обязательна — заказ привязывается к вашему Workspace.
          </p>
          {loggedIn ? (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">
              Вы вошли. Можно продолжить настройку.
              <div className="mt-3">
                <button
                  type="button"
                  className="rounded-xl bg-emerald-500 px-4 py-2 font-semibold text-black"
                  onClick={() => void goNext()}
                >
                  Далее →
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex gap-2 text-sm">
                <button
                  type="button"
                  className={`rounded-lg px-3 py-1.5 ${
                    authMode === "register" ? "bg-white/15 text-white" : "text-zinc-400"
                  }`}
                  onClick={() => {
                    setAuthMode("register");
                    setAwaitingCode(false);
                  }}
                >
                  Регистрация
                </button>
                <button
                  type="button"
                  className={`rounded-lg px-3 py-1.5 ${
                    authMode === "login" ? "bg-white/15 text-white" : "text-zinc-400"
                  }`}
                  onClick={() => {
                    setAuthMode("login");
                    setAwaitingCode(false);
                  }}
                >
                  Вход
                </button>
              </div>
              {authMode === "register" && !awaitingCode ? (
                <div className="space-y-3">
                  <input
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                    placeholder="Имя"
                    value={authName}
                    onChange={(e) => setAuthName(e.target.value)}
                  />
                  <input
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                    placeholder="Email"
                    type="email"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                  />
                  <input
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                    placeholder="Пароль (от 8 символов)"
                    type="password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void handleRegisterStart()}
                    className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black disabled:opacity-50"
                  >
                    Получить код на email
                  </button>
                </div>
              ) : null}
              {authMode === "register" && awaitingCode ? (
                <div className="space-y-3">
                  <p className="text-sm text-zinc-300">Код отправлен на {authEmail}</p>
                  <input
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                    placeholder="Код из письма"
                    value={authCode}
                    onChange={(e) => setAuthCode(e.target.value)}
                  />
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void handleRegisterConfirm()}
                    className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black disabled:opacity-50"
                  >
                    Подтвердить и продолжить
                  </button>
                </div>
              ) : null}
              {authMode === "login" ? (
                <div className="space-y-3">
                  <input
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                    placeholder="Email"
                    type="email"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                  />
                  <input
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                    placeholder="Пароль"
                    type="password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void handleLogin()}
                    className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black disabled:opacity-50"
                  >
                    Войти
                  </button>
                </div>
              ) : null}
              <p className="text-xs text-zinc-500">
                Уже есть кабинет?{" "}
                <Link href="/client/login" className="text-emerald-300 underline">
                  /client/login
                </Link>
              </p>
            </>
          )}
        </section>
      ) : null}

      {!done && step === 3 ? (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-white">3. Компания и AI</h2>
          <input
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="Название компании *"
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="Ниша / вид деятельности *"
            value={activity}
            onChange={(e) => setActivity(e.target.value)}
          />
          <textarea
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="Услуги (кратко)"
            rows={2}
            value={services}
            onChange={(e) => setServices(e.target.value)}
          />
          <textarea
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="FAQ / типичные вопросы"
            rows={3}
            value={faq}
            onChange={(e) => setFaq(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="Имя цифрового сотрудника *"
            value={botDisplayName}
            onChange={(e) => setBotDisplayName(e.target.value)}
          />
          <textarea
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="Что должен делать бот"
            rows={3}
            value={aiInstructions}
            onChange={(e) => setAiInstructions(e.target.value)}
          />
          <label className="block text-sm text-zinc-400">
            Тон
            <select
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
            >
              <option value="friendly">Дружелюбный</option>
              <option value="professional">Деловой</option>
              <option value="concise">Краткий</option>
            </select>
          </label>
          <div className="flex flex-wrap gap-2">
            {[
              ["de", "DE"],
              ["ru", "RU"],
              ["en", "EN"],
              ["uk", "UK"],
            ].map(([id, label]) => {
              const on = languages.includes(id);
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() =>
                    setLanguages((prev) =>
                      on ? prev.filter((x) => x !== id) : [...prev, id],
                    )
                  }
                  className={`rounded-lg px-3 py-1.5 text-sm ${
                    on ? "bg-sky-500/30 text-sky-100" : "bg-white/5 text-zinc-400"
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
          <input
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="Сайт компании (если есть)"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
          />
        </section>
      ) : null}

      {!done && step === 4 ? (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-white">4. Каналы</h2>
          <p className="text-sm text-zinc-400">
            Каналы не ограничивают тариф. После оплаты подключите свои аккаунты.
          </p>
          <div className="grid gap-2">
            {CHANNELS.map((ch) => {
              const selectedCh = ch.available
                ? channels.includes(ch.id)
                : channelInterest.includes(ch.id);
              return (
                <button
                  key={ch.id}
                  type="button"
                  onClick={() => toggleChannel(ch.id, ch.available)}
                  className={`flex items-center justify-between rounded-xl border px-4 py-3 text-left ${
                    selectedCh
                      ? "border-emerald-400/40 bg-emerald-500/10"
                      : "border-white/10 bg-white/[0.03]"
                  }`}
                >
                  <span className="flex items-start gap-3">
                    <ch.Icon
                      className={`mt-0.5 h-6 w-6 shrink-0 ${
                        ch.id === "telegram"
                          ? "text-[#2AABEE]"
                          : ch.id === "whatsapp"
                            ? "text-[#25D366]"
                            : ch.id === "instagram"
                              ? "text-[#E4405F]"
                              : ch.id === "facebook_messenger"
                                ? "text-[#0084FF]"
                                : "text-emerald-300"
                      }`}
                      title={ch.label}
                    />
                    <span>
                      <span className="font-medium text-white">{ch.label}</span>
                      <span className="mt-0.5 block text-xs text-zinc-500">{ch.note}</span>
                    </span>
                  </span>
                  <span className="text-xs text-zinc-400">
                    {ch.available ? (selectedCh ? "✓" : "") : "скоро"}
                  </span>
                </button>
              );
            })}
          </div>
        </section>
      ) : null}

      {!done && step === 5 ? (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-white">5. Итог и оплата</h2>
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-zinc-300">
            <p>
              <strong className="text-white">{selected?.name || packageId}</strong>
            </p>
            <p className="mt-1 text-emerald-200">
              {selected?.setup_label || selected?.price_label}
              {selected?.monthly_label ? ` · ${selected.monthly_label}/мес` : ""}
            </p>
            <p className="mt-3">Компания: {businessName || "—"}</p>
            <p>Сотрудник: {botDisplayName || "—"}</p>
            <p>
              Каналы: {[...channels, ...channelInterest].join(", ") || "—"}
            </p>
          </div>
          <input
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="Email для чека *"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
            placeholder="Телефон (необязательно)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <button
            type="button"
            disabled={busy}
            onClick={() => void submitAndPay()}
            className="w-full rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-black disabled:opacity-50"
          >
            {busy ? "Создаём заказ…" : "Оплатить через Stripe"}
          </button>
        </section>
      ) : null}

      {!done && step !== 2 ? (
        <div className="flex justify-between gap-3 pt-2">
          <button
            type="button"
            disabled={step <= 1 || busy}
            onClick={() => {
              setError("");
              setStep((s) => Math.max(1, s - 1));
            }}
            className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 disabled:opacity-40"
          >
            ← Назад
          </button>
          {step < 5 ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void goNext()}
              className="rounded-xl bg-white/10 px-4 py-2 text-sm font-medium text-white hover:bg-white/15"
            >
              Далее →
            </button>
          ) : null}
        </div>
      ) : null}

      {step === 2 && !loggedIn ? (
        <div className="pt-2">
          <button
            type="button"
            onClick={() => setStep(1)}
            className="text-sm text-zinc-400 underline"
          >
            ← К выбору пакета
          </button>
        </div>
      ) : null}
    </>
  );
}
