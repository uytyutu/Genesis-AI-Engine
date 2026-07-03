"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export type NotificationItem = {
  id: string;
  at: string;
  title: string;
  body: string;
  icon?: string;
  href?: string | null;
};

export function NotificationRail({ items }: { items: NotificationItem[] }) {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    setVisible(0);
  }, [items]);

  useEffect(() => {
    if (visible >= items.length) return;
    const t = setTimeout(() => setVisible((v) => v + 1), visible === 0 ? 600 : 2800);
    return () => clearTimeout(t);
  }, [visible, items.length]);

  const shown = items.slice(0, visible);

  if (!items.length) return null;

  return (
    <aside className="hidden w-64 shrink-0 2xl:block">
      <div className="sticky top-6 space-y-3">
        <p className="genesis-label px-1">Уведомления</p>
        <ul className="space-y-2">
          {shown.map((n, i) => (
            <li
              key={n.id}
              className="animate-slide-in-right rounded-xl border border-genesis-border-subtle bg-genesis-elevated/90 p-3 shadow-card backdrop-blur-md"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-[10px] tabular-nums text-genesis-muted">{n.at}</span>
                {n.icon && <span className="text-sm">{n.icon}</span>}
              </div>
              <p className="mt-1 text-xs font-semibold">{n.title}</p>
              <p className="mt-0.5 text-xs leading-relaxed text-genesis-muted">{n.body}</p>
              {n.href && (
                <Link href={n.href} className="mt-2 inline-block text-[11px] font-medium text-genesis-accent hover:underline">
                  Открыть →
                </Link>
              )}
            </li>
          ))}
          {visible < items.length && (
            <li className="flex items-center gap-2 px-2 text-[11px] text-genesis-muted">
              <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-genesis-accent" />
              Новое событие…
            </li>
          )}
        </ul>
      </div>
    </aside>
  );
}
