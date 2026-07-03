"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChecksList } from "../components/ChecksList";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Product = {
  product_id: string;
  business_name: string;
  product_type: string;
  status_label: string;
  owner_approved: boolean;
  checks: { id: string; label: string; ok: boolean; pending?: boolean }[];
};

export default function ProjectsPage() {
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    fetch(`${API}/api/factory/products`)
      .then((r) => r.json())
      .then((d) => setProducts(d.products ?? []))
      .catch(() => setProducts([]));
  }, []);

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-lg space-y-4">
        <h1 className="text-2xl font-bold">Галерея продуктов</h1>
        <p className="text-sm text-genesis-muted">История работы отдела создания продуктов</p>
        {products.length === 0 ? (
          <p className="text-genesis-muted">Пока нет продуктов. Создайте первый Landing.</p>
        ) : (
          <ul className="space-y-4">
            {products.map((p) => (
              <li key={p.product_id} className="rounded-xl border border-genesis-border bg-genesis-panel p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">{p.business_name}</p>
                    <p className="text-sm text-genesis-muted">{p.product_type}</p>
                  </div>
                  <span className="text-lg">{p.owner_approved ? "★★★★★" : "☆☆☆☆☆"}</span>
                </div>
                <p className="mt-2 text-xs text-genesis-muted">{p.status_label}</p>
                <div className="mt-3">
                  <ChecksList checks={p.checks} />
                </div>
                <Link
                  href={`/products/${p.product_id}`}
                  className="mt-3 inline-block text-sm text-genesis-accent hover:underline"
                >
                  Открыть →
                </Link>
              </li>
            ))}
          </ul>
        )}
        <Link href="/create" className="text-sm text-genesis-accent hover:underline">
          + Создать продукт
        </Link>
      </div>
    </main>
  );
}
