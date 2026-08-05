"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../../lib/clientAuth";
import { formatApiDetail } from "../../../lib/formatApiError";
import { publicApiBase } from "../../../lib/publicApiBase";

const API = publicApiBase();

const PIPELINE_STAGES = [
  "accepted",
  "preparing",
  "factory_queue",
  "generating",
  "quality_check",
  "ready_to_publish",
  "published",
] as const;

type StorePayload = {
  order_id: string;
  store_name?: string;
  package_name?: string;
  shop_pipeline?: string | null;
  shop_pipeline_label?: string | null;
  brief_summary?: string;
  shop_brief?: Record<string, unknown>;
  factory_hook?: { status?: string; note?: string; version?: number } | null;
  paid?: boolean;
  product_id?: string | null;
  version?: number | null;
  versions?: { version: number; created_at?: string; quality_passed?: boolean }[];
  published_url?: string | null;
  live_url?: string | null;
  preview_url?: string | null;
  generation_log?: { ts?: string; event?: string; note?: string }[];
  pipeline_stages?: string[];
  r3_sections?: { id: string; label: string; available: boolean }[];
};

function stageIndex(pipeline: string | null | undefined, stages: string[]): number {
  const key = String(pipeline || "");
  const i = stages.indexOf(key);
  return i >= 0 ? i : -1;
}

export default function ClientStorePage() {
  const params = useParams();
  const orderId = String(params?.orderId || "");
  const router = useRouter();
  const [data, setData] = useState<StorePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!getClientToken()) {
      router.replace(
        `/client/login?next=${encodeURIComponent(`/client/stores/${orderId}`)}`,
      );
      return;
    }
    try {
      const res = await fetch(`${API}/api/client/stores/${orderId}`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Store not found");
      }
      setData(body as StorePayload);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [orderId, router]);

  useEffect(() => {
    void load();
  }, [load]);

  const action = async (path: string, body?: object) => {
    setBusy(path);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/stores/${orderId}/${path}`, {
        method: "POST",
        headers: {
          ...clientAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(payload.detail) || "Action failed");
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  };

  const brief = data?.shop_brief || {};
  const stages = data?.pipeline_stages?.length
    ? data.pipeline_stages
    : [...PIPELINE_STAGES];
  const currentIdx = stageIndex(data?.shop_pipeline, stages);
  const isPublished =
    data?.shop_pipeline === "published" || Boolean(data?.published_url);
  const openUrl =
    data?.published_url ||
    data?.live_url ||
    (orderId ? `${API}/api/client/stores/${orderId}/live` : null);
  const absoluteOpen =
    openUrl && openUrl.startsWith("/")
      ? `${API}${openUrl}`
      : openUrl;

  return (
    <ClientWorkspaceShell
      title={data?.store_name || "Мой интернет-магазин"}
      subtitle="AI Store — professional online shop for your business"
    >
      {error ? (
        <p className="text-sm text-rose-300" role="alert">
          {error}
        </p>
      ) : null}
      {!data && !error ? (
        <p className="text-sm text-zinc-400">Загрузка…</p>
      ) : null}
      {data ? (
        <div className="space-y-6">
          <div className="rounded-2xl border border-emerald-500/25 bg-emerald-500/[0.07] p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-200/80">
              Статус
            </p>
            <p className="mt-2 text-2xl font-semibold text-white">
              {data.shop_pipeline_label || data.shop_pipeline || "—"}
            </p>
            <p className="mt-1 text-sm text-zinc-400">
              {data.package_name} · {data.brief_summary}
              {data.version ? ` · v${data.version}` : ""}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {stages.map((stage, idx) => {
                const active = idx === currentIdx;
                const done = currentIdx >= 0 && idx < currentIdx;
                return (
                  <span
                    key={stage}
                    className={`rounded-full px-2.5 py-1 text-[11px] ${
                      active
                        ? "bg-emerald-500/30 text-emerald-100 ring-1 ring-emerald-400/40"
                        : done
                          ? "bg-white/10 text-zinc-300"
                          : "bg-white/[0.03] text-zinc-600"
                    }`}
                  >
                    {stage.replace(/_/g, " ")}
                  </span>
                );
              })}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {isPublished && absoluteOpen ? (
                <a
                  href={absoluteOpen}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-zinc-950 hover:bg-emerald-400"
                >
                  Открыть магазин
                </a>
              ) : null}
              <Link
                href={`/client/stores/${orderId}/admin`}
                className="inline-flex items-center rounded-xl bg-white px-4 py-2 text-sm font-semibold text-zinc-950 hover:bg-zinc-100"
              >
                Open Store Admin
              </Link>
              <button
                type="button"
                disabled={Boolean(busy)}
                onClick={() => void action("regenerate")}
                className="rounded-xl border border-white/15 bg-white/[0.04] px-4 py-2 text-sm text-zinc-100 hover:bg-white/[0.08] disabled:opacity-50"
              >
                {busy === "regenerate" ? "…" : "Пересобрать"}
              </button>
              <button
                type="button"
                disabled={Boolean(busy) || !data.product_id}
                onClick={() => void action("publish")}
                className="rounded-xl border border-white/15 bg-white/[0.04] px-4 py-2 text-sm text-zinc-100 hover:bg-white/[0.08] disabled:opacity-50"
              >
                {busy === "publish" ? "…" : isPublished ? "Опубликовать снова" : "Опубликовать"}
              </button>
            </div>
            <p className="mt-3 text-xs text-zinc-500">
              Store Admin is the control panel for this shop — separate from Virtus Core
              Client Workspace. Product catalog tools arrive next.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Бриф (только чтение)
            </p>
            <ul className="mt-3 space-y-1 text-sm text-zinc-300">
              <li>Компания: {String(brief.company_name || "—")}</li>
              <li>Магазин: {String(brief.store_name || "—")}</li>
              <li>Категория: {String(brief.category || "—")}</li>
              <li>Каталог: ~{String(brief.catalog_size || "—")}</li>
              <li>Стиль: {String(brief.style || "—")}</li>
              <li>
                Оплата:{" "}
                {Array.isArray(brief.payments)
                  ? (brief.payments as string[]).join(", ")
                  : "—"}
              </li>
              <li>
                Доставка:{" "}
                {Array.isArray(brief.shipping)
                  ? (brief.shipping as string[]).join(", ")
                  : "—"}
              </li>
            </ul>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Activity log
            </p>
            <p className="mt-2 text-sm text-zinc-300">
              status: {data.factory_hook?.status || "—"}
              {data.product_id ? ` · ${data.product_id}` : ""}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              {data.factory_hook?.note || "—"}
            </p>
            <ul className="mt-3 max-h-48 space-y-1 overflow-y-auto font-mono text-[11px] text-zinc-500">
              {(data.generation_log || []).length === 0 ? (
                <li>Лог пока пуст</li>
              ) : (
                (data.generation_log || []).map((row, i) => (
                  <li key={`${row.ts || i}-${row.event || i}`}>
                    [{row.ts || "—"}] {row.event || "event"}
                  </li>
                ))
              )}
            </ul>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Версии
            </p>
            <ul className="mt-3 space-y-2">
              {(data.versions || []).length === 0 ? (
                <li className="text-sm text-zinc-500">Пока нет версий</li>
              ) : (
                (data.versions || []).map((v) => (
                  <li
                    key={v.version}
                    className="flex flex-wrap items-center justify-between gap-2 text-sm text-zinc-300"
                  >
                    <span>
                      v{v.version}
                      {data.version === v.version ? " (текущая)" : ""}
                      {v.created_at ? (
                        <span className="ml-2 text-xs text-zinc-500">
                          {v.created_at}
                        </span>
                      ) : null}
                    </span>
                    {data.version !== v.version ? (
                      <button
                        type="button"
                        disabled={Boolean(busy)}
                        onClick={() => void action("rollback", { version: v.version })}
                        className="rounded-lg border border-white/10 px-2 py-1 text-xs hover:bg-white/[0.06] disabled:opacity-50"
                      >
                        Откатить
                      </button>
                    ) : null}
                  </li>
                ))
              )}
            </ul>
          </div>

          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Админка магазина (R3 — скоро)
            </p>
            <ul className="grid gap-2 sm:grid-cols-2">
              {(data.r3_sections || []).map((s) => (
                <li
                  key={s.id}
                  className="rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3 opacity-70"
                >
                  <p className="text-sm font-medium text-white">{s.label}</p>
                  <p className="text-xs text-zinc-500">Скоро (R3)</p>
                </li>
              ))}
            </ul>
          </div>

          <Link
            href="/client/products"
            className="inline-flex text-sm text-emerald-300 hover:underline"
          >
            ← К продуктам
          </Link>
        </div>
      ) : null}
    </ClientWorkspaceShell>
  );
}
