import Link from "next/link";
import { Card } from "./ui";
import {
  ORDER_TRUST_CONTENT,
  type OrderPurchaseType,
} from "../lib/orderTrustCard";

export function OrderTrustCard({ purchaseType }: { purchaseType: OrderPurchaseType }) {
  const lines = ORDER_TRUST_CONTENT[purchaseType];

  return (
    <Card
      hover={false}
      padding="md"
      className="border-emerald-500/15 bg-emerald-950/10 text-left"
    >
      <p className="genesis-label text-emerald-200/80">
        {purchaseType === "subscription" ? "Доверие · подписка" : "Доверие · разовая покупка"}
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
                  <Link href="/impressum" className="text-genesis-accent hover:underline">
                    Impressum
                  </Link>
                  {" и "}
                  <Link href="/datenschutz" className="text-genesis-accent hover:underline">
                    Datenschutz
                  </Link>
                  {" доступны всегда."}
                </span>
              ) : (
                <span>
                  {line.text}
                  {line.links?.length ? (
                    <>
                      {" "}
                      {line.links.map((link, i) => (
                        <span key={link.href}>
                          {i > 0 ? " и " : null}
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
          Подробнее о данных и доверии
        </Link>
      </p>
    </Card>
  );
}
