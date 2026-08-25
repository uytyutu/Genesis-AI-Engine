"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type GiveawayStatus = {
  ok?: boolean;
  available?: boolean;
  code?: string;
  label?: string;
  product?: string;
  original_value_eur?: number;
  price_eur?: number;
  reason?: string | null;
};

type RedeemResult = {
  ok?: boolean;
  need_profile?: boolean;
  next?: string;
  message?: string;
  order_id?: string;
  detail?: string;
};

export default function GiveawayRedeemPage() {
  const params = useParams();
  const router = useRouter();
  const code = String(params?.code || "").trim();
  const [status, setStatus] = useState<GiveawayStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loggedIn, setLoggedIn] = useState(false);

  const load = useCallback(async () => {
    if (!code) return;
    setError(null);
    try {
      const res = await fetch(`${API}/api/giveaway/${encodeURIComponent(code)}`, {
        cache: "no-store",
      });
      const body = (await res.json().catch(() => ({}))) as GiveawayStatus;
      setStatus(body);
      if (!res.ok || body.ok === false) {
        setError(
          body.reason === "code_not_found"
            ? "Dieser Giveaway-Link ist ungültig."
            : "Giveaway nicht verfügbar.",
        );
      }
    } catch {
      setError("Netzwerkfehler — bitte später erneut versuchen.");
    }
  }, [code]);

  useEffect(() => {
    setLoggedIn(Boolean(getClientToken()));
    void load();
  }, [load]);

  async function redeem() {
    if (!code) return;
    if (!getClientToken()) {
      router.push(
        `/client/login?next=${encodeURIComponent(`/giveaway/${code}`)}`,
      );
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/giveaway/${encodeURIComponent(code)}/redeem`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...clientAuthHeaders(),
          },
        },
      );
      const body = (await res.json().catch(() => ({}))) as RedeemResult;
      if (res.status === 401) {
        router.push(
          `/client/login?next=${encodeURIComponent(`/giveaway/${code}`)}`,
        );
        return;
      }
      if (body.need_profile && body.next) {
        router.push(body.next);
        return;
      }
      if (!res.ok || body.ok === false) {
        const detail = String(body.detail || body.message || "");
        if (detail === "code_exhausted") {
          setError("Dieser Giveaway wurde bereits eingelöst.");
        } else if (detail === "already_redeemed") {
          setError("Sie haben Website Basic Giveaway bereits erhalten.");
          router.push("/client/products");
        } else {
          setError(detail || "Einlösen fehlgeschlagen.");
        }
        return;
      }
      router.push(body.next || `/client/products?order=${body.order_id || ""}`);
    } catch {
      setError("Einlösen fehlgeschlagen.");
    } finally {
      setBusy(false);
    }
  }

  const available = Boolean(status?.available);
  const original = Number(status?.original_value_eur || 299);

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-5 py-12">
        <p className="text-sm font-medium tracking-wide text-emerald-300/90">
          Virtus Core · Giveaway
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          Website Basic — geschenkt
        </h1>
        <p className="mt-3 text-base leading-relaxed text-zinc-400">
          Wert {original.toFixed(0)} € →{" "}
          <span className="font-semibold text-emerald-300">0 €</span>. Keine
          Stripe-Zahlung. Ein erfolgreiches Einlösen pro Link.
        </p>

        {status?.label ? (
          <p className="mt-2 text-sm text-zinc-500">{status.label}</p>
        ) : null}

        {error ? (
          <p className="mt-6 rounded-xl border border-rose-500/30 bg-rose-950/40 px-4 py-3 text-sm text-rose-100">
            {error}
          </p>
        ) : null}

        {!available && status?.ok ? (
          <p className="mt-6 rounded-xl border border-amber-500/30 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
            Dieser Giveaway-Link ist bereits vergeben.
          </p>
        ) : null}

        <ol className="mt-8 space-y-2 text-sm text-zinc-400">
          <li>1. Anmelden oder Konto erstellen</li>
          <li>2. Unternehmensprofil ausfüllen (einmal)</li>
          <li>3. Website Basic erhalten → Kabinett → Bearbeiten · Preview · ZIP</li>
        </ol>

        <div className="mt-8 flex flex-col gap-3">
          {available ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void redeem()}
              className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-emerald-500 px-5 text-sm font-semibold text-zinc-950 hover:bg-emerald-400 disabled:opacity-60"
            >
              {busy
                ? "Wird eingelöst…"
                : loggedIn
                  ? "Geschenk einlösen"
                  : "Anmelden und einlösen"}
            </button>
          ) : null}
          {!loggedIn && available ? (
            <Link
              href={`/client/register?next=${encodeURIComponent(`/giveaway/${code}`)}`}
              className="inline-flex min-h-[44px] items-center justify-center rounded-xl border border-white/15 px-5 text-sm text-zinc-200 hover:bg-white/5"
            >
              Neues Konto erstellen
            </Link>
          ) : null}
          <Link
            href="/client/products"
            className="text-center text-sm text-zinc-500 hover:text-zinc-300"
          >
            Zum Client Workspace
          </Link>
        </div>
      </div>
    </main>
  );
}
