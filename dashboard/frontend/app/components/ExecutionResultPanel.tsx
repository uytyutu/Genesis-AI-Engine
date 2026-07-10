"use client";

import Link from "next/link";

type Cta = {
  href: string;
  label: string;
  group?: string;
  available?: boolean;
};

type Props = {
  text: string;
  ctas: Cta[];
  onQuickAction?: (message: string) => void;
};

const GROUP_LABELS: Record<string, string> = {
  artifacts: "Результат работы",
  next: "Что дальше",
};

const DEV_ARTIFACT_LINE =
  /(?:\.html|\.css|\.md|\.json|workspace|manifest|brief\.md|index\.html|style\.css|site_manifest)/i;

/** Work-agent result — artifacts + intent-aware actions, not a chat essay. */
export function ExecutionResultPanel({ text, ctas, onQuickAction }: Props) {
  const lines = text.split("\n").filter((l) => l.trim());
  const headline = lines[0] ?? "";
  const steps = lines.filter((l) => l.startsWith("✓"));
  const footer = lines.filter(
    (l) => !l.startsWith("✓") && l !== headline && !DEV_ARTIFACT_LINE.test(l),
  );

  const artifacts = ctas.filter((c) => (c.group ?? "artifacts") === "artifacts");
  const nextSteps = ctas.filter((c) => c.group === "next");

  const renderCta = (cta: Cta) => {
    const disabled = cta.available === false;
    const base =
      "rounded-xl px-3 py-2 text-xs font-semibold transition min-h-[2.25rem] inline-flex items-center justify-center";

    if (cta.href.startsWith("#horizon:")) {
      return (
        <span
          key={cta.href}
          className={`${base} cursor-not-allowed border border-white/10 bg-white/5 text-genesis-muted opacity-60`}
          title="Скоро в Virtus Core"
        >
          {cta.label}
        </span>
      );
    }

    if (cta.href.startsWith("#action:") && onQuickAction) {
      if (disabled) {
        return (
          <span
            key={cta.href}
            className={`${base} cursor-not-allowed border border-white/10 text-genesis-muted opacity-60`}
          >
            {cta.label}
          </span>
        );
      }
      const message = cta.href.slice("#action:".length);
      return (
        <button
          key={cta.href}
          type="button"
          onClick={() => onQuickAction(message)}
          className={`${base} border border-genesis-accent/35 bg-genesis-accent/10 text-genesis-accent hover:bg-genesis-accent/20`}
        >
          {cta.label}
        </button>
      );
    }

    if (disabled) {
      return (
        <span
          key={cta.href}
          className={`${base} cursor-not-allowed border border-white/10 text-genesis-muted opacity-60`}
        >
          {cta.label}
        </span>
      );
    }

    return (
      <Link
        key={`${cta.href}-${cta.label}`}
        href={cta.href}
        target="_blank"
        rel="noopener noreferrer"
        className={`${base} bg-gradient-to-r from-genesis-accent to-indigo-600 text-white hover:opacity-90`}
      >
        {cta.label}
      </Link>
    );
  };

  const renderGroup = (items: Cta[], groupKey: string) => {
    if (items.length === 0) return null;
    return (
      <div className="space-y-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-genesis-muted">
          {GROUP_LABELS[groupKey] ?? groupKey}
        </p>
        <div className="flex flex-wrap gap-2">{items.map(renderCta)}</div>
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {headline ? (
        <p className="text-sm font-semibold text-white">{headline}</p>
      ) : null}
      {steps.length > 0 ? (
        <ul className="space-y-1.5 rounded-xl border border-emerald-500/20 bg-emerald-950/20 px-3 py-2.5 text-sm text-emerald-100/90">
          {steps.map((line) => (
            <li key={line} className="leading-snug">
              {line.replace(/\*\*(.+?)\*\*/g, "$1")}
            </li>
          ))}
        </ul>
      ) : null}
      {footer.length > 0 ? (
        <p className="text-xs leading-relaxed text-genesis-muted">{footer.join(" ")}</p>
      ) : null}
      {artifacts.length > 0 || nextSteps.length > 0 ? (
        <div className="space-y-3 border-t border-white/10 pt-3">
          {renderGroup(artifacts, "artifacts")}
          {renderGroup(nextSteps, "next")}
        </div>
      ) : null}
    </div>
  );
}
