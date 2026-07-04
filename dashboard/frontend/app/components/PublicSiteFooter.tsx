import Link from "next/link";
import { CONTACT_EMAIL } from "../lib/siteConfig";

const LEGAL = [
  { href: "/impressum", label: "Impressum" },
  { href: "/datenschutz", label: "Datenschutz" },
  { href: "/agb", label: "AGB" },
];

const HELP = [
  { href: "/faq", label: "FAQ" },
  { href: "/kontakt", label: "Kontakt" },
  { href: "/services", label: "Услуги" },
];

export function PublicSiteFooter() {
  return (
    <footer className="mt-16 border-t border-white/5 pt-8 pb-6">
      <div className="grid gap-8 sm:grid-cols-3">
        <div>
          <p className="font-semibold">Genesis</p>
          <p className="mt-2 text-sm text-genesis-muted">
            Лендинги для бизнеса · цена сразу · оплата онлайн
          </p>
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="mt-3 inline-block text-sm text-genesis-accent hover:underline"
          >
            {CONTACT_EMAIL}
          </a>
        </div>
        <div>
          <p className="genesis-label">Правовая информация</p>
          <ul className="mt-3 space-y-2 text-sm">
            {LEGAL.map((l) => (
              <li key={l.href}>
                <Link href={l.href} className="text-genesis-muted hover:text-white">
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="genesis-label">Помощь</p>
          <ul className="mt-3 space-y-2 text-sm">
            {HELP.map((l) => (
              <li key={l.href}>
                <Link href={l.href} className="text-genesis-muted hover:text-white">
                  {l.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/order" className="font-medium text-genesis-accent hover:underline">
                Заказать сайт →
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <p className="mt-8 text-center text-[11px] text-genesis-muted/80">
        © {new Date().getFullYear()} Genesis AI Engine
      </p>
    </footer>
  );
}
