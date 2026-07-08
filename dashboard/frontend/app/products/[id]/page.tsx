"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChecksList } from "../../components/ChecksList";
import { GenesisCard } from "../../components/GenesisCard";
import { formatApiDetail } from "../../lib/formatApiError";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type HandoffStep = { id: string; label: string; done: boolean };

type Product = {
  product_id: string;
  product_type: string;
  business_name: string;
  description: string;
  status_label: string;
  revision: number;
  preview_url: string;
  checks: { id: string; label: string; ok: boolean; pending?: boolean }[];
  owner_approved: boolean;
  published: boolean;
  delivered_to_client: boolean;
  client_message: string;
  handoff_checklist: HandoffStep[];
};

export default function ProductPage() {
  const params = useParams();
  const productId = String(params.id ?? "");
  const [product, setProduct] = useState<Product | null>(null);
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [loadError, setLoadError] = useState("");

  const refresh = useCallback(async () => {
    setLoadError("");
    try {
      const res = await fetch(`${API}/api/factory/products/${productId}`);
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        setProduct(body);
      } else {
        setProduct(null);
        setLoadError(formatApiDetail(body.detail, "Продукт не найден"));
      }
    } catch {
      setProduct(null);
      setLoadError("Не удалось связаться с Virtus Core.");
    }
  }, [productId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function improve() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/factory/products/${productId}/improve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(formatApiDetail(body.detail));
      } else {
        setProduct(body);
        setMessage(`Версия ${body.revision} готова. Проверьте превью и одобрите, если готовы отправить клиенту.`);
        setFeedback("");
      }
    } catch {
      setMessage("Не удалось связаться с Virtus Core.");
    } finally {
      setBusy(false);
    }
  }

  async function approve() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/factory/products/${productId}/approve`, { method: "POST" });
      const body = await res.json();
      if (!res.ok) {
        setMessage(formatApiDetail(body.detail));
      } else {
        setProduct(body);
        setMessage("Одобрено — следующий шаг: подготовить к передаче клиенту.");
      }
    } catch {
      setMessage("Не удалось связаться с Virtus Core.");
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/factory/products/${productId}/publish`, { method: "POST" });
      const body = await res.json();
      if (!res.ok) {
        setMessage(formatApiDetail(body.detail));
      } else {
        setProduct(body);
        setMessage("Готово к передаче — скачайте ZIP и отправьте клиенту.");
      }
    } catch {
      setMessage("Не удалось связаться с Virtus Core.");
    } finally {
      setBusy(false);
    }
  }

  async function markDelivered() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/factory/products/${productId}/delivered`, { method: "POST" });
      const body = await res.json();
      if (!res.ok) {
        setMessage(formatApiDetail(body.detail));
      } else {
        setProduct(body);
        setMessage("✔ Передано клиенту. Первый заказ завершён — зафиксируйте оплату вручную, если уже получили.");
      }
    } catch {
      setMessage("Не удалось связаться с Virtus Core.");
    } finally {
      setBusy(false);
    }
  }

  async function copyClientMessage() {
    if (!product?.client_message) return;
    try {
      await navigator.clipboard.writeText(product.client_message);
      setMessage("Сообщение для клиента скопировано — вставьте в WhatsApp или email и приложите ZIP.");
    } catch {
      setMessage("Не удалось скопировать — выделите текст вручную.");
    }
  }

  function downloadZip() {
    window.location.href = `${API}/api/factory/products/${productId}/export`;
    setTimeout(refresh, 800);
  }

  if (!product) {
    return (
      <main className="min-h-screen pb-12 text-center">
        <p className={`mt-12 ${loadError ? "text-red-400" : "text-genesis-muted"}`}>
          {loadError || "Загрузка…"}
        </p>
        {loadError && (
          <p className="mt-4 text-sm">
            <Link href="/" className="text-genesis-accent hover:underline">
              ← Virtus Core
            </Link>
          </p>
        )}
      </main>
    );
  }

  const previewHref = `${API}/api/factory/products/${productId}/preview`;
  const step = !product.owner_approved
    ? 1
    : !product.published
      ? 2
      : !product.delivered_to_client
        ? 3
        : 4;

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-lg space-y-5">
        <header className="genesis-card p-6 text-center">
          <p className="genesis-label">R1.5 · Первый завершённый заказ</p>
          <h1 className="mt-2 text-2xl font-bold">{product.business_name}</h1>
          <p className="mt-1 text-genesis-muted">{product.product_type}</p>
        </header>

        <GenesisCard title="Путь заказа">
          <ol className="space-y-2 text-sm">
            <Step n={1} done={step > 1} active={step === 1} label="Просмотреть превью" />
            <Step n={2} done={step > 2} active={step === 2} label="Одобрить (Owner Approved)" />
            <Step n={3} done={step > 3} active={step === 3} label="Подготовить к передаче (Publish)" />
            <Step n={4} done={product.delivered_to_client} active={step === 4} label="Передать клиенту (ZIP)" />
          </ol>
        </GenesisCard>

        <GenesisCard>
          <Row label="Статус" value={product.status_label} />
          <Row label="Версия" value={String(product.revision)} />
          <div className="mt-3">
            <p className="genesis-label mb-2">Проверки</p>
            <ChecksList checks={product.checks} />
          </div>
        </GenesisCard>

        {message && (
          <p className="rounded-xl border border-genesis-border bg-genesis-elevated px-4 py-3 text-sm text-genesis-muted">
            {message}
          </p>
        )}

        <a
          href={previewHref}
          target="_blank"
          rel="noreferrer"
          className="block rounded-2xl bg-gradient-to-r from-genesis-accent to-blue-600 py-3 text-center font-semibold text-white shadow-glow hover:opacity-90"
        >
          Открыть превью
        </a>

        {!product.owner_approved && (
          <button
            type="button"
            disabled={busy}
            onClick={approve}
            className="w-full rounded-2xl border border-emerald-500/50 bg-emerald-950/30 py-3 font-semibold text-emerald-300 hover:bg-emerald-950/50 disabled:opacity-50"
          >
            ✔ Готов отправить клиенту
          </button>
        )}

        {product.owner_approved && !product.published && (
          <button
            type="button"
            disabled={busy}
            onClick={publish}
            className="w-full rounded-2xl bg-genesis-accent py-3 font-semibold text-white hover:bg-genesis-accent-soft disabled:opacity-50"
          >
            📦 Подготовить к передаче
          </button>
        )}

        {product.published && (
          <GenesisCard title="Передача клиенту" subtitle="R1.5 — без Payment Hub, реальная доставка">
            <ul className="mb-4 space-y-2 text-sm">
              {product.handoff_checklist.map((item) => (
                <li key={item.id} className="flex items-center gap-3">
                  <span className={item.done ? "text-emerald-400" : "text-genesis-muted"}>
                    {item.done ? "✔" : "○"}
                  </span>
                  <span className={item.done ? "text-genesis-text" : "text-genesis-muted"}>{item.label}</span>
                </li>
              ))}
            </ul>

            <div className="grid gap-2 sm:grid-cols-2">
              <button
                type="button"
                disabled={busy || product.delivered_to_client}
                onClick={downloadZip}
                className="rounded-xl border border-genesis-accent/40 bg-genesis-accent/10 py-3 text-sm font-semibold text-genesis-accent hover:bg-genesis-accent/20 disabled:opacity-50"
              >
                ⬇ Скачать проект (ZIP)
              </button>
              <button
                type="button"
                disabled={busy || product.delivered_to_client}
                onClick={copyClientMessage}
                className="rounded-xl border border-genesis-border py-3 text-sm font-semibold hover:border-genesis-accent/40 disabled:opacity-50"
              >
                📋 Сообщение клиенту
              </button>
            </div>

            {product.client_message && (
              <pre className="mt-3 max-h-40 overflow-auto whitespace-pre-wrap rounded-xl bg-genesis-bg p-3 text-xs text-genesis-muted">
                {product.client_message}
              </pre>
            )}

            {!product.delivered_to_client ? (
              <button
                type="button"
                disabled={busy}
                onClick={markDelivered}
                className="mt-4 w-full rounded-2xl border border-emerald-500/50 bg-emerald-950/30 py-3 font-semibold text-emerald-300 hover:bg-emerald-950/50 disabled:opacity-50"
              >
                ✔ Передано клиенту
              </button>
            ) : (
              <p className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 px-4 py-3 text-center text-sm text-emerald-200">
                ✔ Заказ завершён — сайт передан клиенту
              </p>
            )}

            <p className="mt-3 text-xs text-genesis-muted">
              Оплату примите вручную (перевод, наличные). Payment Hub — после первого реального дохода.
            </p>
          </GenesisCard>
        )}

        <GenesisCard title="Запросить улучшение">
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={4}
            placeholder="Например: строже, больше синего, добавь калькулятор…"
            className="w-full rounded-xl border border-genesis-border bg-genesis-bg px-3 py-2 text-sm outline-none focus:border-genesis-accent"
            disabled={product.delivered_to_client}
          />
          <button
            type="button"
            disabled={busy || feedback.trim().length < 2 || product.delivered_to_client}
            onClick={improve}
            className="mt-3 w-full rounded-xl border border-genesis-border py-3 font-semibold hover:border-genesis-accent disabled:opacity-50"
          >
            {busy ? "Улучшаем…" : "Improve"}
          </button>
        </GenesisCard>

        <p className="text-center text-sm">
          <Link href="/" className="text-genesis-accent hover:underline">
            ← Virtus Core
          </Link>
        </p>
      </div>
    </main>
  );
}

function Step({
  n,
  label,
  done,
  active,
}: {
  n: number;
  label: string;
  done: boolean;
  active: boolean;
}) {
  return (
    <li className={`flex items-center gap-3 ${active ? "text-white" : "text-genesis-muted"}`}>
      <span
        className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
          done ? "bg-emerald-500/20 text-emerald-400" : active ? "bg-genesis-accent/20 text-genesis-accent" : "bg-genesis-elevated"
        }`}
      >
        {done ? "✔" : n}
      </span>
      {label}
    </li>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <span className="text-genesis-muted">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
