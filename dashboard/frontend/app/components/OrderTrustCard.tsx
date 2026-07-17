import Link from "next/link";
import { Card } from "./ui";
import {
  ORDER_TRUST_CONTENT,
  type OrderPurchaseType,
} from "../lib/orderTrustCard";

export function OrderTrustCard({
  purchaseType,
  legalReady,
}: {
  purchaseType: OrderPurchaseType;
  legalReady?: boolean;
}) {
  const lines = ORDER_TRUST_CONTENT[purchaseType];

  return (
    <Card
      hover={false}
      padding="md"
      className="border-emerald-500/15 bg-emerald-950/10 text-left"
    >
      <p className="genesis-label text-emerald-200/80">
        {purchaseType === "subscription" ? "Vertrauen · Abo" : "Vertrauen · Einmalkauf"}
      </p>
      <ul className="mt-3 space-y-3 text-xs leading-relaxed text-genesis-muted">
        {lines.map((line, index) => (
          <li key={`${purchaseType}-${index}`} className="flex gap-2">
            <span className="shrink-0 text-base leading-none" aria-hidden>
              {line.emoji}
            </span>
            <div>
              {line.emoji === "📄" && purchaseType === "subscription" ? (
                <span>
                  {legalReady === false ? (
                    <>
                      Das vollständige Impressum wird vorbereitet. Kontakt:{" "}
                      <a href="mailto:hello@genesis-ai-engine.com" className="text-genesis-accent hover:underline">
                        hello@genesis-ai-engine.com
                      </a>
                      .
                    </>
                  ) : (
                    <>
                      <Link href="/impressum" className="text-genesis-accent hover:underline">
                        Impressum
                      </Link>
                      {" und "}
                      <Link href="/datenschutz" className="text-genesis-accent hover:underline">
                        Datenschutz
                      </Link>
                      {" sind jederzeit verfügbar."}
                    </>
                  )}
                </span>
              ) : line.emoji === "📄" && legalReady === false ? (
                <span>
                  Rechtliche Dokumente werden vorbereitet. Verkäuferkontakt:{" "}
                  <a href="mailto:hello@genesis-ai-engine.com" className="text-genesis-accent hover:underline">
                    hello@genesis-ai-engine.com
                  </a>
                  .
                </span>
              ) : (
                <span>
                  {line.text}
                  {line.links?.length ? (
                    <>
                      {" "}
                      {line.links.map((link, i) => (
                        <span key={link.href}>
                          {i > 0 ? " und " : null}
                          <Link href={link.href} className="text-genesis-accent hover:underline">
                            {link.label}
                          </Link>
                        </span>
                      ))}
                      .
                    </>
                  ) : null}
                </span>
              )}
              {line.bullets?.length ? (
                <ul className="mt-1.5 list-disc space-y-0.5 pl-4">
                  {line.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[10px] text-genesis-muted/80">
        <Link href="/trust" className="text-genesis-accent hover:underline">
          Mehr zu Daten und Vertrauen
        </Link>
      </p>
    </Card>
  );
}
