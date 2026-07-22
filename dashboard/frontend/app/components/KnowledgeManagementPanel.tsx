"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button, Field, Input, Textarea } from "./ui";
import {
  KNOWLEDGE_CATEGORIES,
  KNOWLEDGE_CATEGORY_META,
  type KnowledgeCategoryId,
} from "../lib/knowledgeCategories";
import { PortalApiError, portalFetch } from "../lib/portalApi";

export type KnowledgeItem = {
  knowledge_id: string;
  category: string;
  title: string;
  content: string;
  updated_at?: string;
};

function isCategory(value: string): value is KnowledgeCategoryId {
  return (KNOWLEDGE_CATEGORIES as readonly string[]).includes(value);
}

export function KnowledgeManagementPanel() {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [selected, setSelected] = useState<KnowledgeCategoryId | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);
  const [needsProfile, setNeedsProfile] = useState(false);

  const [editId, setEditId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  const run = useCallback(async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await fn();
    } catch (err) {
      if (err instanceof PortalApiError) {
        if (err.status === 401) {
          setNeedsAuth(true);
          setError("Sign in required — open First Run to continue.");
        } else if (err.detail === "profile_required") {
          setNeedsProfile(true);
          setError("Complete Business Profile in First Run first.");
        } else {
          setError(err.detail);
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("unexpected_error");
      }
    } finally {
      setBusy(false);
    }
  }, []);

  const load = useCallback(async () => {
    await run(async () => {
      const rows = await portalFetch<KnowledgeItem[]>("/portal/chatbot/knowledge");
      setItems(rows);
      setNeedsAuth(false);
      setNeedsProfile(false);
    });
  }, [run]);

  useEffect(() => {
    void load();
  }, [load]);

  const byCategory = useMemo(() => {
    const map = new Map<KnowledgeCategoryId, KnowledgeItem[]>();
    for (const cat of KNOWLEDGE_CATEGORIES) map.set(cat, []);
    for (const item of items) {
      if (!isCategory(item.category)) continue;
      map.get(item.category)?.push(item);
    }
    return map;
  }, [items]);

  const filledCount = useMemo(
    () => KNOWLEDGE_CATEGORIES.filter((c) => (byCategory.get(c)?.length ?? 0) > 0).length,
    [byCategory],
  );
  const readinessPct = Math.round((filledCount / KNOWLEDGE_CATEGORIES.length) * 100);

  const categoryItems = selected ? byCategory.get(selected) ?? [] : [];
  const meta = selected ? KNOWLEDGE_CATEGORY_META[selected] : null;

  const resetForm = () => {
    setEditId(null);
    setTitle("");
    setContent("");
  };

  const openCategory = (cat: KnowledgeCategoryId) => {
    setSelected(cat);
    resetForm();
    setNotice(null);
    setError(null);
  };

  const startEdit = (item: KnowledgeItem) => {
    setEditId(item.knowledge_id);
    setTitle(item.title);
    setContent(item.content);
    setNotice(null);
    setError(null);
  };

  const save = () =>
    run(async () => {
      if (!selected) return;
      const cleanTitle = title.trim();
      const cleanContent = content.trim();
      if (!cleanTitle) throw new PortalApiError(400, "title_required");
      if (!cleanContent) throw new PortalApiError(400, "content_required");

      if (editId) {
        await portalFetch(`/portal/chatbot/knowledge/${editId}`, {
          method: "PUT",
          body: JSON.stringify({
            title: cleanTitle,
            content: cleanContent,
          }),
        });
        setNotice("Saved.");
      } else {
        await portalFetch("/portal/chatbot/knowledge", {
          method: "POST",
          body: JSON.stringify({
            category: selected,
            title: cleanTitle,
            content: cleanContent,
          }),
        });
        setNotice("Added to Business Knowledge.");
      }
      resetForm();
      const rows = await portalFetch<KnowledgeItem[]>("/portal/chatbot/knowledge");
      setItems(rows);
    });

  const remove = (knowledgeId: string) =>
    run(async () => {
      await portalFetch(`/portal/chatbot/knowledge/${knowledgeId}`, {
        method: "DELETE",
      });
      if (editId === knowledgeId) resetForm();
      setNotice("Removed.");
      const rows = await portalFetch<KnowledgeItem[]>("/portal/chatbot/knowledge");
      setItems(rows);
    });

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-1 py-2">
      <header className="space-y-2">
        <Badge>Vector · Knowledge</Badge>
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Business Knowledge
        </h1>
        <p className="text-sm text-zinc-400">
          Keep facts current so Vector answers from your real business — not from
          guesses. This screen only edits Knowledge.
        </p>
      </header>

      <section
        className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"
        aria-label="Knowledge readiness"
      >
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-zinc-500">
              Readiness
            </p>
            <p className="text-2xl font-semibold text-white">{readinessPct}%</p>
            <p className="text-sm text-zinc-500">
              {filledCount} of {KNOWLEDGE_CATEGORIES.length} categories have facts
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => void load()} disabled={busy}>
              Refresh
            </Button>
            <Link
              href="/projects/chatbot/setup"
              className="inline-flex items-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
            >
              First Run
            </Link>
          </div>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-black/40">
          <div
            className="h-full rounded-full bg-emerald-400/80 transition-all"
            style={{ width: `${readinessPct}%` }}
          />
        </div>
      </section>

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
          {needsAuth || needsProfile ? (
            <>
              {" "}
              <Link href="/projects/chatbot/setup" className="underline">
                Open First Run
              </Link>
            </>
          ) : null}
        </p>
      ) : null}
      {notice ? (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
          {notice}
        </p>
      ) : null}

      {!selected ? (
        <section aria-label="Knowledge overview">
          <h2 className="mb-3 text-lg font-medium text-white">Categories</h2>
          <ul className="grid gap-3 sm:grid-cols-2">
            {KNOWLEDGE_CATEGORIES.map((cat) => {
              const rows = byCategory.get(cat) ?? [];
              const filled = rows.length > 0;
              const info = KNOWLEDGE_CATEGORY_META[cat];
              return (
                <li key={cat}>
                  <button
                    type="button"
                    onClick={() => openCategory(cat)}
                    className="flex w-full flex-col gap-1 rounded-2xl border border-white/10 bg-black/20 px-4 py-4 text-left transition hover:border-white/25 hover:bg-white/[0.04]"
                  >
                    <span className="flex items-center justify-between gap-2">
                      <span className="font-medium text-white">{info.label}</span>
                      <span
                        className={`text-xs ${filled ? "text-emerald-300" : "text-zinc-500"}`}
                      >
                        {filled ? `${rows.length} fact${rows.length === 1 ? "" : "s"}` : "Empty"}
                      </span>
                    </span>
                    <span className="text-xs text-zinc-500">{info.hint}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      ) : (
        <section className="space-y-4" aria-label="Knowledge editor">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-medium text-white">{meta?.label}</h2>
              <p className="text-sm text-zinc-500">{meta?.hint}</p>
            </div>
            <Button variant="ghost" onClick={() => setSelected(null)} disabled={busy}>
              ← All categories
            </Button>
          </div>

          <ul className="space-y-2">
            {categoryItems.length === 0 ? (
              <li className="rounded-xl border border-dashed border-white/10 px-4 py-6 text-sm text-zinc-500">
                No facts yet in this category. Add the first one below.
              </li>
            ) : (
              categoryItems.map((item) => (
                <li
                  key={item.knowledge_id}
                  className="rounded-xl border border-white/10 bg-black/20 px-4 py-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-white">{item.title}</p>
                      <p className="mt-1 whitespace-pre-wrap text-sm text-zinc-400">
                        {item.content}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => startEdit(item)}
                        disabled={busy}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => void remove(item.knowledge_id)}
                        disabled={busy}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </li>
              ))
            )}
          </ul>

          <div className="space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <h3 className="text-sm font-medium text-white">
              {editId ? "Edit fact" : "Add fact"}
            </h3>
            <Field label="Title" required>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={meta?.titlePlaceholder}
                maxLength={200}
              />
            </Field>
            <Field label="Content" required>
              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder={meta?.contentPlaceholder}
                rows={4}
                maxLength={8000}
              />
            </Field>
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => void save()}
                disabled={busy || !title.trim() || !content.trim()}
              >
                {editId ? "Save changes" : "Add to knowledge"}
              </Button>
              {editId ? (
                <Button variant="ghost" onClick={resetForm} disabled={busy}>
                  Cancel edit
                </Button>
              ) : null}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
