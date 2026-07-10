"use client";

import Link from "next/link";

type Cta = { href: string; label: string };

type Props = {
  text: string;
  ctas: Cta[];
  onQuickAction?: (message: string) => void;
};

/** Compact execution result — artifacts and progress, not a chat essay. */
export function ExecutionResultPanel({ text, ctas, onQuickAction }: Props) {
  const lines = text.split("\n").filter((l) => l.trim());
  const headline = lines[0] ?? "";
  const steps = lines.filter((l) => l.startsWith("✓"));
  const footer = lines.filter((l) => !l.startsWith("✓") && l !== headline);

  return (
    <div className="space-y-3">
      {headline ? (
        <p className="text-sm font-semibold text-white">{headline}</p>
      ) : null}
      {steps.length > 0 ? (
        <ul className="space-y-1 rounded-xl border border-emerald-500/20 bg-emerald-950/20 px-3 py-2.5 text-sm text-emerald-100/90">
          {steps.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : null}
      {footer.length > 0 ? (
        <p className="text-xs text-genesis-muted">{footer.join(" · ")}</p>
      ) : null}
      {ctas.length > 0 ? (
        <div className="flex flex-wrap gap-2 pt-1">
          {ctas.map((cta) => {
            if (cta.href.startsWith("#action:") && onQuickAction) {
              const message = cta.href.slice("#action:".length);
              return (
                <button
                  key={cta.href}
                  type="button"
                  onClick={() => onQuickAction(message)}
                  className="rounded-xl border border-genesis-accent/35 bg-genesis-accent/10 px-3 py-2 text-xs font-semibold text-genesis-accent transition hover:bg-genesis-accent/20"
                >
                  {cta.label}
                </button>
              );
            }
            return (
              <Link
                key={`${cta.href}-${cta.label}`}
                href={cta.href}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl bg-gradient-to-r from-genesis-accent to-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:opacity-90"
              >
                {cta.label}
              </Link>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
