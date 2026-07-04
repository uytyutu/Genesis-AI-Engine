import type { ReactNode } from "react";
import { Card, CardHeader } from "./ui/Card";

type Props = {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  glow?: boolean;
  animate?: boolean;
};

/** @deprecated Prefer `Card` from `components/ui` for new code. */
export function GenesisCard({ title, subtitle, children, className = "", glow, animate }: Props) {
  return (
    <Card
      glow={glow}
      hover={!animate}
      className={`${animate ? "animate-fade-up" : ""} ${className}`}
    >
      {(title || subtitle) && (
        <CardHeader title={title ?? ""} subtitle={subtitle} />
      )}
      {children}
    </Card>
  );
}
