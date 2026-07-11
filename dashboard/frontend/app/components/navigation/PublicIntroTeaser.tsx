"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { ASSISTANT_NAME, BRAND_NAME } from "../../lib/publicBrand";
import { nextFunnelStep, PUBLIC_FUNNEL } from "../../lib/publicFunnel";
import { ButtonLink, Card } from "../ui";

const EXAMPLE_RESULTS = [
  {
    title: "Сайт для кофейни",
    detail: "Лендинг с меню, контактами и стилем бренда — из разговора с Vector",
    tag: "Пример результата",
  },
  {
    title: "Бизнес-план",
    detail: "Структура, цифры и PDF — Vector помог собрать и доработать",
    tag: "Пример результата",
  },
  {
    title: "Презентация",
    detail: "Слайды для инвестора или партнёра — вместе с Vector",
    tag: "Пример результата",
  },
] as const;

type Props = {
  onTryVector?: () => void;
};

export function PublicIntroTeaser({ onTryVector }: Props) {
  const pathname = usePathname() ?? "/site";
  const searchParams = useSearchParams();
  const view = searchParams.get("view") ?? "";
  const next = nextFunnelStep(pathname, view);

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <Card padding="lg" className="border-emerald-500/20 bg-gradient-to-br from-emerald-950/20 to-genesis-panel">
        <p className="text-xs font-medium uppercase tracking-wide text-emerald-400/90">Знакомство с продуктом</p>
        <h2 className="mt-2 text-xl font-semibold leading-snug">
          {BRAND_NAME} — операционная система вашей цифровой компании
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-genesis-muted">
          Не чат-бот и не генератор. <strong className="text-white">{ASSISTANT_NAME}</strong> — ваш
          цифровой сотрудник: помнит контекст, ведёт проекты и доводит до результата.
        </p>
        <p className="mt-2 text-sm text-genesis-muted">
          Слева — живой разговор. Здесь — примеры того, что вы создаёте вместе.
        </p>
      </Card>

      <div className="grid gap-3 sm:grid-cols-1">
        {EXAMPLE_RESULTS.map((item) => (
          <Card key={item.title} padding="md" className="border-genesis-border-subtle">
            <p className="text-[10px] font-medium uppercase tracking-wide text-genesis-muted">{item.tag}</p>
            <p className="mt-1 font-semibold">{item.title}</p>
            <p className="mt-1 text-xs leading-relaxed text-genesis-muted">{item.detail}</p>
          </Card>
        ))}
      </div>

      <Card padding="md" className="mt-auto border-genesis-border-subtle">
        <p className="text-sm font-medium">Попробуйте сейчас</p>
        <p className="mt-1 text-xs text-genesis-muted">
          Задайте Vector вопрос слева — о бизнесе, идее или задаче. Это полноценное знакомство, не демо-заглушка.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {onTryVector ? (
            <button
              type="button"
              onClick={onTryVector}
              className="rounded-lg bg-genesis-accent px-4 py-2 text-sm font-medium text-white shadow-glow hover:brightness-110"
            >
              Спросить {ASSISTANT_NAME}
            </button>
          ) : null}
          <ButtonLink href="/services" variant="secondary" size="sm">
            Услуги →
          </ButtonLink>
        </div>
      </Card>

      {next ? (
        <PublicNextStepBanner step={next} />
      ) : null}

      <p className="text-center text-[11px] text-genesis-muted/70">
        Уже работаете над проектом?{" "}
        <Link href="/projects" className="text-genesis-accent hover:underline">
          Откройте в своей компании →
        </Link>
      </p>
    </div>
  );
}

export function PublicNextStepBanner({ step }: { step: { label: string; href: string; description: string } }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-genesis-border-subtle bg-genesis-elevated/40 px-4 py-3">
      <div>
        <p className="text-xs text-genesis-muted">Следующий шаг</p>
        <p className="text-sm font-medium">{step.description}</p>
      </div>
      <ButtonLink href={step.href} variant="primary" size="sm">
        {step.label} →
      </ButtonLink>
    </div>
  );
}

export function PublicFunnelSteps({ activeId }: { activeId?: string }) {
  return (
    <ol className="flex flex-wrap gap-2 text-[11px] text-genesis-muted" aria-label="Путь знакомства">
      {PUBLIC_FUNNEL.map((step, i) => (
        <li key={step.id} className="flex items-center gap-2">
          <Link
            href={step.href}
            className={
              activeId === step.id
                ? "rounded-md bg-genesis-accent/15 px-2 py-0.5 font-medium text-white"
                : "hover:text-white"
            }
          >
            {step.label}
          </Link>
          {i < PUBLIC_FUNNEL.length - 1 ? <span aria-hidden>→</span> : null}
        </li>
      ))}
    </ol>
  );
}
