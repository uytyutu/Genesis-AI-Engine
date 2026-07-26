"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Field, Input, Textarea } from "./ui";
import {
  PortalApiError,
  portalFetch,
  portalFetchAllow404,
} from "../lib/portalApi";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

const DEMO_EMAIL = "client@virtus.local";
const DEMO_PASSWORD = "demo-vector";

type Step = "gate" | "form" | "preview" | "done";

type Answers = {
  business_name: string;
  what_company_does: string;
  services: string;
  answer_topics: string;
  avoid_topics: string;
  working_hours: string;
  address: string;
  phone: string;
  website: string;
  language: string;
  tone: string;
  industry: string;
  book_appointments: boolean;
  take_leads: boolean;
  give_prices: boolean;
  timezone: string;
};

type Preview = {
  greeting: string;
  system_prompt: string;
  note_ru?: string;
  capabilities?: Record<string, boolean>;
};

const EMPTY: Answers = {
  business_name: "",
  what_company_does: "",
  services: "",
  answer_topics: "",
  avoid_topics: "",
  working_hours: "Пн–Пт 09:00–18:00",
  address: "",
  phone: "",
  website: "",
  language: "de",
  tone: "professional_friendly",
  industry: "auto_service",
  book_appointments: true,
  take_leads: true,
  give_prices: false,
  timezone: "Europe/Berlin",
};

export function ChatbotSetupQuestionnaire() {
  const [step, setStep] = useState<Step>("gate");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [owned, setOwned] = useState(false);
  const [answers, setAnswers] = useState<Answers>(EMPTY);
  const [preview, setPreview] = useState<Preview | null>(null);

  const run = useCallback(async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (err) {
      if (err instanceof PortalApiError) setError(err.detail);
      else if (err instanceof Error) setError(err.message);
      else setError("unexpected_error");
    } finally {
      setBusy(false);
    }
  }, []);

  const refreshOwnership = useCallback(async () => {
    const products = await portalFetch<
      Array<{ product_type?: string; catalog_product_id?: string; product_id?: string }>
    >("/portal/my-products");
    const has = products.some(
      (p) =>
        p.product_type === "chatbot" ||
        p.catalog_product_id === "prod_chatbot" ||
        p.product_id === "prod_chatbot",
    );
    setOwned(has);
    return has;
  }, []);

  useEffect(() => {
    void run(async () => {
      try {
        const has = await refreshOwnership();
        const profile = await portalFetchAllow404<{
          business_name?: string;
          industry?: string;
          language?: string;
          timezone?: string;
          description?: string;
          initial_configuration?: { placeholders?: { setup_status?: string } };
        }>("/portal/chatbot/profile");
        if (profile?.business_name) {
          setAnswers((a) => ({
            ...a,
            business_name: profile.business_name || "",
            industry: profile.industry || a.industry,
            language: profile.language || a.language,
            timezone: profile.timezone || a.timezone,
            what_company_does: profile.description || a.what_company_does,
          }));
        }
        const published =
          profile?.initial_configuration?.placeholders?.setup_status ===
          "published";
        if (!has) {
          setStep("gate");
          return;
        }
        setStep(published ? "done" : "form");
      } catch (err) {
        if (err instanceof PortalApiError && err.status === 401) {
          setStep("gate");
          return;
        }
        throw err;
      }
    });
  }, [refreshOwnership, run]);

  const setField = <K extends keyof Answers>(key: K, value: Answers[K]) => {
    setAnswers((prev) => ({ ...prev, [key]: value }));
  };

  const loginAndBuy = () =>
    run(async () => {
      const res = await portalFetch<{ authenticated: boolean }>("/portal/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      if (!res.authenticated) throw new PortalApiError(401, "login_failed");
      let has = await refreshOwnership();
      if (!has) {
        try {
          await portalFetch("/portal/products/prod_chatbot/purchase", {
            method: "POST",
          });
        } catch {
          await portalFetch("/portal/products/prod_chatbot/activate", {
            method: "POST",
            body: JSON.stringify({ activation_code: "DEMO-CHATBOT" }),
          });
        }
        has = await refreshOwnership();
      }
      if (!has) throw new PortalApiError(400, "purchase_required");
      setStep("form");
    });

  const buildPreview = () =>
    run(async () => {
      if (!answers.business_name.trim()) {
        throw new PortalApiError(400, "business_name_required");
      }
      const body = await portalFetch<Preview>("/portal/chatbot/setup/preview", {
        method: "POST",
        body: JSON.stringify(answers),
      });
      setPreview(body);
      setStep("preview");
    });

  const publish = () =>
    run(async () => {
      const body = await portalFetch<Preview & { message_ru?: string }>(
        "/portal/chatbot/setup/publish",
        {
          method: "POST",
          body: JSON.stringify(answers),
        },
      );
      setPreview(body);
      setStep("done");
    });

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 px-1 py-2">
      <header className="space-y-2">
        <Badge>
          {BRAND_NAME} · {ASSISTANT_NAME}
        </Badge>
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Настройка цифрового сотрудника
        </h1>
        <p className="text-sm text-zinc-400">
          Анкета → превью → «Опубликовать». Без одобрения владельца Virtus — клиент
          делает сам.
        </p>
      </header>

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      {step === "gate" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-lg font-medium text-white">Заказ и вход</h2>
          <p className="text-sm text-zinc-400">
            Клиент входит и сразу покупает / активирует бота — без вашего Approve.
          </p>
          <Field label="Email">
            <Input value={email} onChange={(e) => setEmail(e.target.value)} />
          </Field>
          <Field label="Password">
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          <Button onClick={loginAndBuy} disabled={busy}>
            Войти и продолжить
          </Button>
          {owned ? (
            <p className="text-sm text-emerald-300">Продукт уже куплен.</p>
          ) : null}
        </section>
      ) : null}

      {step === "form" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-lg font-medium text-white">Анкета компании</h2>
          <Field label="Название компании">
            <Input
              value={answers.business_name}
              onChange={(e) => setField("business_name", e.target.value)}
              placeholder="Auto Müller"
            />
          </Field>
          <Field label="Чем занимается компания?">
            <Textarea
              value={answers.what_company_does}
              onChange={(e) => setField("what_company_does", e.target.value)}
              rows={3}
            />
          </Field>
          <Field label="Какие услуги оказывает?">
            <Textarea
              value={answers.services}
              onChange={(e) => setField("services", e.target.value)}
              rows={3}
            />
          </Field>
          <Field label="На какие вопросы бот должен отвечать?">
            <Textarea
              value={answers.answer_topics}
              onChange={(e) => setField("answer_topics", e.target.value)}
              rows={2}
            />
          </Field>
          <Field label="Какие вопросы бот не должен обсуждать?">
            <Textarea
              value={answers.avoid_topics}
              onChange={(e) => setField("avoid_topics", e.target.value)}
              rows={2}
            />
          </Field>
          <Field label="Часы работы">
            <Input
              value={answers.working_hours}
              onChange={(e) => setField("working_hours", e.target.value)}
            />
          </Field>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Адрес">
              <Input
                value={answers.address}
                onChange={(e) => setField("address", e.target.value)}
              />
            </Field>
            <Field label="Телефон">
              <Input
                value={answers.phone}
                onChange={(e) => setField("phone", e.target.value)}
              />
            </Field>
            <Field label="Сайт">
              <Input
                value={answers.website}
                onChange={(e) => setField("website", e.target.value)}
              />
            </Field>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Язык общения">
              <select
                className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
                value={answers.language}
                onChange={(e) => setField("language", e.target.value)}
              >
                <option value="de">Немецкий</option>
                <option value="ru">Русский</option>
                <option value="en">English</option>
                <option value="uk">Українська</option>
                <option value="pl">Polski</option>
              </select>
            </Field>
            <Field label="Тон общения">
              <select
                className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
                value={answers.tone}
                onChange={(e) => setField("tone", e.target.value)}
              >
                <option value="formal">Официальный</option>
                <option value="professional_friendly">Профессиональный + дружелюбный</option>
                <option value="friendly">Дружелюбный</option>
                <option value="casual">Простой</option>
              </select>
            </Field>
          </div>
          <Field label="Отрасль (шаблон безопасности)">
            <select
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
              value={answers.industry}
              onChange={(e) => setField("industry", e.target.value)}
            >
              <option value="auto_service">Автосервис</option>
              <option value="dental">Стоматология</option>
              <option value="beauty">Салон красоты</option>
              <option value="restaurant">Ресторан</option>
              <option value="real_estate">Недвижимость</option>
              <option value="ecommerce">Интернет-магазин</option>
              <option value="other">Другое</option>
            </select>
          </Field>
          <div className="flex flex-col gap-2 text-sm text-zinc-300">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={answers.book_appointments}
                onChange={(e) => setField("book_appointments", e.target.checked)}
              />
              Записывать клиентов
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={answers.take_leads}
                onChange={(e) => setField("take_leads", e.target.checked)}
              />
              Принимать заявки
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={answers.give_prices}
                onChange={(e) => setField("give_prices", e.target.checked)}
              />
              Давать цены
            </label>
          </div>
          <Button onClick={buildPreview} disabled={busy}>
            Собрать превью
          </Button>
        </section>
      ) : null}

      {step === "preview" && preview ? (
        <section className="space-y-4 rounded-2xl border border-emerald-500/25 bg-emerald-950/20 p-5">
          <h2 className="text-lg font-medium text-white">Превью сотрудника</h2>
          <p className="text-sm text-zinc-400">{preview.note_ru}</p>
          <div className="rounded-xl border border-white/10 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">Приветствие</p>
            <p className="mt-2 text-base text-white">{preview.greeting}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">Промпт / бриф</p>
            <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs text-zinc-300">
              {preview.system_prompt}
            </pre>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={publish} disabled={busy}>
              Опубликовать
            </Button>
            <Button variant="secondary" onClick={() => setStep("form")} disabled={busy}>
              Править анкету
            </Button>
          </div>
        </section>
      ) : null}

      {step === "done" ? (
        <section className="space-y-4 rounded-2xl border border-emerald-500/30 bg-emerald-950/25 p-5">
          <h2 className="text-lg font-medium text-emerald-100">Опубликовано</h2>
          <p className="text-sm text-zinc-300">
            Цифровой сотрудник готов. Одобрение владельца Virtus не требуется.
          </p>
          {preview?.greeting ? (
            <p className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-white">
              {preview.greeting}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Link
              href="/projects/chatbot"
              className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
            >
              Открыть кабинет
            </Link>
            <Button variant="secondary" onClick={() => setStep("form")} disabled={busy}>
              Изменить анкету
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
