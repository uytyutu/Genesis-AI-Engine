"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Notification = {
  at: string;
  title: string;
  message: string;
  order_id: string | null;
};

export function OwnerNotificationsPanel() {
  const [items, setItems] = useState<Notification[]>([]);

  useEffect(() => {
    fetch(`${API}/api/owner/notifications`)
      .then((r) => r.json())
      .then((body) => setItems(body.notifications ?? []))
      .catch(() => setItems([]));
    const t = setInterval(() => {
      fetch(`${API}/api/owner/notifications`)
        .then((r) => r.json())
        .then((body) => setItems(body.notifications ?? []))
        .catch(() => {});
    }, 15000);
    return () => clearInterval(t);
  }, []);

  if (!items.length) return null;

  return (
    <section className="genesis-card border-blue-500/25 bg-gradient-to-br from-blue-950/20 to-genesis-panel p-5">
      <p className="genesis-label text-blue-300/90">Уведомления</p>
      <ul className="mt-3 space-y-2">
        {items.slice(0, 5).map((n, i) => (
          <li
            key={`${n.at}-${i}`}
            className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 px-4 py-3 text-sm"
          >
            <p className="font-medium">{n.title}</p>
            <p className="mt-1 text-xs text-genesis-muted">{n.message}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
