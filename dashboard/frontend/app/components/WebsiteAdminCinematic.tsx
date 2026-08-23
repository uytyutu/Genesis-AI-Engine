"use client";

import { useCallback, useEffect, useState } from "react";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type Scene = {
  scene: number;
  filename: string;
  rel: string;
};

type Props = {
  orderId: string;
  previewUrl?: string | null;
  onSaved?: () => void;
};

export function WebsiteAdminCinematic({ orderId, previewUrl, onSaved }: Props) {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!getClientToken()) return;
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/cinematic`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "load_failed");
      setScenes(Array.isArray(body.scenes) ? body.scenes : []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "load_failed");
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const replace = async (scene: number, file: File) => {
    setBusy(scene);
    setStatus("Saving…");
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/cinematic/${scene}/replace`,
        { method: "POST", headers: { ...clientAuthHeaders() }, body: fd },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "save_failed");
      setStatus("Saved");
      await load();
      onSaved?.();
    } catch (e) {
      setStatus(null);
      setError(e instanceof Error ? e.message : "Could not save");
    } finally {
      setBusy(null);
    }
  };

  const restore = async (scene: number) => {
    setBusy(scene);
    setStatus("Saving…");
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/cinematic/${scene}/restore`,
        { method: "POST", headers: { ...clientAuthHeaders() } },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "restore_failed");
      setStatus("Saved");
      await load();
      onSaved?.();
    } catch (e) {
      setStatus(null);
      setError(e instanceof Error ? e.message : "Could not save");
    } finally {
      setBusy(null);
    }
  };

  const restoreOriginal = async () => {
    if (!window.confirm("Restore original Premium version? Current edits will be replaced.")) {
      return;
    }
    setStatus("Saving…");
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/versions/restore-original`,
        { method: "POST", headers: { ...clientAuthHeaders() } },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "restore_failed");
      setStatus("Saved");
      await load();
      onSaved?.();
    } catch (e) {
      setStatus(null);
      setError(e instanceof Error ? e.message : "Could not save");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Cinematic Experience</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Scene frames drive the Premium scroll cinema. Replace updates the live
            website assets — not a separate gallery.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void restoreOriginal()}
          className="min-h-11 rounded-xl border border-white/20 px-4 py-2 text-sm text-zinc-200 hover:bg-white/5"
        >
          Restore original
        </button>
      </div>
      {status ? (
        <p className="text-sm text-emerald-300" role="status">
          {status}
        </p>
      ) : null}
      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}{" "}
          <button type="button" className="underline" onClick={() => void load()}>
            Retry
          </button>
        </p>
      ) : null}
      {previewUrl ? (
        <p className="text-xs text-zinc-500">
          Live preview:{" "}
          <a className="text-emerald-300 hover:underline" href={previewUrl} target="_blank" rel="noreferrer">
            Open website
          </a>
        </p>
      ) : null}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {scenes.map((s) => (
          <article
            key={s.scene}
            className="rounded-2xl border border-white/10 bg-white/[0.03] p-3"
          >
            <p className="text-xs uppercase tracking-wide text-zinc-500">
              Scene {String(s.scene).padStart(2, "0")}
            </p>
            <p className="mt-1 truncate text-sm text-zinc-300">{s.filename}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <label className="inline-flex min-h-11 cursor-pointer items-center rounded-xl bg-emerald-500 px-3 text-sm font-semibold text-black">
                {busy === s.scene ? "…" : "Replace"}
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  disabled={busy === s.scene}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void replace(s.scene, f);
                    e.target.value = "";
                  }}
                />
              </label>
              <button
                type="button"
                disabled={busy === s.scene}
                onClick={() => void restore(s.scene)}
                className="min-h-11 rounded-xl border border-white/15 px-3 text-sm text-zinc-200 hover:bg-white/5"
              >
                Restore
              </button>
            </div>
          </article>
        ))}
      </div>
      {scenes.length === 0 && !error ? (
        <p className="text-sm text-zinc-400">No cinematic scenes on this product yet.</p>
      ) : null}
    </div>
  );
}
