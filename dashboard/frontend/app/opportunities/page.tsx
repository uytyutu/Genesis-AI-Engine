"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Source = { id: string; label: string; enabled: boolean; count_today?: number };
type SourceToday = { source_id: string; label: string; enabled: boolean; count_today?: number };
type OppType = { id: string; label: string };
type StatusOpt = { id: string; label: string };

type Opportunity = {
  id: string;
  opportunity_type: string;
  source_id: string;
  company_name: string;
  contact: string;
  fit_reason: string;
  score: number;
  status: string;
  status_label: string;
  proposed_message: string;
  notes: string;
  potential_value_eur: number;
  website_url?: string;
  outreach_status?: string;
  found_at: string;
};

type Dashboard = {
  date: string;
  total_today: number;
  potential_value_eur: number;
  sources_today: SourceToday[];
  pipeline_count: number;
  won_count: number;
  revenue_eur: number;
  top_today: Opportunity[];
  kpi_note: string;
};

const EMPTY_FORM = {
  source_id: "manual",
  opportunity_type: "lead",
  company_name: "",
  contact: "",
  fit_reason: "",
  website_url: "",
  potential_value_eur: "650",
  notes: "",
};

export default function OpportunitiesPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [types, setTypes] = useState<OppType[]>([]);
  const [statuses, setStatuses] = useState<StatusOpt[]>([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [preparing, setPreparing] = useState("");
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [dashRes, listRes, srcRes] = await Promise.all([
        fetch(`${API}/api/opportunities/dashboard`),
        fetch(`${API}/api/opportunities?limit=50`),
        fetch(`${API}/api/opportunities/sources`),
      ]);
      if (dashRes.ok) setDashboard(await dashRes.json());
      if (listRes.ok) {
        const body = await listRes.json();
        setOpportunities(body.opportunities ?? []);
      }
      if (srcRes.ok) {
        const body = await srcRes.json();
        setSources(body.sources ?? []);
        setTypes(body.types ?? []);
        setStatuses(body.statuses ?? []);
      }
    } catch {
      setMessage("Не удалось загрузить данные. Проверьте backend.");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/opportunities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          potential_value_eur: parseFloat(form.potential_value_eur) || 0,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(body.detail ?? "Ошибка сохранения");
        return;
      }
      setForm({ ...EMPTY_FORM, source_id: form.source_id });
      setMessage("Добавлено в журнал.");
      refresh();
    } catch {
      setMessage("Ошибка сети");
    } finally {
      setSaving(false);
    }
  }

  async function updateStatus(id: string, status: string) {
    await fetch(`${API}/api/opportunities/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    refresh();
  }

  async function prepareProposal(id: string, websiteUrl?: string) {
    setPreparing(id);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/acquisition/opportunities/${id}/prepare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ website_url: websiteUrl || undefined }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Готово" : "Ошибка"));
      if (res.ok) {
        window.location.href = "/acquisition";
      }
    } catch {
      setMessage("Ошибка подготовки КП");
    } finally {
      setPreparing("");
    }
  }

  const enabledSources = sources.filter((s) => s.enabled);

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-3xl space-y-6">
        <header className="rounded-2xl border border-violet-500/25 bg-gradient-to-br from-violet-950/30 to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-violet-300/80">Opportunity Engine</p>
          <h1 className="mt-2 text-2xl font-semibold">Возможности компании</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Журнал лидов Mission 1.5 — добавьте компанию, подготовьте КП в{" "}
            <Link href="/acquisition" className="text-emerald-400 underline">
              Acquisition Studio
            </Link>
            .
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link href="/acquisition" className="rounded-lg border border-emerald-500/40 px-3 py-1.5 hover:bg-genesis-elevated/40">
              Acquisition Studio
            </Link>
            <Link href="/site" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Публичная страница
            </Link>
            <Link href="/order" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Форма заказа
            </Link>
          </div>
        </header>

        {dashboard && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold">Найдено сегодня · {dashboard.date}</h2>
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Stat label="Всего" value={String(dashboard.total_today)} />
              <Stat label="В воронке" value={String(dashboard.pipeline_count)} />
              <Stat label="Потенциал" value={formatEur(dashboard.potential_value_eur)} />
              <Stat label="Продажи" value={String(dashboard.won_count)} />
            </div>
            <ul className="mt-4 space-y-1.5 text-sm">
              {dashboard.sources_today.map((s) => (
                <li key={s.source_id} className="flex justify-between gap-3">
                  <span className={s.enabled ? "" : "text-genesis-muted line-through"}>
                    {s.label}
                    {!s.enabled && " (выкл.)"}
                  </span>
                  <span className="tabular-nums font-medium">{s.count_today ?? 0}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-[11px] text-genesis-muted">{dashboard.kpi_note}</p>
          </section>
        )}

        <section className="genesis-card p-5">
          <h2 className="text-sm font-semibold">Добавить возможность</h2>
          <form onSubmit={handleCreate} className="mt-4 space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-xs text-genesis-muted">
                Источник
                <select
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                  value={form.source_id}
                  onChange={(e) => setForm({ ...form, source_id: e.target.value })}
                >
                  {enabledSources.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-xs text-genesis-muted">
                Тип
                <select
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                  value={form.opportunity_type}
                  onChange={(e) => setForm({ ...form, opportunity_type: e.target.value })}
                >
                  {types.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="block text-xs text-genesis-muted">
              Компания *
              <input
                required
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                placeholder="Автосервис Müller"
              />
            </label>
            <label className="block text-xs text-genesis-muted">
              Контакт
              <input
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                value={form.contact}
                onChange={(e) => setForm({ ...form, contact: e.target.value })}
                placeholder="телефон, email или ссылка Maps"
              />
            </label>
            <label className="block text-xs text-genesis-muted">
              Сайт (URL)
              <input
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                value={form.website_url}
                onChange={(e) => setForm({ ...form, website_url: e.target.value })}
                placeholder="https://beispiel.de"
              />
            </label>
            <label className="block text-xs text-genesis-muted">
              Почему подходит
              <input
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                value={form.fit_reason}
                onChange={(e) => setForm({ ...form, fit_reason: e.target.value })}
                placeholder="Нет сайта, только страница в Google Maps"
              />
            </label>
            <label className="block text-xs text-genesis-muted">
              Потенциальная ценность (€)
              <input
                type="number"
                min={0}
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                value={form.potential_value_eur}
                onChange={(e) => setForm({ ...form, potential_value_eur: e.target.value })}
              />
            </label>
            <button
              type="submit"
              disabled={saving}
              className="w-full rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              {saving ? "Сохранение…" : "Добавить в журнал"}
            </button>
            {message && <p className="text-xs text-genesis-muted">{message}</p>}
          </form>
        </section>

        <section className="genesis-card p-5">
          <h2 className="text-sm font-semibold">Журнал</h2>
          {opportunities.length === 0 ? (
            <p className="mt-3 text-sm text-genesis-muted">
              Пока пусто. Добавьте первую реальную возможность — из Google Maps или вручную.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {opportunities.map((o) => (
                <li
                  key={o.id}
                  className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-medium">{o.company_name}</p>
                      <p className="text-xs text-genesis-muted">
                        {o.source_id} · {o.opportunity_type} · score {o.score}
                      </p>
                    </div>
                    <span className="rounded-full bg-genesis-elevated px-2 py-0.5 text-[11px]">
                      {o.status_label}
                    </span>
                  </div>
                  {o.fit_reason && (
                    <p className="mt-2 text-sm text-genesis-muted">{o.fit_reason}</p>
                  )}
                  {o.contact && (
                    <p className="mt-1 text-xs text-genesis-muted">Контакт: {o.contact}</p>
                  )}
                  <div className="mt-3 flex flex-wrap gap-2 items-center">
                    <select
                      className="rounded-lg border border-genesis-border bg-genesis-bg px-2 py-1 text-xs"
                      value={o.status}
                      onChange={(e) => updateStatus(o.id, e.target.value)}
                    >
                      {statuses.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      disabled={preparing === o.id}
                      onClick={() => prepareProposal(o.id, o.website_url)}
                      className="rounded-lg bg-emerald-700/80 px-2 py-1 text-xs text-white disabled:opacity-50"
                    >
                      {preparing === o.id ? "…" : "Подготовить КП"}
                    </button>
                    {o.outreach_status === "pending_approval" && (
                      <Link href="/acquisition" className="text-xs text-emerald-400">
                        → Approve
                      </Link>
                    )}
                    <span className="text-xs text-genesis-muted self-center">
                      {formatEur(o.potential_value_eur)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 p-3 text-center">
      <p className="text-lg font-bold tabular-nums">{value}</p>
      <p className="text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}
