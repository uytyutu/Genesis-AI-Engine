"use client";

import { companyInitials, type GuidedCommerceState } from "../lib/guidedCommerce";
import { getIndustryProfile, logoChoiceLabel, slugDomain } from "../lib/guidedOwnership";
import { SpringIn } from "./motion/SpringIn";

type Props = {
  state: GuidedCommerceState;
};

function FromAnswer({ label }: { label: string }) {
  return (
    <span className="mt-0.5 block text-[8px] font-medium leading-tight text-emerald-300/95">
      ← {label}
    </span>
  );
}

export function GuidedOwnershipPreview({ state }: Props) {
  const name = state.companyName.trim();
  const hasName = Boolean(name);
  const hasGoal = Boolean(state.goalId);
  const hasLogo = Boolean(state.logoChoice);
  const hue = state.brandHue ?? 220;
  const industry = getIndustryProfile(state.goalId);
  const initials = companyInitials(name);

  const brandGradient = hasName
    ? `linear-gradient(135deg, hsl(${hue} 52% 38%) 0%, hsl(${(hue + 35) % 360} 48% 26%) 100%)`
    : `linear-gradient(135deg, ${industry.heroFrom} 0%, ${industry.heroTo} 100%)`;

  return (
    <SpringIn className="mt-4 overflow-hidden rounded-xl border border-white/10 bg-[#0a0d14] shadow-inner">
      {hasName ? (
        <div className="border-b border-emerald-500/20 bg-emerald-950/30 px-3 py-1.5 text-center text-[9px] font-medium text-emerald-200/90">
          Предварительная версия — из ваших ответов
        </div>
      ) : null}
      {/* Browser chrome */}
      <div className="flex items-center gap-1.5 border-b border-white/8 bg-[#0c0f18] px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-rose-400/80" />
        <span className="h-2 w-2 rounded-full bg-amber-400/80" />
        <span className="h-2 w-2 rounded-full bg-emerald-400/80" />
        <div className="ml-2 min-w-0 flex-1">
          <span className="block truncate text-[10px] text-white/90">
            {hasName ? slugDomain(name) : "ваш-сайт.de"}
          </span>
          {hasName ? <FromAnswer label="домен из названия" /> : null}
        </div>
      </div>

      {/* Facade / storefront — appears with company name */}
      {hasName ? (
        <div
          className="relative overflow-hidden border-b border-white/8 px-3 py-4 transition-all duration-700"
          style={{ background: brandGradient }}
        >
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(255,255,255,0.12),transparent_55%)]" />
          <div className="relative flex items-end justify-between gap-2">
            <div className="min-w-0 flex-1">
              <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-white/70">
                {industry.categoryLabel}
              </p>
              <FromAnswer label="из вашей цели" />
              <p
                className="mt-1 truncate text-lg font-bold leading-tight text-white drop-shadow-sm sm:text-xl"
                style={{ textShadow: "0 2px 12px rgba(0,0,0,0.35)" }}
              >
                {name}
              </p>
              <FromAnswer label={`из названия «${name}»`} />
              {hasGoal && !hasName ? null : (
                <p className="mt-0.5 truncate text-[10px] text-white/80">{industry.tagline}</p>
              )}
            </div>
            {hasLogo ? (
              <div className="flex shrink-0 flex-col items-center gap-1">
                <span
                  className="flex h-11 w-11 items-center justify-center rounded-xl border-2 border-white/30 bg-white/15 text-sm font-bold text-white shadow-lg backdrop-blur-sm"
                  aria-hidden
                >
                  {initials}
                </span>
                <span className="text-[8px] text-white/60">логотип</span>
                <FromAnswer label={logoChoiceLabel(state.logoChoice)} />
              </div>
            ) : (
              <div className="h-11 w-11 shrink-0 rounded-xl border border-dashed border-white/25 bg-white/5" />
            )}
          </div>
          {/* Storefront signboard */}
          <div className="relative mt-3 rounded-lg border border-white/25 bg-black/25 px-3 py-2 backdrop-blur-sm">
            <p className="text-center text-[11px] font-semibold tracking-wide text-white">{name}</p>
            <p className="text-center text-[9px] text-white/70">{industry.categoryLabel}</p>
            <FromAnswer label="вывеска из названия" />
          </div>
        </div>
      ) : hasGoal ? (
        <div
          className="border-b border-white/8 px-3 py-5 transition-all duration-500"
          style={{
            background: `linear-gradient(135deg, ${industry.heroFrom} 0%, ${industry.heroTo} 100%)`,
          }}
        >
          <p className="text-[10px] font-semibold uppercase tracking-wider text-white/70">
            {industry.categoryLabel}
          </p>
          <p className="mt-1 text-sm text-white/90">Введите название — появится вывеска</p>
        </div>
      ) : null}

      {/* Hero + services — after goal */}
      {hasGoal ? (
        <div className="space-y-2 p-3">
          <div
            className={`relative overflow-hidden rounded-lg transition-all duration-700 ${
              hasName ? "h-20 opacity-100" : "h-12 opacity-50"
            }`}
            style={{
              background: `linear-gradient(160deg, ${industry.heroFrom} 0%, ${industry.heroTo} 70%, ${industry.accent}33 100%)`,
            }}
          >
            <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_40%,rgba(255,255,255,0.06)_50%,transparent_60%)]" />
            <div className="relative flex h-full flex-col justify-end p-2.5">
              <p className="text-[9px] font-medium text-white/80">
                {hasName ? industry.categoryLabel : "Ваш бизнес"}
              </p>
              <p className="text-xs font-semibold text-white">
                {hasName ? industry.tagline : "Услуги появятся здесь"}
              </p>
            </div>
          </div>

          {hasName ? (
            <>
              <p className="text-[9px] font-medium text-genesis-muted">
                Услуги <span className="text-emerald-300/90">← тип вашего бизнеса</span>
              </p>
              <div className="grid grid-cols-2 gap-1.5">
                {industry.services.map((svc, i) => (
                  <div
                    key={svc.label}
                    className="flex items-center gap-1.5 rounded-lg border border-white/8 bg-white/[0.04] px-2 py-1.5 text-[10px] text-white/90 transition-all duration-500"
                    style={{ transitionDelay: `${i * 60}ms` }}
                  >
                    <span className="text-sm" aria-hidden>
                      {svc.icon}
                    </span>
                    <span className="truncate font-medium">{svc.label}</span>
                  </div>
                ))}
              </div>

              <button
                type="button"
                tabIndex={-1}
                className="w-full rounded-lg py-2 text-center text-[11px] font-semibold text-white transition-all duration-500"
                style={{
                  background: `linear-gradient(90deg, hsl(${hue} 50% 42%), hsl(${(hue + 25) % 360} 45% 35%))`,
                }}
              >
                Запись онлайн
              </button>
              <FromAnswer label="цвет из названия" />

              <div className="flex flex-wrap gap-2 text-[9px] text-genesis-muted">
                <span className="flex items-center gap-1 rounded-full bg-white/5 px-2 py-0.5">
                  📞 {industry.phone}
                </span>
                <span className="flex items-center gap-1 rounded-full bg-white/5 px-2 py-0.5">
                  🕐 {industry.hours}
                </span>
                <span className="flex items-center gap-1 rounded-full bg-white/5 px-2 py-0.5">
                  📍 {industry.city}
                </span>
              </div>
            </>
          ) : (
            <div className="grid grid-cols-3 gap-1.5">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-8 rounded bg-white/5 opacity-40" />
              ))}
            </div>
          )}
        </div>
      ) : null}

      {/* Logo placements — business card + mobile */}
      {hasLogo && hasName ? (
        <div className="flex gap-2 border-t border-white/8 bg-white/[0.02] p-3">
          <div className="min-w-0 flex-1 rounded-lg border border-white/10 bg-white/5 p-2">
            <p className="text-[8px] uppercase tracking-wider text-genesis-muted">Визитка</p>
            <FromAnswer label="логотип + название" />
            <div className="mt-1 flex items-center gap-2">
              <span
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[10px] font-bold text-white"
                style={{ background: brandGradient }}
              >
                {initials}
              </span>
              <div className="min-w-0">
                <p className="truncate text-[10px] font-semibold text-white">{name}</p>
                <p className="truncate text-[8px] text-genesis-muted">{industry.phone}</p>
              </div>
            </div>
          </div>
          <div className="w-[4.5rem] shrink-0 rounded-xl border-2 border-white/15 bg-[#0c0f18] p-1 shadow-inner">
            <p className="text-center text-[7px] text-genesis-muted">📱 мобильная</p>
            <FromAnswer label="тот же сайт" />
            <div
              className="mt-0.5 rounded-md px-1 py-1.5"
              style={{ background: brandGradient }}
            >
              <div className="flex items-center gap-0.5">
                <span className="flex h-3 w-3 items-center justify-center rounded-[3px] bg-white/20 text-[6px] font-bold text-white">
                  {initials.slice(0, 1)}
                </span>
                <span className="truncate text-[6px] font-semibold text-white">{name.split(" ")[0]}</span>
              </div>
              <div className="mt-1 h-4 rounded bg-black/20" />
            </div>
          </div>
        </div>
      ) : null}
    </SpringIn>
  );
}
