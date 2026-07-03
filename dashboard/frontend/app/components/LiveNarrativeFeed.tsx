"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export type NarrativeEvent = {
  department: string;
  message: string;
  at: string;
  icon: string;
  action_label: string | null;
  action_href: string | null;
  progress_percent: number | null;
  delay_ms: number;
};

export function LiveNarrativeFeed({ feed }: { feed: NarrativeEvent[] }) {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    setVisible(0);
  }, [feed]);

  useEffect(() => {
    if (visible >= feed.length) return;
    const next = feed[visible];
    const wait = visible === 0 ? 400 : next?.delay_ms - (feed[visible - 1]?.delay_ms ?? 0) || 3500;
    const t = setTimeout(() => setVisible((v) => v + 1), Math.max(800, wait));
    return () => clearTimeout(t);
  }, [visible, feed]);

  const shown = feed.slice(0, visible);

  return (
    <ul className="space-y-4">
      {shown.map((e, i) => (
        <li
          key={`${e.department}-${i}`}
          className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/50 p-4 transition-all duration-500 hover:border-genesis-accent/20"
        >
          <div className="flex items-baseline gap-2 text-xs text-genesis-muted">
            <span className="tabular-nums">{e.at}</span>
            <span className="font-semibold text-genesis-text">{e.department}</span>
          </div>
          <p className="mt-2 text-sm leading-relaxed">
            {e.icon} {e.message}
          </p>
          {e.progress_percent != null && (
            <div className="mt-3">
              <div className="h-2 overflow-hidden rounded-full bg-genesis-border">
                <div
                  className="h-full rounded-full bg-genesis-accent transition-all duration-1000"
                  style={{ width: `${e.progress_percent}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-genesis-muted">{e.progress_percent}%</p>
            </div>
          )}
          {e.action_label && e.action_href && (
            <Link
              href={e.action_href}
              className="mt-3 inline-block rounded-lg bg-genesis-accent px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500"
            >
              {e.action_label}
            </Link>
          )}
        </li>
      ))}
      {visible < feed.length && (
        <li className="flex items-center gap-2 text-xs text-genesis-muted">
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-genesis-accent" />
          Команда работает…
        </li>
      )}
    </ul>
  );
}
