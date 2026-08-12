"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ClientWorkspaceShell } from "../../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../../lib/clientAuth";
import { BRAND_NAME } from "../../../lib/publicBrand";
import { publicApiBase } from "../../../lib/publicApiBase";

const API = publicApiBase();

function SetupInner() {
  const search = useSearchParams();
  const orderId = search.get("order") || "";
  const paid = search.get("paid") === "1";
  const [status, setStatus] = useState<string>("loading");
  const [botName, setBotName] = useState("");
  const [botId, setBotId] = useState("");

  useEffect(() => {
    if (!getClientToken()) {
      setStatus("need_login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        if (orderId) {
          const st = await fetch(
            `${API}/api/sales/orders/${encodeURIComponent(orderId)}/status`,
            { cache: "no-store" },
          );
          if (st.ok) {
            const body = await st.json();
            if (!cancelled && body.status === "paid") {
              setStatus("paid");
            }
          }
        }
        const res = await fetch(`${API}/api/client/bots`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        });
        if (!res.ok) {
          if (!cancelled) setStatus(paid ? "paid" : "ready");
          return;
        }
        const body = await res.json();
        const bots = (body.bots || []) as { bot_id: string; display_name: string; status: string }[];
        if (cancelled) return;
        if (bots.length) {
          setBotName(bots[0].display_name);
          setBotId(bots[0].bot_id);
          setStatus(bots[0].status === "online" ? "online" : "learning");
        } else {
          setStatus(paid ? "paid" : "ready");
        }
      } catch {
        if (!cancelled) setStatus(paid ? "paid" : "ready");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [orderId, paid]);

  return (
    <ClientWorkspaceShell
      title="Подключение AI Digital Employee"
      subtitle={`${BRAND_NAME} · после оплаты подключите свои каналы`}
    >
      <div className="mx-auto max-w-lg space-y-6 py-6 text-center">
        {status === "need_login" ? (
          <p className="text-sm text-zinc-300">
            Войдите, чтобы продолжить.{" "}
            <Link
              href={`/client/login?next=${encodeURIComponent(`/client/bots/setup?order=${orderId}`)}`}
              className="text-emerald-300 underline"
            >
              Войти
            </Link>
          </p>
        ) : null}

        {status === "loading" ? (
          <p className="text-sm text-zinc-400">Проверяем оплату и Workspace…</p>
        ) : null}

        {status === "paid" || status === "learning" || status === "ready" ? (
          <div className="space-y-3 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-6 text-left">
            <p className="text-center text-lg font-medium text-white">Payment received</p>
            <ul className="space-y-2 text-sm text-zinc-300">
              <li>✓ Within 24 hours we will contact you if anything is missing for setup.</li>
              <li>✓ You will receive: Workspace access and channel connection steps.</li>
              <li>✓ Your AI employee goes live after you connect Telegram and/or Website Chat (WhatsApp / Instagram / Messenger — Coming Soon).</li>
            </ul>
            <p className="text-sm text-zinc-400">
              {botName
                ? `«${botName}» готовится. Подключите каналы — затем статус станет Online.`
                : "Подключите каналы, чтобы вывести AI Digital Employee Online."}
            </p>
            {orderId ? (
              <p className="text-center text-xs text-zinc-500">Заказ {orderId}</p>
            ) : null}
          </div>
        ) : null}

        {status === "online" ? (
          <div className="space-y-3 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-6">
            <p className="text-lg font-medium text-white">🟢 Online</p>
            <p className="text-sm text-zinc-300">
              {botName || "AI Digital Employee"} готов принимать сообщения.
            </p>
          </div>
        ) : null}

        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href={botId ? `/client/bots` : "/client/bots"}
            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black"
          >
            Открыть Bot Dashboard
          </Link>
          <Link
            href="/order/bot"
            className="rounded-xl border border-white/20 px-4 py-2.5 text-sm text-white"
          >
            Ещё один пакет
          </Link>
        </div>
      </div>
    </ClientWorkspaceShell>
  );
}

export default function ClientBotsSetupPage() {
  return (
    <Suspense fallback={<p className="p-8 text-center text-zinc-500">Загрузка…</p>}>
      <SetupInner />
    </Suspense>
  );
}
