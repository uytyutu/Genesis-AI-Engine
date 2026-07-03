import type { ReactNode } from "react";

type Props = {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  glow?: boolean;
  animate?: boolean;
};

export function GenesisCard({ title, subtitle, children, className = "", glow, animate }: Props) {
  return (
    <section
      className={`genesis-card p-5 ${glow ? "border-genesis-accent/25 shadow-glow" : ""} ${
        animate ? "animate-fade-up" : ""
      } ${className}`}
    >
      {(title || subtitle) && (
        <header className="mb-4">
          {title && <h2 className="text-sm font-semibold text-genesis-text">{title}</h2>}
          {subtitle && <p className="mt-0.5 text-xs text-genesis-muted">{subtitle}</p>}
        </header>
      )}
      {children}
    </section>
  );
}
