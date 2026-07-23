"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../components/ClientWorkspaceShell";
import {
  PortalApiError,
  portalFetch,
  portalFetchAllow404,
} from "../lib/portalApi";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

type MyProduct = {
  product_id: string;
  product_type: string;
  display_name: string;
  status: string;
  source: string;
};

type ConversationRow = {
  conversation_id: string;
  status?: string;
  updated_at?: string;
};

function isWebsite(p: MyProduct) {
  return p.product_type === "website" || p.product_id === "prod_website";
}

function isChatbot(p: MyProduct) {
  return p.product_type === "chatbot" || p.product_id === "prod_chatbot";
}

export default function ClientDashboardPage() {
  const router = useRouter();
  const [products, setProducts] = useState<MyProduct[] | null>(null);
  const [openConversations, setOpenConversations] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const owned = await portalFetch<MyProduct[]>("/portal/my-products");
      setProducts(owned);
      if (owned.some(isChatbot)) {
        const list = await portalFetchAllow404<ConversationRow[]>(
          "/portal/chatbot/conversations",
        );
        const open = (list ?? []).filter(
          (c) => c.status === "open" || c.status === "prepared",
        ).length;
        setOpenConversations(open);
      } else {
        setOpenConversations(0);
      }
    } catch (err) {
      if (err instanceof PortalApiError && err.status === 401) {
        router.replace("/client/login");
        return;
      }
      if (err instanceof PortalApiError) setError(err.detail);
      else if (err instanceof Error) setError(err.message);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  const hasWebsite = (products ?? []).some(isWebsite);
  const hasVector = (products ?? []).some(isChatbot);
  const todayLabel = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "short",
  });

  const recommendation = !hasVector
    ? {
        text: `Add ${ASSISTANT_NAME} — answer customers 24/7`,
        href: "/projects/chatbot/setup",
        cta: `Activate ${ASSISTANT_NAME}`,
      }
    : openConversations > 0
      ? {
          text: "Review open conversations in Inbox",
          href: "/projects/chatbot/inbox",
          cta: "Open Inbox",
        }
      : !hasWebsite
        ? {
            text: "Order a Landing Website for your business",
            href: "/order",
            cta: "Order Landing",
          }
        : {
            text: "Ask Vector what to improve next",
            href: "/projects/chatbot",
            cta: `Open ${ASSISTANT_NAME}`,
          };

  return (
    <ClientWorkspaceShell
      title={`Welcome to ${BRAND_NAME}`}
      subtitle={`What is happening with your business today · ${todayLabel}`}
    >
      {error ? (
        <p className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <section className="rounded-2xl border border-emerald-400/20 bg-emerald-500/[0.06] p-5">
          <h2 className="text-lg font-semibold text-white">Today</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Live status of your {BRAND_NAME} workspace
          </p>
          <ul className="mt-4 space-y-2 text-sm text-zinc-200">
            <li className="flex items-start gap-2">
              <span className="text-emerald-300">✔</span>
              <span>
                Website{" "}
                <strong className="text-white">
                  {hasWebsite ? "Active" : "Not connected yet"}
                </strong>
                {!hasWebsite ? (
                  <>
                    {" "}
                    ·{" "}
                    <Link href="/order" className="text-emerald-300 hover:underline">
                      Order Landing
                    </Link>
                  </>
                ) : null}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className={hasVector ? "text-emerald-300" : "text-zinc-500"}>
                {hasVector ? "✔" : "·"}
              </span>
              <span>
                {ASSISTANT_NAME}{" "}
                <strong className="text-white">
                  {hasVector ? "Online" : "Not activated"}
                </strong>
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-300">✔</span>
              <span>
                {openConversations > 0 ? (
                  <>
                    <strong className="text-white">{openConversations}</strong> open
                    conversation{openConversations === 1 ? "" : "s"}
                  </>
                ) : (
                  <>No open conversations waiting</>
                )}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-300">✔</span>
              <span>
                Last backup —{" "}
                <strong className="text-white">today</strong>
                <span className="text-zinc-500">
                  {" "}
                  (platform snapshot · delivery files via Orders)
                </span>
              </span>
            </li>
            <li className="mt-3 rounded-xl border border-amber-400/20 bg-amber-500/10 px-3 py-3">
              <p className="text-xs uppercase tracking-wide text-amber-100/80">
                Next recommendation
              </p>
              <p className="mt-1 text-sm text-white">{recommendation.text}</p>
              <Link
                href={recommendation.href}
                className="mt-2 inline-flex text-sm font-medium text-amber-100 hover:underline"
              >
                {recommendation.cta} →
              </Link>
            </li>
          </ul>
        </section>

        <section className="rounded-2xl border border-sky-400/25 bg-sky-500/[0.07] p-5">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold text-white">{ASSISTANT_NAME}</h2>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs ${
                hasVector
                  ? "bg-emerald-500/20 text-emerald-100"
                  : "bg-white/10 text-zinc-400"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  hasVector ? "bg-emerald-400" : "bg-zinc-500"
                }`}
              />
              {hasVector ? "Online" : "Offline"}
            </span>
          </div>
          <p className="mt-4 text-sm text-zinc-200">
            {hasVector
              ? "Hello. How can I help you today?"
              : `${ASSISTANT_NAME} is your AI Business Employee. Activate to start.`}
          </p>
          <Link
            href={hasVector ? "/projects/chatbot" : "/projects/chatbot/setup"}
            className="mt-5 inline-flex rounded-xl bg-sky-400 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
          >
            {hasVector ? "Open chat" : `Activate ${ASSISTANT_NAME}`} →
          </Link>
        </section>
      </div>

      <section className="mt-6">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
            My Products
          </h2>
          <Link
            href="/client/products"
            className="text-sm text-emerald-300 hover:underline"
          >
            Manage all →
          </Link>
        </div>
        {products === null ? (
          <p className="mt-3 text-sm text-zinc-500">Loading…</p>
        ) : products.length === 0 ? (
          <p className="mt-3 rounded-xl border border-dashed border-white/15 px-4 py-6 text-sm text-zinc-400">
            No products activated yet. After your first purchase or activation,
            cards appear here.
          </p>
        ) : (
          <ul className="mt-3 grid gap-3 sm:grid-cols-2">
            {products.slice(0, 4).map((p) => {
              const openHref = isChatbot(p)
                ? "/projects/chatbot"
                : isWebsite(p)
                  ? "/client/orders"
                  : "/client/products";
              return (
                <li
                  key={p.product_id}
                  className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"
                >
                  <p className="font-semibold text-white">{p.display_name}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-emerald-300/90">
                    Active
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Link
                      href={openHref}
                      className="rounded-lg bg-emerald-500/20 px-3 py-1.5 text-xs font-medium text-emerald-100 hover:bg-emerald-500/30"
                    >
                      Open
                    </Link>
                    <Link
                      href="/client/products"
                      className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-zinc-300 hover:bg-white/5"
                    >
                      Manage
                    </Link>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </ClientWorkspaceShell>
  );
}
