"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { BRAND_NAME } from "../../lib/publicBrand";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type BotRecord = {
  bot_id: string;
  display_name: string;
  status: string;
  channels?: string[];
  bot_config?: Record<string, unknown>;
  package_id?: string;
};

type Connection = {
  connection_id: string;
  channel: string;
  bot_id?: string;
  status?: string;
  telegram?: { username?: string };
};

type WebsiteChatConnection = {
  connection_id: string;
  bot_id?: string;
  status?: string;
  public_key?: string;
  site_label?: string;
  commercial_live?: boolean;
};

type Entitlements = {
  package_id?: string;
  max_bots?: number | null;
  bots_used?: number;
};

function statusLamp(status: string): string {
  const s = (status || "").toLowerCase();
  if (s === "online" || s === "connected") return "🟢 Online";
  if (s === "pending_connect" || s === "learning") return "🟡 Learning";
  return "🔴 Offline";
}

function ClientBotsDashboard() {
  const search = useSearchParams();
  const [bots, setBots] = useState<BotRecord[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [websiteChats, setWebsiteChats] = useState<WebsiteChatConnection[]>([]);
  const [ents, setEnts] = useState<Entitlements | null>(null);
  const [metaConfigured, setMetaConfigured] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editInstructions, setEditInstructions] = useState("");
  const [tgToken, setTgToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);

  const selected = useMemo(
    () => bots.find((b) => b.bot_id === selectedId) || bots[0] || null,
    [bots, selectedId],
  );

  const load = useCallback(async () => {
    if (!getClientToken()) {
      setError("Войдите в Workspace, чтобы управлять ботами.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/bots`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || `HTTP ${res.status}`);
      }
      setBots((body.bots || []) as BotRecord[]);
      setConnections((body.connections || []) as Connection[]);
      setEnts((body.entitlements || null) as Entitlements | null);
      setMetaConfigured(Boolean(body.meta_oauth_configured));
      if (!selectedId && body.bots?.[0]?.bot_id) {
        setSelectedId(String(body.bots[0].bot_id));
      }
      const wch = await fetch(`${API}/api/client/bots/website-chat/connections`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      if (wch.ok) {
        const wbody = await wch.json().catch(() => ({}));
        setWebsiteChats((wbody.connections || []) as WebsiteChatConnection[]);
      } else {
        setWebsiteChats([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const meta = search.get("meta");
    if (meta === "ok") setBanner("Meta канал подключён.");
    if (meta === "error") {
      setBanner(`Meta OAuth: ${search.get("reason") || "ошибка"}`);
    }
  }, [search]);

  useEffect(() => {
    if (!selected) return;
    setEditName(selected.display_name || "");
    const cfg = selected.bot_config || {};
    setEditInstructions(String(cfg.ai_instructions || ""));
  }, [selected]);

  const botConnections = useMemo(() => {
    if (!selected) return [];
    return connections.filter((c) => c.bot_id === selected.bot_id);
  }, [connections, selected]);

  const botWebsiteChats = useMemo(() => {
    if (!selected) return [];
    return websiteChats.filter((c) => c.bot_id === selected.bot_id);
  }, [websiteChats, selected]);

  async function saveBot() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/bots/${selected.bot_id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...clientAuthHeaders(),
        },
        body: JSON.stringify({
          display_name: editName.trim(),
          bot_config: { ai_instructions: editInstructions.trim() },
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Не удалось сохранить");
      }
      await load();
      setBanner("Инструкции сохранены.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }

  async function connectTelegram() {
    if (!selected || !tgToken.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/bots/telegram/connect`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...clientAuthHeaders(),
        },
        body: JSON.stringify({ bot_id: selected.bot_id, token: tgToken.trim() }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Telegram connect failed");
      }
      setTgToken("");
      setBanner("Telegram подключён. Бот Online.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка Telegram");
    } finally {
      setBusy(false);
    }
  }

  async function startMeta(channel: string) {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/bots/meta/oauth/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...clientAuthHeaders(),
        },
        body: JSON.stringify({ bot_id: selected.bot_id, channel }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          formatApiDetail(body.detail) ||
            (body.detail === "meta_not_configured"
              ? "Connect Meta — platform keys pending"
              : "Meta OAuth failed"),
        );
      }
      const url = String(body.authorize_url || "");
      if (!url) throw new Error("Нет authorize_url");
      window.location.href = url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Meta error");
      setBusy(false);
    }
  }

  async function connectWebsiteChat() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/bots/${encodeURIComponent(selected.bot_id)}/website-chat/connect`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...clientAuthHeaders(),
          },
          body: JSON.stringify({
            site_ref: "workspace-connect",
            site_label: `${selected.display_name || "AI Employee"} website`,
          }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Website Chat connect failed");
      }
      const key = String(body.connection?.public_key || "");
      setBanner(
        key
          ? "Website Chat connected. Open preview to chat with your AI Employee."
          : "Website Chat connection created.",
      );
      await load();
      if (key) {
        window.open(
          `/spike/website-chat?key=${encodeURIComponent(key)}&label=${encodeURIComponent(
            selected.display_name || "Website",
          )}`,
          "_blank",
          "noopener,noreferrer",
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Website Chat error");
    } finally {
      setBusy(false);
    }
  }

  async function disconnectWebsiteChat(connectionId: string) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/bots/website-chat/${encodeURIComponent(connectionId)}/disconnect`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders() },
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Disconnect failed");
      }
      setBanner("Website Chat disconnected — widget should stop answering.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Disconnect error");
    } finally {
      setBusy(false);
    }
  }

  async function reconnectWebsiteChat(connectionId: string) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/bots/website-chat/${encodeURIComponent(connectionId)}/reconnect`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders() },
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Reconnect failed");
      }
      const key = String(body.connection?.public_key || "");
      setBanner("Website Chat reconnected.");
      await load();
      if (key) {
        window.open(
          `/spike/website-chat?key=${encodeURIComponent(key)}&label=${encodeURIComponent(
            selected?.display_name || "Website",
          )}`,
          "_blank",
          "noopener,noreferrer",
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reconnect error");
    } finally {
      setBusy(false);
    }
  }

  async function addBot() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/bots`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...clientAuthHeaders(),
        },
        body: JSON.stringify({
          display_name: `AI Bot ${(ents?.bots_used || 0) + 1}`,
          channels: ["telegram"],
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          formatApiDetail(body.detail) ||
            (body.detail === "max_bots_reached"
              ? "Лимит пакета исчерпан"
              : "Не удалось создать бота"),
        );
      }
      await load();
      if (body.bot?.bot_id) setSelectedId(String(body.bot.bot_id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }

  const canAdd =
    ents?.max_bots == null ||
    Number(ents.bots_used || 0) < Number(ents.max_bots || 0);

  return (
    <ClientWorkspaceShell
      title="AI Business Bot"
      subtitle="Цифровые сотрудники · Online/Offline · подключение своих каналов"
    >
      <div className="mx-auto max-w-4xl space-y-6 py-2">
        <p className="text-sm text-zinc-400">
          <Link href="/client/inbox" className="font-medium text-emerald-300 hover:underline">
            Posteingang / Inbox →
          </Link>
        </p>
        {ents ? (
          <p className="text-xs text-zinc-500">
            Пакет {ents.package_id || "—"} · ботов {ents.bots_used ?? 0}
            {ents.max_bots != null ? ` / ${ents.max_bots}` : " · Fair Use"}
            {" · "}
            {BRAND_NAME} Workspace
          </p>
        ) : (
          <p className="text-xs text-zinc-500">{BRAND_NAME} Workspace</p>
        )}

        {banner ? (
          <p className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
            {banner}
          </p>
        ) : null}
        {error ? (
          <p className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {error}
            {!getClientToken() ? (
              <>
                {" "}
                <Link href="/client/login" className="underline">
                  Войти
                </Link>
              </>
            ) : null}
          </p>
        ) : null}

        {loading ? (
          <p className="text-sm text-zinc-500">Загрузка…</p>
        ) : bots.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 space-y-3">
            <p className="text-sm text-zinc-300">
              Пока нет AI-ботов. Оформите пакет или создайте бота, если пакет уже оплачен.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/order/bot"
                className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
              >
                Заказать AI Business Bot
              </Link>
              <button
                type="button"
                disabled={busy || !canAdd}
                onClick={() => void addBot()}
                className="rounded-xl border border-white/20 px-4 py-2 text-sm text-white disabled:opacity-40"
              >
                Создать бота
              </button>
            </div>
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
            <aside className="space-y-2">
              {bots.map((bot) => (
                <button
                  key={bot.bot_id}
                  type="button"
                  onClick={() => setSelectedId(bot.bot_id)}
                  className={`w-full rounded-xl border px-3 py-3 text-left text-sm ${
                    selected?.bot_id === bot.bot_id
                      ? "border-emerald-400/40 bg-emerald-500/10"
                      : "border-white/10 bg-white/[0.03]"
                  }`}
                >
                  <p className="font-medium text-white">{bot.display_name}</p>
                  <p className="mt-1 text-xs text-zinc-400">{statusLamp(bot.status)}</p>
                </button>
              ))}
              <button
                type="button"
                disabled={busy || !canAdd}
                onClick={() => void addBot()}
                className="w-full rounded-xl border border-dashed border-white/20 px-3 py-2 text-xs text-zinc-400 disabled:opacity-40"
              >
                {canAdd ? "+ Добавить AI-бота" : "Лимит пакета"}
              </button>
            </aside>

            {selected ? (
              <section className="space-y-5">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="text-lg font-semibold text-white">
                      {selected.display_name}
                    </h2>
                    <span className="text-sm text-zinc-300">
                      {statusLamp(selected.status)}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500">id: {selected.bot_id}</p>
                  <div className="flex flex-wrap gap-2 text-xs">
                    {(selected.channels || []).map((ch) => {
                      const online = botConnections.some(
                        (c) => c.channel === ch && c.status === "online",
                      );
                      return (
                        <span
                          key={ch}
                          className={`rounded-full px-2.5 py-1 ${
                            online
                              ? "bg-emerald-500/20 text-emerald-100"
                              : "bg-white/5 text-zinc-400"
                          }`}
                        >
                          {online ? "●" : "○"} {ch}
                        </span>
                      );
                    })}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-3">
                  <h3 className="font-medium text-white">Инструкции AI</h3>
                  <input
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="Имя цифрового сотрудника"
                  />
                  <textarea
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                    rows={4}
                    value={editInstructions}
                    onChange={(e) => setEditInstructions(e.target.value)}
                    placeholder="Чем занимается бот, тон, запреты…"
                  />
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void saveBot()}
                    className="rounded-xl bg-white/10 px-4 py-2 text-sm text-white"
                  >
                    Сохранить
                  </button>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-4">
                  <h3 className="font-medium text-white">Каналы</h3>

                  <div className="space-y-2">
                    <p className="text-sm text-zinc-300">Telegram — свой бот из @BotFather</p>
                    <input
                      className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 font-mono text-sm text-white"
                      placeholder="123456:ABC…"
                      value={tgToken}
                      onChange={(e) => setTgToken(e.target.value)}
                      autoComplete="off"
                    />
                    <button
                      type="button"
                      disabled={busy || !tgToken.trim()}
                      onClick={() => void connectTelegram()}
                      className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-40"
                    >
                      Подключить Telegram
                    </button>
                  </div>

                  <div className="space-y-2 border-t border-white/10 pt-4">
                    <p className="text-sm text-zinc-300">Meta (WhatsApp / Instagram / Messenger)</p>
                    {metaConfigured ? (
                      <div className="flex flex-wrap gap-2">
                        {["whatsapp", "instagram", "facebook_messenger"].map((ch) => (
                          <button
                            key={ch}
                            type="button"
                            disabled={busy}
                            onClick={() => void startMeta(ch)}
                            className="rounded-xl border border-white/20 px-3 py-1.5 text-xs text-white"
                          >
                            Connect {ch}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-amber-200/90">
                        Telegram + Website Chat are Live. WhatsApp / Instagram /
                        Messenger — Coming Soon.
                      </p>
                    )}
                  </div>

                  <div className="border-t border-white/10 pt-4 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-sm text-zinc-300">Website Chat</p>
                        <p className="mt-1 text-xs text-emerald-200/90">
                          Live — connect to your website, open preview, chat with
                          the same AI Employee as Telegram.
                        </p>
                      </div>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void connectWebsiteChat()}
                        className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-40"
                      >
                        Connect to my website
                      </button>
                    </div>
                    {botWebsiteChats.length ? (
                      <ul className="space-y-2 text-xs text-zinc-400">
                        {botWebsiteChats.map((c) => (
                          <li
                            key={c.connection_id}
                            className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 space-y-2"
                          >
                            <p>
                              {c.status === "connected" ? "🟢" : "○"}{" "}
                              {c.site_label || "Website"} · {c.status || "—"}
                            </p>
                            {c.public_key ? (
                              <p className="font-mono break-all text-[11px] text-zinc-500">
                                {c.public_key}
                              </p>
                            ) : null}
                            <div className="flex flex-wrap gap-2">
                              {c.public_key && c.status === "connected" ? (
                                <Link
                                  href={`/spike/website-chat?key=${encodeURIComponent(
                                    c.public_key,
                                  )}&label=${encodeURIComponent(
                                    c.site_label || selected.display_name || "Website",
                                  )}`}
                                  target="_blank"
                                  className="rounded-lg border border-white/20 px-2.5 py-1 text-white hover:bg-white/5"
                                >
                                  Open site preview
                                </Link>
                              ) : null}
                              {c.status === "connected" ? (
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() => void disconnectWebsiteChat(c.connection_id)}
                                  className="rounded-lg border border-rose-400/40 px-2.5 py-1 text-rose-100 disabled:opacity-40"
                                >
                                  Disconnect
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() => void reconnectWebsiteChat(c.connection_id)}
                                  className="rounded-lg border border-emerald-400/40 px-2.5 py-1 text-emerald-100 disabled:opacity-40"
                                >
                                  Reconnect
                                </button>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-zinc-500">
                        No Website Chat connection yet — Connect to my website to embed the Live widget.
                      </p>
                    )}
                  </div>

                  {botConnections.length ? (
                    <ul className="space-y-1 text-xs text-zinc-400">
                      {botConnections.map((c) => (
                        <li key={c.connection_id}>
                          {c.channel}: {c.status || "—"}
                          {c.telegram?.username ? ` @${c.telegram.username}` : ""}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                  <h3 className="font-medium text-white">Статистика</h3>
                  <p className="mt-2 text-xs text-zinc-500">
                    Лог сообщений и базовая аналитика — после стабильного connect (stub).
                  </p>
                </div>
              </section>
            ) : null}
          </div>
        )}

        <p className="text-center text-sm text-zinc-500">
          <Link href="/order/bot" className="text-emerald-300 hover:underline">
            Новый заказ AI Business Bot
          </Link>
        </p>
      </div>
    </ClientWorkspaceShell>
  );
}

export default function ClientBotsPage() {
  return (
    <Suspense fallback={<p className="p-8 text-center text-zinc-500">Загрузка…</p>}>
      <ClientBotsDashboard />
    </Suspense>
  );
}
