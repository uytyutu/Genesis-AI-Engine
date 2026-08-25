"use client";

import { FarmDashboard } from "../components/FarmDashboard";
import { MissionControlRecoverBoundary } from "../components/MissionControlRecoverBoundary";

/** ARCHIVE / Earn Labs — Farm desk moved off Virtus home. */
export default function FarmDeskPage() {
  return (
    <MissionControlRecoverBoundary>
      <div className="mb-3 rounded-xl border border-amber-500/25 bg-amber-950/20 px-4 py-3 text-sm text-amber-100/90">
        <p className="font-semibold">Студия · Ферма (архив)</p>
        <p className="mt-1 text-xs text-amber-100/70">
          Это не ежедневный Mission Control. Коммерция Virtus: Обзор → Клиенты →
          Заказы → Продукты.
        </p>
      </div>
      <FarmDashboard />
    </MissionControlRecoverBoundary>
  );
}
