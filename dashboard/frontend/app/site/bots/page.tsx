"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";

/**
 * Commercial AI Employee vitrine — honest: no LIVE claim without deployment gate.
 * Prices from SSOT (pricing_engine): setup + monthly; Automation one-time.
 */
const PACKAGES = [
  {
    id: "starter",
    name: "AI Receptionist",
    setup: 499,
    monthly: 99,
    href: "/order/bot?package=starter",
    cta: "AI Receptionist bestellen",
    includes: [
      "1 AI Employee",
      "Website Chat + Telegram (nach Setup)",
      "Lead-Qualifizierung",
      "FAQ aus Ihren Angaben",
      "Client Workspace",
    ],
    excludes: [
      "WhatsApp / Instagram (Coming Soon)",
      "Automatisches Website-Embedding ohne Ihre Freigabe",
      "Garantierte Native-Human-Übersetzung",
    ],
  },
  {
    id: "business",
    name: "Business",
    setup: 999,
    monthly: 199,
    href: "/order/bot?package=business",
    cta: "Business bestellen",
    includes: [
      "Bis zu 3 AI Employees",
      "Website Chat + Telegram",
      "Erweiterte Anweisungen & Knowledge",
      "Lead-Weiterleitung",
      "Client Workspace",
    ],
    excludes: [
      "WhatsApp / Instagram (Coming Soon)",
      "Recurring Stripe-Abo (noch Setup-Zahlung)",
    ],
  },
  {
    id: "professional",
    name: "Professional",
    setup: 1499,
    monthly: 349,
    href: "/order/bot?package=professional",
    cta: "Professional bestellen",
    includes: [
      "Fair-Use AI Employees",
      "Website Chat + Telegram",
      "Knowledge Hub & Onboarding",
      "Deployment-Readiness Gate",
      "Operator-Review vor Go-Live",
    ],
    excludes: ["Unverifizierte LIVE-Channels", "WhatsApp / Instagram"],
  },
] as const;

export default function SiteBotsPage() {
  const { t } = useTranslation("site");

  return (
    <div className="min-h-screen bg-[#f6f4ef] text-slate-900">
      <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4">
          <Link href="/site" className="text-sm font-semibold tracking-wide">
            Virtus Core
          </Link>
          <Link
            href="/order/bot"
            className="text-sm text-slate-600 underline-offset-2 hover:underline"
          >
            {t("agencyHub.atmosphere.botsCta", {
              defaultValue: "AI Employee bestellen",
            })}
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-12 sm:py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-800">
          Virtus Core · AI Employee
        </p>
        <h1 className="mt-3 font-serif text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
          {t("agencyHub.atmosphere.botsTitle", {
            defaultValue: "AI Employee für echte Kanäle",
          })}
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-slate-600">
          {t("agencyHub.atmosphere.botsSub", {
            defaultValue:
              "Bestellen → bezahlen → Onboarding → Knowledge → Test → Deployment-Check. Kein Fake-LIVE.",
          })}
        </p>
        <p className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          Status: Verkauf & Setup-Zahlung möglich. Recurring-Abo und unverifizierte Channels
          werden nicht als LIVE ausgewiesen.
        </p>

        <div className="mt-10 grid gap-6 lg:grid-cols-3">
          {PACKAGES.map((pkg) => (
            <article
              key={pkg.id}
              className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <h2 className="text-xl font-semibold text-slate-900">{pkg.name}</h2>
              <p className="mt-4 text-3xl font-semibold text-slate-900">
                {pkg.setup} €
                <span className="ml-1 text-sm font-normal text-slate-500">Einrichtung</span>
              </p>
              <p className="mt-1 text-sm text-slate-600">
                + {pkg.monthly} € / Monat{" "}
                <span className="text-slate-400">(Abo noch nicht aktiv)</span>
              </p>
              <div className="mt-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Enthalten
                </p>
                <ul className="mt-2 space-y-1.5 text-sm text-slate-700">
                  {pkg.includes.map((line) => (
                    <li key={line}>✓ {line}</li>
                  ))}
                </ul>
              </div>
              <div className="mt-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Nicht enthalten
                </p>
                <ul className="mt-2 space-y-1.5 text-sm text-slate-500">
                  {pkg.excludes.map((line) => (
                    <li key={line}>— {line}</li>
                  ))}
                </ul>
              </div>
              <Link
                href={pkg.href}
                className="mt-6 inline-flex min-h-[48px] items-center justify-center rounded-xl bg-slate-900 px-4 text-sm font-semibold text-white hover:bg-slate-800"
              >
                {pkg.cta}
              </Link>
            </article>
          ))}
        </div>

        <section className="mt-10 rounded-2xl border border-dashed border-slate-300 bg-white/70 p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-slate-900">Business Automation</h2>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            650 € <span className="text-sm font-normal text-slate-500">einmalig / Projekt</span>
          </p>
          <p className="mt-3 max-w-2xl text-sm text-slate-600">
            Prozess- und Automatisierungsprojekt mit Operator — kein Sofort-Bot-Deploy.
          </p>
          <Link
            href="/order?service=business_automation"
            className="mt-5 inline-flex min-h-[48px] items-center justify-center rounded-xl border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-900 hover:border-slate-400"
          >
            Automation anfragen
          </Link>
        </section>

        <p className="mt-8 text-center text-sm text-slate-500">
          Nach der Zahlung: Client Workspace → Onboarding → Knowledge → Test → Deployment Gate.
        </p>
      </main>
    </div>
  );
}
