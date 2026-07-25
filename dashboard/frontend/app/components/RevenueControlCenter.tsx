"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BRAND_NAME } from "../lib/publicBrand";
import { RevenueSourcesPanel, type RevenueSourcesCenter } from "./RevenueSourcesPanel";
import { RevenueLabCeoPanel, type CeoAction, type RevenueLabBrief } from "./RevenueLabCeoPanel";
import { Digistore24LabPanel, type DigistoreCapability } from "./Digistore24LabPanel";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type LabFinding = {
  id: string;
  name: string;
  type: string;
  connected: boolean;
  status: string;
  status_ru: string;
  model_ru: string;
  income_hypothesis_ru: string;
  ceo_action_ru: string;
  confidence: string;
  reality_note_ru?: string;
  uses_farm?: boolean;
  uses_commercial_api?: boolean;
};

type PackageRow = {
  id: string;
  name: string;
  price_eur: number;
  balance_eur?: number;
  note_ru?: string;
  best_for_ru?: string;
  scopes?: string[];
};

type Contours = {
  title_ru?: string;
  lab_rule_ru?: string;
  contours?: { id: string; role: string; note_ru: string }[];
};

export function RevenueControlCenter() {
  const [sources, setSources] = useState<RevenueSourcesCenter | null>(null);
  const [brief, setBrief] = useState<RevenueLabBrief | null>(null);
  const [findings, setFindings] = useState<LabFinding[]>([]);
  const [digistore, setDigistore] = useState<DigistoreCapability | null>(null);
  const [packages, setPackages] = useState<PackageRow[]>([]);
  const [contours, setContours] = useState<Contours | null>(null);
  const [loadError, setLoadError] = useState("");
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");

  const refresh = useCallback(async () => {
    setLoadError("");
    setMsg("");
    setBusy("refresh");
    const errors: string[] = [];

    try {
      const srcRes = await fetch(`${API}/api/farm/revenue-sources/center`);
      if (srcRes.ok) {
        setSources(await srcRes.json());
      } else {
        errors.push(`источники ${srcRes.status}`);
      }
    } catch {
      errors.push("источники недоступны");
    }

    try {
      // Farm route — no owner gate (Genesis.exe local desk). Fallback to admin.
      let briefRes = await fetch(`${API}/api/farm/revenue-lab/brief`);
      if (!briefRes.ok) {
        briefRes = await fetch(`${API}/api/v1/admin/lab/brief`, {
          credentials: "include",
        });
      }
      if (briefRes.ok) {
        const body = await briefRes.json();
        setBrief({
          title_ru: body.title_ru ?? "Revenue Lab",
          headline_ru: body.headline_ru ?? "",
          rule_ru: body.rule_ru,
          ceo_actions: (body.ceo_actions ?? []) as CeoAction[],
        });
        setFindings(Array.isArray(body.findings) ? body.findings : []);
        if (body.digistore24) setDigistore(body.digistore24 as DigistoreCapability);
        if (body.contours) setContours(body.contours);
        setMsg("Обновлено · Lab показывает живые пути дохода (Country Desk + ключи).");
      } else if (briefRes.status === 403) {
        errors.push("Lab: нужен owner-доступ");
      } else {
        errors.push(`Lab ${briefRes.status}`);
      }
    } catch {
      errors.push("Lab недоступна");
    }

    try {
      const pkgRes = await fetch(`${API}/api/v1/packages`);
      if (pkgRes.ok) {
        const body = await pkgRes.json();
        const list = Array.isArray(body.packages)
          ? body.packages
          : Array.isArray(body)
            ? body
            : Object.values(body.packages ?? body ?? {});
        setPackages(list as PackageRow[]);
      }
    } catch {
      /* optional */
    }

    if (errors.length) setLoadError(errors.join(" · "));
    setBusy("");
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const runScan = async () => {
    setBusy("scan");
    setMsg("");
    try {
      let res = await fetch(`${API}/api/farm/revenue-lab/scan`, { method: "POST" });
      if (!res.ok) {
        res = await fetch(`${API}/api/v1/admin/lab/scan`, {
          method: "POST",
          credentials: "include",
        });
      }
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMsg(
          body.detail === "owner_only"
            ? "Нужен owner-доступ для скана."
            : `Скан: ${res.status}`,
        );
        return;
      }
      setFindings(Array.isArray(body.findings) ? body.findings : []);
      setBrief({
        title_ru: "Revenue Lab → действия CEO",
        headline_ru: body.headline_ru ?? "",
        rule_ru: body.rule_ru,
        ceo_actions: (body.ceo_actions ?? []) as CeoAction[],
      });
      if (body.digistore24) setDigistore(body.digistore24 as DigistoreCapability);
      if (body.contours) setContours(body.contours);
      setMsg(
        `Скан ${body.scanned_at ? String(body.scanned_at).slice(11, 19) : "OK"} · ` +
          `${(body.findings || []).length} путей · ${(body.ceo_actions || []).length} действий CEO`,
      );
    } catch {
      setMsg("Скан не удался — backend не отвечает (Genesis.exe → Запустить).");
    } finally {
      setBusy("");
    }
  };

  const needKey = findings.filter((f) => !f.connected);
  const ready = findings.filter((f) => f.connected);

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6">
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/35 via-genesis-panel to-genesis-bg p-6 sm:p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-400/80">{BRAND_NAME}</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">Доход · Revenue Lab</h1>
          <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
            Lab ищет пути к доходу внутри Virtus: Country Desk (лиды 24/7), Stripe, Digistore,
            Recommendation Engine. Это не скрапинг интернета. «Обновить» / «Сканировать» перечитывают
            живое состояние — ключ ≠ деньги.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void runScan()}
              disabled={busy === "scan"}
              className="rounded-lg border border-amber-500/40 bg-amber-950/40 px-4 py-2 text-sm text-amber-50 hover:bg-amber-900/50 disabled:opacity-50"
            >
              {busy === "scan" ? "Скан…" : "Сканировать возможности"}
            </button>
            <button
              type="button"
              onClick={() => void refresh()}
              className="rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/90 hover:bg-white/10"
            >
              Обновить
            </button>
            <Link
              href="/finance"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm text-genesis-muted hover:text-white"
            >
              Финансы →
            </Link>
            <Link
              href="/"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm text-genesis-muted hover:text-white"
            >
              Ферма →
            </Link>
          </div>
          {msg ? <p className="mt-3 text-xs text-emerald-200">{msg}</p> : null}
          {loadError ? <p className="mt-2 text-xs text-amber-200/90">{loadError}</p> : null}
        </header>

        {contours?.contours?.length ? (
          <section className="genesis-card space-y-2 border-white/10 p-5">
            <h2 className="text-sm font-semibold text-white">{contours.title_ru ?? "Контуры"}</h2>
            {contours.lab_rule_ru ? (
              <p className="text-[11px] text-genesis-muted">{contours.lab_rule_ru}</p>
            ) : null}
            <ul className="space-y-2">
              {contours.contours.map((c) => (
                <li key={c.id} className="rounded-lg border border-white/5 bg-black/20 px-3 py-2 text-xs">
                  <span className="font-medium text-white/90">{c.id}</span>
                  <span className="ml-2 text-[10px] uppercase text-genesis-muted">{c.role}</span>
                  <p className="mt-1 text-genesis-muted">{c.note_ru}</p>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {brief ? <RevenueLabCeoPanel data={brief} /> : null}

        {digistore ? <Digistore24LabPanel data={digistore} /> : null}

        <section className="genesis-card space-y-4 border-sky-500/25 p-5">
          <div>
            <h2 className="text-sm font-semibold text-sky-100">Что Lab смотрит</h2>
            <p className="mt-1 text-[11px] text-genesis-muted">
              Найдено / не подключено / ключи на месте. Гипотеза ≠ запись в Ledger.
            </p>
          </div>
          {!findings.length ? (
            <p className="text-xs text-genesis-muted">
              Нажмите «Сканировать возможности» — список кандидатов появится здесь.
            </p>
          ) : (
            <>
              <p className="text-[11px] text-white/70">
                Нужен ключ / аккаунт: <span className="text-amber-200">{needKey.length}</span>
                {" · "}
                Ключи на месте: <span className="text-emerald-200">{ready.length}</span>
              </p>
              <ul className="space-y-2">
                {findings.map((f) => (
                  <li
                    key={f.id}
                    className={`rounded-lg border px-3 py-2.5 text-xs ${
                      f.connected
                        ? "border-emerald-500/30 bg-emerald-950/15"
                        : "border-amber-500/30 bg-amber-950/10"
                    }`}
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <p className="font-medium text-white">{f.name}</p>
                      <span className="text-[10px] text-genesis-muted">
                        {f.connected ? "✅" : "🔑"} {f.status_ru}
                      </span>
                    </div>
                    <p className="mt-1 text-white/85">{f.model_ru}</p>
                    <p className="mt-1 text-[11px] text-genesis-muted">{f.income_hypothesis_ru}</p>
                    {!f.connected ? (
                      <p className="mt-1 text-amber-100/90">→ {f.ceo_action_ru}</p>
                    ) : null}
                    <p className="mt-1 font-mono text-[10px] text-violet-200/80">{f.confidence}</p>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>

        {sources ? <RevenueSourcesPanel data={sources} /> : null}

        <section className="genesis-card space-y-3 border-violet-500/25 p-5">
          <div>
            <h2 className="text-sm font-semibold text-violet-100">Commercial API · пакеты</h2>
            <p className="mt-1 text-[11px] text-genesis-muted">
              Продажа своих возможностей (Audit / Leads). Gateway заморожен до первого API-клиента —
              здесь цены и смысл пакетов.
            </p>
          </div>
          {!packages.length ? (
            <p className="text-xs text-genesis-muted">Пакеты не загрузились — проверьте backend.</p>
          ) : (
            <ul className="grid gap-2 sm:grid-cols-3">
              {packages.map((p) => (
                <li key={p.id} className="rounded-lg border border-white/10 bg-black/20 px-3 py-3 text-xs">
                  <p className="font-medium text-white">
                    {p.name}{" "}
                    <span className="text-emerald-200">{Number(p.price_eur).toFixed(0)} €</span>
                  </p>
                  {p.note_ru ? <p className="mt-1 text-genesis-muted">{p.note_ru}</p> : null}
                  {p.best_for_ru ? <p className="mt-1 text-violet-100/80">{p.best_for_ru}</p> : null}
                </li>
              ))}
            </ul>
          )}
          <p className="text-[10px] text-genesis-muted">
            Публичный прайс:{" "}
            <a className="text-sky-300 hover:underline" href={`${API}/api/v1/pricing`}>
              /api/v1/pricing
            </a>
          </p>
        </section>
      </div>
    </main>
  );
}
