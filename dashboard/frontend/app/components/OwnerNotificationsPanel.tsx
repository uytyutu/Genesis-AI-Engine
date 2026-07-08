"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "../lib/fetchApi";
import { useDeferredMount } from "../lib/useDeferredMount";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Notification = {
  at: string;
  title: string;
  message: string;
  order_id: string | null;
};

export function OwnerNotificationsPanel() {
  const deferred = useDeferredMount(2200);
  const [items, setItems] = useState<Notification[]>([]);

  useEffect(() => {
    if (!deferred) return;
    const load = () =>
      fetchApi(`${API}/api/owner/notifications`, { timeoutMs: 8_000 })
        .then((r) => r.json())
        .then((body) => setItems(body.notifications ?? []))
        .catch(() => setItems([]));
    load();
    const t = setInterval(load, 20000);
    return () => clearInterval(t);
  }, [deferred]);

  if (!deferred || !items.length) return null;

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
