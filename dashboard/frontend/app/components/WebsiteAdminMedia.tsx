"use client";

import { useCallback, useEffect, useState } from "react";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type MediaRow = {
  id: string;
  role?: string;
  url?: string;
  path?: string;
};

type ContentSnap = {
  hero?: { image?: MediaRow | null };
  gallery?: { id: string; caption?: string; image?: MediaRow | null }[];
  team?: { id: string; name: string; role: string; image?: MediaRow | null }[];
};

type Props = {
  orderId: string;
  onSaved?: () => void;
};

function withToken(url: string | null | undefined) {
  if (!url) return "";
  const token = getClientToken();
  const abs = url.startsWith("http") ? url : `${API}${url}`;
  if (!token) return abs;
  return `${abs}${abs.includes("?") ? "&" : "?"}access_token=${encodeURIComponent(token)}`;
}

export function WebsiteAdminMedia({ orderId, onSaved }: Props) {
  const [content, setContent] = useState<ContentSnap | null>(null);
  const [library, setLibrary] = useState<MediaRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!getClientToken() || !orderId) return;
    try {
      const [cRes, mRes] = await Promise.all([
        fetch(`${API}/api/client/websites/${orderId}/admin/content`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        }),
        fetch(`${API}/api/client/websites/${orderId}/admin/media`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        }),
      ]);
      const cBody = await cRes.json();
      const mBody = await mRes.json();
      if (!cRes.ok) throw new Error(formatApiDetail(cBody) || "load_failed");
      setContent(cBody.content as ContentSnap);
      if (mRes.ok) setLibrary((mBody.media as MediaRow[]) || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "load_failed");
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const upload = async (file: File, role: string) => {
    const fd = new FormData();
    fd.append("file", file);
    const up = await fetch(
      `${API}/api/client/websites/${orderId}/admin/media?role=${encodeURIComponent(role)}`,
      { method: "POST", headers: { ...clientAuthHeaders() }, body: fd },
    );
    const upBody = await up.json();
    if (!up.ok) throw new Error(formatApiDetail(upBody) || "upload_failed");
    return upBody.media as MediaRow;
  };

  const patchContent = async (payload: Record<string, unknown>) => {
    const patch = await fetch(
      `${API}/api/client/websites/${orderId}/admin/content`,
      {
        method: "PATCH",
        headers: {
          ...clientAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );
    const patchBody = await patch.json();
    if (!patch.ok) throw new Error(formatApiDetail(patchBody) || "save_failed");
    setContent(patchBody.content as ContentSnap);
    onSaved?.();
  };

  const replaceHero = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const media = await upload(file, "hero");
      await patchContent({
        hero: { image: { id: media.id, path: media.path, url: media.url } },
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "upload_failed");
    } finally {
      setBusy(false);
    }
  };

  const clearHero = async () => {
    setBusy(true);
    setError(null);
    try {
      await patchContent({ hero: { image: null } });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "clear_failed");
    } finally {
      setBusy(false);
    }
  };

  const addGalleryPhoto = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const media = await upload(file, "gallery");
      const gallery = [
        ...(content?.gallery || []),
        {
          id: `gal-${Date.now()}`,
          caption: "",
          image: { id: media.id, path: media.path, url: media.url },
        },
      ];
      await patchContent({ gallery });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "upload_failed");
    } finally {
      setBusy(false);
    }
  };

  const setTeamPhoto = async (index: number, file: File) => {
    setBusy(true);
    setError(null);
    try {
      const media = await upload(file, "team");
      const team = [...(content?.team || [])];
      if (!team[index]) {
        team[index] = {
          id: `team-${Date.now()}`,
          name: "Team",
          role: "",
          image: null,
        };
      }
      team[index] = {
        ...team[index],
        image: { id: media.id, path: media.path, url: media.url },
      };
      await patchContent({ team });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "upload_failed");
    } finally {
      setBusy(false);
    }
  };

  const deleteMedia = async (imageId: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/media/${imageId}`,
        { method: "DELETE", headers: { ...clientAuthHeaders() } },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "delete_failed");
      await load();
      onSaved?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "delete_failed");
    } finally {
      setBusy(false);
    }
  };

  const heroUrl = withToken(content?.hero?.image?.url);

  return (
    <div className="space-y-8">
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}

      <section className="space-y-3">
        <h3 className="text-sm font-semibold text-white">Hero</h3>
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-zinc-900">
          {heroUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={heroUrl} alt="" className="aspect-[16/9] w-full object-cover" />
          ) : (
            <div className="flex aspect-[16/9] items-center justify-center text-sm text-zinc-500">
              No Hero image yet
            </div>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <label className="inline-flex cursor-pointer items-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black">
            {busy ? "Working…" : "Upload Hero"}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              disabled={busy}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void replaceHero(f);
              }}
            />
          </label>
          {content?.hero?.image?.id ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void clearHero()}
              className="rounded-xl border border-white/20 px-4 py-2.5 text-sm text-zinc-200"
            >
              Remove Hero photo
            </button>
          ) : null}
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-white">Gallery</h3>
          <label className="inline-flex cursor-pointer rounded-lg border border-emerald-400/40 px-3 py-1.5 text-xs font-semibold text-emerald-200">
            + Upload photo
            <input
              type="file"
              accept="image/*"
              className="hidden"
              disabled={busy}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void addGalleryPhoto(f);
              }}
            />
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {(content?.gallery || []).map((item) => {
            const src = withToken(item.image?.url);
            return (
              <div
                key={item.id}
                className="overflow-hidden rounded-xl border border-white/10 bg-black/30"
              >
                {src ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={src} alt="" className="aspect-square w-full object-cover" />
                ) : (
                  <div className="flex aspect-square items-center justify-center text-xs text-zinc-500">
                    Empty
                  </div>
                )}
                {item.image?.id ? (
                  <button
                    type="button"
                    className="w-full border-t border-white/10 py-1.5 text-[11px] text-rose-200"
                    disabled={busy}
                    onClick={() => void deleteMedia(item.image!.id!)}
                  >
                    Delete
                  </button>
                ) : null}
              </div>
            );
          })}
        </div>
      </section>

      <section className="space-y-3">
        <h3 className="text-sm font-semibold text-white">Team photos</h3>
        <div className="space-y-3">
          {(content?.team || []).length === 0 ? (
            <p className="text-xs text-zinc-500">
              Add team members under Website → Team, then upload photos here.
            </p>
          ) : null}
          {(content?.team || []).map((member, idx) => {
            const src = withToken(member.image?.url);
            return (
              <div
                key={member.id}
                className="flex flex-wrap items-center gap-3 rounded-xl border border-white/10 bg-black/20 p-3"
              >
                <div className="h-16 w-16 overflow-hidden rounded-lg bg-zinc-800">
                  {src ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={src} alt="" className="h-full w-full object-cover" />
                  ) : null}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-white">{member.name}</p>
                  <p className="text-xs text-zinc-500">{member.role}</p>
                </div>
                <label className="cursor-pointer rounded-lg border border-white/15 px-3 py-1.5 text-xs text-zinc-200">
                  Replace
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    disabled={busy}
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) void setTeamPhoto(idx, f);
                    }}
                  />
                </label>
              </div>
            );
          })}
        </div>
      </section>

      <section className="space-y-3">
        <h3 className="text-sm font-semibold text-white">Uploaded files</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {library.map((row) => (
            <div
              key={row.id}
              className="overflow-hidden rounded-xl border border-white/10 bg-black/30"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={withToken(row.url)}
                alt=""
                className="aspect-square w-full object-cover"
              />
              <div className="flex items-center justify-between gap-1 border-t border-white/10 px-2 py-1.5">
                <span className="truncate text-[10px] text-zinc-500">{row.role}</span>
                <button
                  type="button"
                  className="text-[10px] text-rose-200"
                  disabled={busy}
                  onClick={() => void deleteMedia(row.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
