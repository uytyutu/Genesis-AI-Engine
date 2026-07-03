"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "genesis_owner_checklist_v1";

type ChecklistItem = {
  id: string;
  label: string;
  done: boolean;
  optional?: boolean;
};

const DEFAULT_ITEMS: ChecklistItem[] = [
  { id: "system_check", label: "Проверить систему", done: false },
  { id: "create_product", label: "Создать первый продукт", done: false },
  { id: "preview_product", label: "Просмотреть результат", done: false },
  { id: "approve_product", label: "Одобрить продукт", done: false },
  { id: "publish_product", label: "Опубликовать продукт", done: false },
  {
    id: "payment_hub",
    label: "Подключить Payment Hub (когда появится первый клиент)",
    done: false,
    optional: true,
  },
];

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function loadItems(): ChecklistItem[] {
  if (typeof window === "undefined") return DEFAULT_ITEMS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_ITEMS;
    const parsed = JSON.parse(raw) as ChecklistItem[];
    return DEFAULT_ITEMS.map((item) => {
      const saved = parsed.find((p) => p.id === item.id);
      return saved ? { ...item, done: saved.done } : item;
    });
  } catch {
    return DEFAULT_ITEMS;
  }
}

function saveItems(items: ChecklistItem[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

type Props = {
  ownerName?: string;
};

export function OwnerWelcomeChecklist({ ownerName = "Владелец" }: Props) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<ChecklistItem[]>(DEFAULT_ITEMS);

  const syncFromApi = useCallback(async () => {
    try {
      const [checkRes, mcRes, productsRes] = await Promise.all([
        fetch(`${API}/api/owner/system-check`),
        fetch(`${API}/api/owner/mission-control`),
        fetch(`${API}/api/factory/products`),
      ]);
      const check = checkRes.ok ? await checkRes.json() : null;
      const mc = mcRes.ok ? await mcRes.json() : null;
      const products = productsRes.ok ? await productsRes.json() : null;
      const list = products?.products ?? [];

      setItems((prev) => {
        const next = prev.map((item) => {
          if (item.id === "system_check") return { ...item, done: Boolean(check?.ready) };
          if (item.id === "create_product") return { ...item, done: list.length > 0 };
          if (item.id === "preview_product") {
            return {
              ...item,
              done: list.some(
                (p: { status?: string; quality_percent?: number }) =>
                  p.status === "ready" || (p.quality_percent ?? 0) >= 50,
              ),
            };
          }
          if (item.id === "approve_product") {
            return { ...item, done: list.some((p: { owner_approved?: boolean }) => p.owner_approved) };
          }
          if (item.id === "publish_product") {
            return { ...item, done: list.some((p: { published?: boolean }) => p.published) };
          }
          if (item.id === "payment_hub") {
            return { ...item, done: Boolean(mc?.payment_connected) };
          }
          return item;
        });
        saveItems(next);
        return next;
      });
    } catch {
      /* backend offline */
    }
  }, []);

  useEffect(() => {
    const loaded = loadItems();
    setItems(loaded);
    const dismissed = sessionStorage.getItem("genesis_checklist_dismissed");
    const allDone = loaded.every((i) => i.done || i.optional);
    if (!dismissed && !allDone) {
      setOpen(true);
    }
    syncFromApi();
  }, [syncFromApi]);

  const toggle = (id: string) => {
    setItems((prev) => {
      const next = prev.map((i) => (i.id === id ? { ...i, done: !i.done } : i));
      saveItems(next);
      return next;
    });
  };

  const close = () => {
    sessionStorage.setItem("genesis_checklist_dismissed", "1");
    setOpen(false);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-genesis-border bg-genesis-panel p-6 shadow-2xl">
        <p className="text-xs uppercase tracking-[0.3em] text-genesis-muted">Чек-лист владельца</p>
        <h2 className="mt-2 text-xl font-semibold">Добро пожаловать, {ownerName}.</h2>
        <p className="mt-2 text-sm text-genesis-muted">Сегодня необходимо:</p>
        <ul className="mt-4 space-y-3">
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => toggle(item.id)}
                className="flex w-full items-start gap-3 text-left text-sm"
              >
                <span
                  className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border ${
                    item.done
                      ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                      : "border-genesis-border text-genesis-muted"
                  }`}
                >
                  {item.done ? "✓" : ""}
                </span>
                <span className={item.done ? "text-genesis-muted line-through" : ""}>
                  {item.label}
                </span>
              </button>
            </li>
          ))}
        </ul>
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={syncFromApi}
            className="rounded-lg border border-genesis-border px-4 py-2 text-sm"
          >
            Обновить
          </button>
          <button
            type="button"
            onClick={close}
            className="rounded-lg bg-genesis-accent px-4 py-2 text-sm font-medium text-white"
          >
            Продолжить
          </button>
        </div>
      </div>
    </div>
  );
}
