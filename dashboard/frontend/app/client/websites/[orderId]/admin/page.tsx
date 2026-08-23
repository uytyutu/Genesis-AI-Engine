"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  WebsiteAdminComingSoon,
  WebsiteAdminShell,
  type WebsiteAdminSectionId,
} from "../../../../components/WebsiteAdminShell";
import { WebsiteAdminContent } from "../../../../components/WebsiteAdminContent";
import { WebsiteAdminDesign } from "../../../../components/WebsiteAdminDesign";
import { WebsiteAdminMedia } from "../../../../components/WebsiteAdminMedia";
import { WebsiteAdminCinematic } from "../../../../components/WebsiteAdminCinematic";
import { WebsiteTipsPanel } from "../../../../components/WebsiteTipsPanel";
import { VectorCoachingToasts } from "../../../../components/VectorCoachingToasts";
import { clientAuthHeaders, getClientToken } from "../../../../lib/clientAuth";
import { formatApiDetail } from "../../../../lib/formatApiError";
import { publicApiBase } from "../../../../lib/publicApiBase";

const API = publicApiBase();

type PreviewMeta = {
  business_name?: string;
  preview_url?: string | null;
  product_id?: string | null;
  has_product_dir?: boolean;
  commerce_mode?: string;
};

export default function WebsiteAdminPage() {
  const params = useParams();
  const orderId = String(params?.orderId || "");
  const router = useRouter();
  const searchParams = useSearchParams();
  const [section, setSection] = useState<WebsiteAdminSectionId>("dashboard");
  const [meta, setMeta] = useState<PreviewMeta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewKey, setPreviewKey] = useState(0);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [aiMsg, setAiMsg] = useState<string | null>(null);
  const [publishMsg, setPublishMsg] = useState<string | null>(null);

  useEffect(() => {
    const q = (searchParams.get("section") || "").trim() as WebsiteAdminSectionId | "";
    const allowed: WebsiteAdminSectionId[] = [
      "dashboard",
      "website",
      "cinematic",
      "design",
      "media",
      "files",
      "support",
      "ai",
      "store",
      "crm",
      "automation",
      "marketing",
      "analytics",
    ];
    if (q && allowed.includes(q)) setSection(q);
  }, [searchParams]);

  const refreshPreview = () => setPreviewKey((k) => k + 1);

  const loadMeta = useCallback(async () => {
    if (!getClientToken()) {
      router.replace(
        `/client/login?next=${encodeURIComponent(`/client/websites/${orderId}/admin`)}`,
      );
      return;
    }
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/preview-meta`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(formatApiDetail(body) || "load_failed");
      setMeta(body as PreviewMeta);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "load_failed");
    }
  }, [orderId, router]);

  useEffect(() => {
    void loadMeta();
  }, [loadMeta]);

  const runAiEdit = async () => {
    if (!aiPrompt.trim()) return;
    setAiBusy(true);
    setAiMsg(null);
    try {
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/ai-edit`,
        {
          method: "POST",
          headers: {
            ...clientAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ prompt: aiPrompt }),
        },
      );
      const body = await res.json();
      if (!res.ok) {
        const detail = formatApiDetail(body) || "ai_edit_failed";
        if (
          detail.includes("unsupported_ai_edit_intent") ||
          detail.includes("unsupported")
        ) {
          throw new Error(
            "This request is not supported yet. Try: shorter Hero, add a service, premium tone, prices section, or lighter/darker design.",
          );
        }
        throw new Error(detail);
      }
      setAiMsg(String(body.summary || "Updated"));
      setAiPrompt("");
      refreshPreview();
      if (section === "website") setSection("website");
    } catch (e) {
      setAiMsg(e instanceof Error ? e.message : "ai_edit_failed");
    } finally {
      setAiBusy(false);
    }
  };

  const publish = async () => {
    setPublishMsg(null);
    try {
      const check = await fetch(
        `${API}/api/client/websites/${orderId}/admin/publish-check`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const checkBody = await check.json();
      if (check.ok && checkBody.ok === false) {
        const blockers = (checkBody.blockers || [])
          .map((b: { message?: string }) => b.message)
          .filter(Boolean);
        throw new Error(
          blockers.length
            ? `Publish blocked: ${blockers.join(" · ")}`
            : "Publish blocked — fix quality issues first.",
        );
      }
      const res = await fetch(
        `${API}/api/client/websites/${orderId}/admin/publish`,
        { method: "POST", headers: { ...clientAuthHeaders() } },
      );
      const body = await res.json();
      if (!res.ok) {
        const detail = body?.detail;
        if (detail && typeof detail === "object" && detail.blockers) {
          const blockers = (detail.blockers as { message?: string }[])
            .map((b) => b.message)
            .filter(Boolean);
          throw new Error(
            blockers.length
              ? `Publish blocked: ${blockers.join(" · ")}`
              : formatApiDetail(body) || "publish_failed",
          );
        }
        throw new Error(formatApiDetail(body) || "publish_failed");
      }
      setPublishMsg(
        body.preview_url
          ? `Published overlay · preview ready`
          : body.applied
            ? "Overlay applied"
            : "No product folder yet — content saved for when Factory finishes",
      );
      refreshPreview();
      void loadMeta();
    } catch (e) {
      setPublishMsg(e instanceof Error ? e.message : "publish_failed");
    }
  };

  const siteName = String(meta?.business_name || "Your Website");
  const previewSrc = meta?.preview_url
    ? `${meta.preview_url}${meta.preview_url.includes("?") ? "&" : "?"}v=${previewKey}`
    : null;

  return (
    <WebsiteAdminShell
      orderId={orderId}
      siteName={siteName}
      section={section}
      onSection={setSection}
      commerceMode={meta?.commerce_mode || "standalone"}
      vectorDock={<VectorCoachingToasts />}
    >
      {error ? (
        <p className="mb-4 rounded-xl border border-rose-400/30 bg-rose-950/30 px-4 py-3 text-sm text-rose-100">
          {error}
        </p>
      ) : null}

      {section === "dashboard" ? (
        <div className="space-y-6">
          <div className="rounded-2xl border border-emerald-500/25 bg-emerald-950/20 px-5 py-5">
            <h2 className="text-lg font-semibold text-white">Website Control</h2>
            <p className="mt-1 text-sm text-zinc-300">
              Telefon, E-Mail, Adresse, Logo und Inhalte selbst ändern — Änderungen
              erscheinen in der Live-Vorschau.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setSection("website")}
                className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
              >
                Einstellungen (Telefon / E-Mail)
              </button>
              <button
                type="button"
                onClick={() => setSection("design")}
                className="rounded-xl border border-white/20 px-4 py-2 text-sm font-semibold text-white"
              >
                Design / Logo
              </button>
              <button
                type="button"
                onClick={() => setSection("media")}
                className="rounded-xl border border-white/20 px-4 py-2 text-sm font-semibold text-white"
              >
                Medien
              </button>
              <button
                type="button"
                onClick={() => setSection("cinematic")}
                className="rounded-xl border border-violet-400/40 px-4 py-2 text-sm font-semibold text-violet-100"
              >
                Cinematic
              </button>
              <button
                type="button"
                onClick={() => void publish()}
                className="rounded-xl border border-white/20 px-4 py-2 text-sm font-semibold text-white"
              >
                Vorschau / Publish
              </button>
            </div>
            {publishMsg ? (
              <p className="mt-3 text-xs text-emerald-200">{publishMsg}</p>
            ) : null}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-black/25 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Status
              </p>
              <ul className="mt-3 space-y-2 text-sm text-zinc-300">
                <li>Product: {meta?.product_id || "pending Factory"}</li>
                <li>
                  Preview folder:{" "}
                  {meta?.has_product_dir ? "ready" : "waiting for generation"}
                </li>
              </ul>
            </div>
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/40">
              <p className="border-b border-white/10 px-3 py-2 text-xs text-zinc-400">
                Live preview
              </p>
              {previewSrc ? (
                <iframe
                  title="Website preview"
                  className="h-[320px] w-full bg-white"
                  src={previewSrc}
                />
              ) : (
                <div className="flex h-[200px] items-center justify-center px-4 text-center text-sm text-zinc-500">
                  Preview appears after Factory creates your site. Content edits
                  are already saved.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {section === "website" ? (
        <WebsiteAdminContent orderId={orderId} onSaved={refreshPreview} />
      ) : null}

      {section === "cinematic" ? (
        <WebsiteAdminCinematic
          orderId={orderId}
          previewUrl={meta?.preview_url}
          onSaved={refreshPreview}
        />
      ) : null}

      {section === "design" ? (
        <WebsiteAdminDesign
          orderId={orderId}
          siteName={siteName}
          onSaved={refreshPreview}
        />
      ) : null}

      {section === "media" ? (
        <WebsiteAdminMedia orderId={orderId} onSaved={refreshPreview} />
      ) : null}

      {section === "files" ? (
        <div className="rounded-2xl border border-white/10 bg-black/25 p-5">
          <h2 className="text-lg font-semibold text-white">Files & downloads</h2>
          <p className="mt-2 text-sm text-zinc-400">
            ZIP remains a delivery format — edit the live site here first.
          </p>
          <Link
            href="/client/downloads"
            className="mt-4 inline-flex rounded-xl border border-emerald-400/40 px-4 py-2 text-sm font-semibold text-emerald-200"
          >
            Open downloads →
          </Link>
        </div>
      ) : null}

      {section === "support" ? (
        <div className="space-y-4">
          <WebsiteTipsPanel orderId={orderId} dark />
        </div>
      ) : null}

      {section === "ai" ? (
        <div className="space-y-4 rounded-2xl border border-white/10 bg-black/25 p-5">
          <h2 className="text-lg font-semibold text-white">AI Assistant</h2>
          <p className="text-sm text-zinc-400">
            Ask for a real change on <strong>this</strong> website only — e.g.
            «Сделай Hero короче», «Добавь услугу Laser Hair Removal», «Замени тон
            на премиальный», «Добавь раздел Цены».
          </p>
          <textarea
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-3 text-sm text-white"
            rows={3}
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            placeholder="Describe the change…"
          />
          <button
            type="button"
            disabled={aiBusy || !aiPrompt.trim()}
            onClick={() => void runAiEdit()}
            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black disabled:opacity-50"
          >
            {aiBusy ? "Applying…" : "Apply with AI"}
          </button>
          {aiMsg ? <p className="text-sm text-emerald-200">{aiMsg}</p> : null}
          <p className="text-xs text-zinc-500">
            Or use Vector in the right dock — same live capabilities.
          </p>
        </div>
      ) : null}

      {section === "store" ||
      section === "crm" ||
      section === "automation" ||
      section === "marketing" ||
      section === "analytics" ? (
        <WebsiteAdminComingSoon label={section} />
      ) : null}
    </WebsiteAdminShell>
  );
}
