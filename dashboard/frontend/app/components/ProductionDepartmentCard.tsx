"use client";

import Link from "next/link";
import { ChecksList } from "./ChecksList";

export type ProductionDepartment = {
  label: string;
  status: string;
  status_label: string;
  product_type: string | null;
  product_id: string | null;
  preview_url: string | null;
  business_name?: string | null;
  checks: { id: string; label: string; ok: boolean; pending?: boolean }[];
  owner_approved: boolean;
  quality_percent: number;
};

export function ProductionDepartmentCard({ dept }: { dept: ProductionDepartment }) {
  const href = dept.product_id ? `/products/${dept.product_id}` : "/create";

  return (
    <GenesisCardShell title="🏭 Отдел создания продуктов" subtitle={dept.status_label}>
      {dept.product_id ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="font-semibold">{dept.business_name ?? dept.product_type}</p>
              <p className="mt-1 text-xs text-genesis-muted">{dept.product_type}</p>
            </div>
            {dept.quality_percent > 0 && (
              <div className="text-right">
                <p className="genesis-label">Качество (проверки)</p>
                <p className="text-lg font-bold tabular-nums text-emerald-400">{dept.quality_percent}%</p>
              </div>
            )}
          </div>
          {dept.checks.length > 0 && <ChecksList checks={dept.checks} />}
          <Link
            href={href}
            className="inline-flex rounded-xl bg-genesis-accent/15 px-4 py-2 text-sm font-medium text-genesis-accent ring-1 ring-genesis-accent/30 hover:bg-genesis-accent/25"
          >
            Открыть продукт →
          </Link>
        </div>
      ) : (
        <div className="space-y-3 text-sm text-genesis-muted">
          <p>Нет активного продукта — создайте первый Landing.</p>
          <Link
            href="/create"
            className="inline-flex rounded-xl bg-gradient-to-r from-genesis-accent to-blue-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Создать продукт
          </Link>
        </div>
      )}
    </GenesisCardShell>
  );
}

function GenesisCardShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="genesis-card animate-fade-up p-5">
      <p className="font-semibold">{title}</p>
      {subtitle && <p className="mt-1 text-xs text-genesis-muted">{subtitle}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}
