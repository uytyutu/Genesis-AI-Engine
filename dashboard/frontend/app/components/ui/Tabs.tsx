"use client";

import { cn } from "../../lib/cn";

type Tab = { id: string; label: string };

export function Tabs({
  tabs,
  active,
  onChange,
  className,
}: {
  tabs: Tab[];
  active: string;
  onChange: (id: string) => void;
  className?: string;
}) {
  return (
    <div
      role="tablist"
      className={cn("flex flex-wrap gap-1 rounded-xl border border-genesis-border-subtle bg-genesis-bg/50 p-1", className)}
    >
      {tabs.map((tab) => {
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(tab.id)}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-genesis-accent/60",
              selected
                ? "bg-genesis-accent text-white shadow-glow"
                : "text-genesis-muted hover:bg-genesis-elevated hover:text-white"
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
