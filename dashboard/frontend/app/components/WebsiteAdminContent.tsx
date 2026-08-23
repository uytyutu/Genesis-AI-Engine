"use client";

import { useCallback, useEffect, useState } from "react";
import { clientAuthHeaders, getClientToken } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type WebsiteContent = {
  hero: {
    headline: string;
    subheadline: string;
    cta_label: string;
    image?: { id?: string; url?: string | null } | null;
  };
  about: { title: string; body: string };
  services: { id: string; title: string; description: string; price: string }[];
  prices: {
    enabled: boolean;
    title: string;
    intro: string;
    items: { id: string; label: string; price: string; note: string }[];
  };
  contacts: {
    phone: string;
    email: string;
    address: string;
    whatsapp: string;
    city: string;
  };
  hours: Record<string, string>;
  social: Record<string, string>;
  faq: { id: string; question: string; answer: string }[];
  seo: { title: string; description: string };
  gallery: {
    id: string;
    caption?: string;
    image?: { id?: string; url?: string } | null;
  }[];
  team: {
    id: string;
    name: string;
    role: string;
    image?: { id?: string; url?: string } | null;
  }[];
  reviews: { id: string; author: string; text: string; rating: number }[];
  can_undo?: boolean;
  can_redo?: boolean;
};

type TabId =
  | "hero"
  | "about"
  | "services"
  | "prices"
  | "gallery"
  | "team"
  | "reviews"
  | "contacts"
  | "hours"
  | "social"
  | "faq"
  | "seo";

type Props = {
  orderId: string;
  onSaved?: () => void;
};

const HOUR_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;
const SOCIAL_KEYS = [
  "instagram",
  "facebook",
  "tiktok",
  "linkedin",
  "youtube",
  "google_business",
] as const;

const TABS: { id: TabId; label: string }[] = [
  { id: "contacts", label: "Kontakte" },
  { id: "hours", label: "Öffnungszeiten" },
  { id: "social", label: "Social" },
  { id: "hero", label: "Hero" },
  { id: "about", label: "Über uns" },
  { id: "services", label: "Leistungen" },
  { id: "prices", label: "Preise" },
  { id: "gallery", label: "Galerie" },
  { id: "team", label: "Team" },
  { id: "reviews", label: "Bewertungen" },
  { id: "faq", label: "FAQ" },
  { id: "seo", label: "SEO" },
];

export function WebsiteAdminContent({ orderId, onSaved }: Props) {
  const [content, setContent] = useState<WebsiteContent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<TabId>("contacts");

  const load = useCallback(async () => {
    if (!getClientToken() || !orderId) return;
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/content`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "load_failed");
      const c = body.content as WebsiteContent;
      setContent({
        ...c,
        about: c.about || { title: "Über uns", body: "" },
        prices: c.prices || {
          enabled: false,
          title: "Preise",
          intro: "",
          items: [],
        },
        gallery: c.gallery || [],
        team: c.team || [],
        reviews: c.reviews || [],
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "load_failed");
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    if (!content) return;
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/content`,
        {
          method: "PATCH",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify(content),
        },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "save_failed");
      setContent(body.content as WebsiteContent);
      onSaved?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "save_failed");
    } finally {
      setSaving(false);
    }
  };

  const historyAction = async (kind: "undo" | "redo") => {
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/content/${kind}`,
        { method: "POST", headers: { ...clientAuthHeaders() } },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || `${kind}_failed`);
      setContent(body.content as WebsiteContent);
      onSaved?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : `${kind}_failed`);
    }
  };

  if (!content) {
    return (
      <p className="text-sm text-zinc-400">{error || "Loading website content…"}</p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={!content.can_undo}
          onClick={() => void historyAction("undo")}
          className="rounded-lg border border-white/15 px-3 py-1.5 text-xs font-semibold text-zinc-200 disabled:opacity-40"
        >
          Undo
        </button>
        <button
          type="button"
          disabled={!content.can_redo}
          onClick={() => void historyAction("redo")}
          className="rounded-lg border border-white/15 px-3 py-1.5 text-xs font-semibold text-zinc-200 disabled:opacity-40"
        >
          Redo
        </button>
      </div>

      <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold ${
              tab === t.id
                ? "bg-emerald-500/20 text-emerald-100"
                : "border border-white/10 text-zinc-400 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error ? <p className="text-sm text-rose-300">{error}</p> : null}

      {tab === "hero" ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-xs text-zinc-400 sm:col-span-2">
            Headline
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              value={content.hero.headline || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  hero: { ...content.hero, headline: e.target.value },
                })
              }
            />
          </label>
          <label className="block text-xs text-zinc-400 sm:col-span-2">
            Subheadline
            <textarea
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              rows={2}
              value={content.hero.subheadline || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  hero: { ...content.hero, subheadline: e.target.value },
                })
              }
            />
          </label>
          <label className="block text-xs text-zinc-400">
            CTA label
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              value={content.hero.cta_label || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  hero: { ...content.hero, cta_label: e.target.value },
                })
              }
            />
          </label>
        </div>
      ) : null}

      {tab === "about" ? (
        <div className="space-y-3">
          <label className="block text-xs text-zinc-400">
            Title
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              value={content.about?.title || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  about: { ...content.about, title: e.target.value },
                })
              }
            />
          </label>
          <label className="block text-xs text-zinc-400">
            Body
            <textarea
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              rows={5}
              value={content.about?.body || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  about: { ...content.about, body: e.target.value },
                })
              }
            />
          </label>
        </div>
      ) : null}

      {tab === "services" ? (
        <div className="space-y-3">
          {content.services.map((svc, idx) => (
            <div
              key={svc.id || idx}
              className="rounded-xl border border-white/10 bg-black/20 p-3"
            >
              <input
                className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={svc.title}
                placeholder="Service title"
                onChange={(e) => {
                  const services = [...content.services];
                  services[idx] = { ...svc, title: e.target.value };
                  setContent({ ...content, services });
                }}
              />
              <textarea
                className="mt-2 w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                rows={2}
                value={svc.description}
                placeholder="Description"
                onChange={(e) => {
                  const services = [...content.services];
                  services[idx] = { ...svc, description: e.target.value };
                  setContent({ ...content, services });
                }}
              />
              <input
                className="mt-2 w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={svc.price}
                placeholder="Price (optional)"
                onChange={(e) => {
                  const services = [...content.services];
                  services[idx] = { ...svc, price: e.target.value };
                  setContent({ ...content, services });
                }}
              />
            </div>
          ))}
          <button
            type="button"
            className="rounded-lg border border-emerald-400/40 px-3 py-2 text-xs font-semibold text-emerald-200"
            onClick={() =>
              setContent({
                ...content,
                services: [
                  ...content.services,
                  {
                    id: `svc-${Date.now()}`,
                    title: "Neue Leistung",
                    description: "",
                    price: "",
                  },
                ],
              })
            }
          >
            + Add service
          </button>
        </div>
      ) : null}

      {tab === "prices" ? (
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm text-zinc-300">
            <input
              type="checkbox"
              checked={!!content.prices?.enabled}
              onChange={(e) =>
                setContent({
                  ...content,
                  prices: { ...content.prices, enabled: e.target.checked },
                })
              }
            />
            Show Prices section
          </label>
          <label className="block text-xs text-zinc-400">
            Title
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              value={content.prices?.title || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  prices: { ...content.prices, title: e.target.value },
                })
              }
            />
          </label>
          <label className="block text-xs text-zinc-400">
            Intro
            <textarea
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              rows={2}
              value={content.prices?.intro || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  prices: { ...content.prices, intro: e.target.value },
                })
              }
            />
          </label>
          {(content.prices?.items || []).map((item, idx) => (
            <div
              key={item.id || idx}
              className="grid gap-2 rounded-xl border border-white/10 bg-black/20 p-3 sm:grid-cols-2"
            >
              <input
                className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={item.label}
                placeholder="Label"
                onChange={(e) => {
                  const items = [...(content.prices.items || [])];
                  items[idx] = { ...item, label: e.target.value };
                  setContent({
                    ...content,
                    prices: { ...content.prices, items },
                  });
                }}
              />
              <input
                className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={item.price}
                placeholder="Price"
                onChange={(e) => {
                  const items = [...(content.prices.items || [])];
                  items[idx] = { ...item, price: e.target.value };
                  setContent({
                    ...content,
                    prices: { ...content.prices, items },
                  });
                }}
              />
            </div>
          ))}
          <button
            type="button"
            className="rounded-lg border border-emerald-400/40 px-3 py-2 text-xs font-semibold text-emerald-200"
            onClick={() =>
              setContent({
                ...content,
                prices: {
                  ...content.prices,
                  enabled: true,
                  items: [
                    ...(content.prices.items || []),
                    {
                      id: `price-${Date.now()}`,
                      label: "Leistung",
                      price: "",
                      note: "",
                    },
                  ],
                },
              })
            }
          >
            + Add price row
          </button>
        </div>
      ) : null}

      {tab === "gallery" ? (
        <div className="space-y-3">
          <p className="text-xs text-zinc-500">
            Captions here — upload / replace photos in Media.
          </p>
          {(content.gallery || []).map((item, idx) => (
            <div
              key={item.id || idx}
              className="rounded-xl border border-white/10 bg-black/20 p-3"
            >
              <input
                className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={item.caption || ""}
                placeholder="Caption"
                onChange={(e) => {
                  const gallery = [...(content.gallery || [])];
                  gallery[idx] = { ...item, caption: e.target.value };
                  setContent({ ...content, gallery });
                }}
              />
            </div>
          ))}
          <button
            type="button"
            className="rounded-lg border border-emerald-400/40 px-3 py-2 text-xs font-semibold text-emerald-200"
            onClick={() =>
              setContent({
                ...content,
                gallery: [
                  ...(content.gallery || []),
                  { id: `gal-${Date.now()}`, caption: "", image: null },
                ],
              })
            }
          >
            + Add gallery slot
          </button>
        </div>
      ) : null}

      {tab === "team" ? (
        <div className="space-y-3">
          {(content.team || []).map((member, idx) => (
            <div
              key={member.id || idx}
              className="grid gap-2 rounded-xl border border-white/10 bg-black/20 p-3 sm:grid-cols-2"
            >
              <input
                className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={member.name}
                placeholder="Name"
                onChange={(e) => {
                  const team = [...(content.team || [])];
                  team[idx] = { ...member, name: e.target.value };
                  setContent({ ...content, team });
                }}
              />
              <input
                className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={member.role}
                placeholder="Role"
                onChange={(e) => {
                  const team = [...(content.team || [])];
                  team[idx] = { ...member, role: e.target.value };
                  setContent({ ...content, team });
                }}
              />
            </div>
          ))}
          <button
            type="button"
            className="rounded-lg border border-emerald-400/40 px-3 py-2 text-xs font-semibold text-emerald-200"
            onClick={() =>
              setContent({
                ...content,
                team: [
                  ...(content.team || []),
                  {
                    id: `team-${Date.now()}`,
                    name: "Team member",
                    role: "",
                    image: null,
                  },
                ],
              })
            }
          >
            + Add team member
          </button>
        </div>
      ) : null}

      {tab === "reviews" ? (
        <div className="space-y-3">
          {(content.reviews || []).map((rev, idx) => (
            <div
              key={rev.id || idx}
              className="rounded-xl border border-white/10 bg-black/20 p-3"
            >
              <input
                className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={rev.author}
                placeholder="Author"
                onChange={(e) => {
                  const reviews = [...(content.reviews || [])];
                  reviews[idx] = { ...rev, author: e.target.value };
                  setContent({ ...content, reviews });
                }}
              />
              <textarea
                className="mt-2 w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                rows={2}
                value={rev.text}
                placeholder="Review text"
                onChange={(e) => {
                  const reviews = [...(content.reviews || [])];
                  reviews[idx] = { ...rev, text: e.target.value };
                  setContent({ ...content, reviews });
                }}
              />
            </div>
          ))}
          <button
            type="button"
            className="rounded-lg border border-emerald-400/40 px-3 py-2 text-xs font-semibold text-emerald-200"
            onClick={() =>
              setContent({
                ...content,
                reviews: [
                  ...(content.reviews || []),
                  {
                    id: `rev-${Date.now()}`,
                    author: "Kunde",
                    text: "",
                    rating: 5,
                  },
                ],
              })
            }
          >
            + Add review
          </button>
        </div>
      ) : null}

      {tab === "contacts" ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {(
            [
              ["phone", "Phone"],
              ["whatsapp", "WhatsApp"],
              ["email", "Email"],
              ["city", "City"],
              ["address", "Address"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="block text-xs text-zinc-400">
              {label}
              <input
                className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={content.contacts[key] || ""}
                onChange={(e) =>
                  setContent({
                    ...content,
                    contacts: { ...content.contacts, [key]: e.target.value },
                  })
                }
              />
            </label>
          ))}
        </div>
      ) : null}

      {tab === "hours" ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {HOUR_KEYS.map((key) => (
            <label key={key} className="block text-xs uppercase text-zinc-400">
              {key}
              <input
                className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm normal-case text-white"
                value={content.hours[key] || ""}
                onChange={(e) =>
                  setContent({
                    ...content,
                    hours: { ...content.hours, [key]: e.target.value },
                  })
                }
              />
            </label>
          ))}
        </div>
      ) : null}

      {tab === "social" ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {SOCIAL_KEYS.map((key) => (
            <label key={key} className="block text-xs capitalize text-zinc-400">
              {key.replace("_", " ")}
              <input
                className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={content.social[key] || ""}
                onChange={(e) =>
                  setContent({
                    ...content,
                    social: { ...content.social, [key]: e.target.value },
                  })
                }
              />
            </label>
          ))}
        </div>
      ) : null}

      {tab === "faq" ? (
        <div className="space-y-3">
          {(content.faq || []).map((item, idx) => (
            <div
              key={item.id || idx}
              className="rounded-xl border border-white/10 bg-black/20 p-3"
            >
              <input
                className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={item.question}
                onChange={(e) => {
                  const faq = [...(content.faq || [])];
                  faq[idx] = { ...item, question: e.target.value };
                  setContent({ ...content, faq });
                }}
              />
              <textarea
                className="mt-2 w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                rows={2}
                value={item.answer}
                onChange={(e) => {
                  const faq = [...(content.faq || [])];
                  faq[idx] = { ...item, answer: e.target.value };
                  setContent({ ...content, faq });
                }}
              />
            </div>
          ))}
        </div>
      ) : null}

      {tab === "seo" ? (
        <div className="space-y-3">
          <label className="block text-xs text-zinc-400">
            Title
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              value={content.seo?.title || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  seo: { ...content.seo, title: e.target.value },
                })
              }
            />
          </label>
          <label className="block text-xs text-zinc-400">
            Description
            <textarea
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
              rows={3}
              value={content.seo?.description || ""}
              onChange={(e) =>
                setContent({
                  ...content,
                  seo: { ...content.seo, description: e.target.value },
                })
              }
            />
          </label>
        </div>
      ) : null}

      <button
        type="button"
        disabled={saving}
        onClick={() => void save()}
        className="w-full rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110 disabled:opacity-50 sm:w-auto"
      >
        {saving ? "Saving…" : "Save & update preview"}
      </button>
    </div>
  );
}
