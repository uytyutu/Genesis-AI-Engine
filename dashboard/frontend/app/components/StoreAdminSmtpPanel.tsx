"use client";

import { useEffect, useMemo, useState } from "react";
import { clientAuthHeaders } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

const PRESETS: Record<
  string,
  { host: string; port: number; encryption: string; hint: string }
> = {
  gmail: {
    host: "smtp.gmail.com",
    port: 587,
    encryption: "tls",
    hint: "Use a Google App Password (not your normal Gmail password).",
  },
  outlook: {
    host: "smtp-mail.outlook.com",
    port: 587,
    encryption: "tls",
    hint: "Outlook.com personal account.",
  },
  microsoft365: {
    host: "smtp.office365.com",
    port: 587,
    encryption: "tls",
    hint: "Microsoft 365 business mailbox.",
  },
  smtp: {
    host: "",
    port: 587,
    encryption: "tls",
    hint: "Any SMTP host (Mailbox.org, IONOS, Strato, …).",
  },
};

type Transport = {
  provider_id?: string | null;
  host?: string | null;
  port?: number;
  username?: string | null;
  encryption?: string;
  from_email?: string | null;
  from_name?: string | null;
  reply_to?: string | null;
  support_email?: string | null;
  sales_email?: string | null;
  password_set?: boolean;
  last_test?: {
    ok?: boolean;
    to?: string;
    sent_at?: string;
    status?: string;
    title?: string;
    reason?: string;
  } | null;
};

type Props = {
  orderId: string;
  providerId: string;
  dark?: boolean;
  initial?: Transport | null;
  onDone?: () => void;
  onCancel?: () => void;
};

function fmtTime(iso?: string | null) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export function StoreAdminSmtpPanel({
  orderId,
  providerId,
  dark = true,
  initial,
  onDone,
  onCancel,
}: Props) {
  const preset = PRESETS[providerId] || PRESETS.smtp;
  const [host, setHost] = useState(initial?.host || preset.host);
  const [port, setPort] = useState(String(initial?.port || preset.port));
  const [username, setUsername] = useState(initial?.username || "");
  const [password, setPassword] = useState("");
  const [encryption, setEncryption] = useState(initial?.encryption || preset.encryption);
  const [fromEmail, setFromEmail] = useState(initial?.from_email || "");
  const [fromName, setFromName] = useState(initial?.from_name || "");
  const [replyTo, setReplyTo] = useState(initial?.reply_to || "");
  const [supportEmail, setSupportEmail] = useState(initial?.support_email || "");
  const [salesEmail, setSalesEmail] = useState(initial?.sales_email || "");
  const [busy, setBusy] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Transport["last_test"] | null>(
    initial?.last_test || null,
  );
  const [vectorHint, setVectorHint] = useState<string | null>(null);

  useEffect(() => {
    if (!initial?.host && preset.host) setHost(preset.host);
  }, [providerId, initial?.host, preset.host]);

  const inputCls = dark
    ? "w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm text-white outline-none"
    : "w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none";

  const label = useMemo(() => {
    const map: Record<string, string> = {
      gmail: "Gmail",
      outlook: "Outlook",
      microsoft365: "Microsoft 365",
      smtp: "SMTP",
    };
    return map[providerId] || "SMTP";
  }, [providerId]);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/integrations/${providerId}/smtp-connect`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({
            host,
            port: Number(port) || 587,
            username,
            password: password || undefined,
            encryption,
            from_email: fromEmail || username,
            from_name: fromName || undefined,
            reply_to: replyTo || undefined,
            support_email: supportEmail || undefined,
            sales_email: salesEmail || undefined,
          }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || "smtp_connect_failed");
      setVectorHint(body.vector_hint?.message || "✅ Email успешно подключён.");
      onDone?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function sendTest() {
    setTesting(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/stores/${orderId}/admin/email/test`, {
        method: "POST",
        headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ to: supportEmail || fromEmail || username || undefined }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok && !body.test) {
        throw new Error(formatApiDetail(body.detail) || "test_failed");
      }
      setTestResult(body.test || null);
      if (!body.ok) {
        setError(
          [body.test?.title || body.message, body.test?.reason].filter(Boolean).join(" — "),
        );
      }
      onDone?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setTesting(false);
    }
  }

  return (
    <div
      className={`space-y-3 rounded-2xl border p-4 ${
        dark ? "border-sky-500/25 bg-sky-950/20" : "border-sky-200 bg-sky-50"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="text-sm font-semibold">Connect {label}</h4>
          <p className={`mt-0.5 text-[11px] ${dark ? "text-zinc-500" : "text-slate-500"}`}>
            {preset.hint}
          </p>
        </div>
        {onCancel ? (
          <button type="button" className="text-xs opacity-70" onClick={onCancel}>
            Cancel
          </button>
        ) : null}
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <label className="text-xs">
          SMTP Host
          <input className={inputCls} value={host} onChange={(e) => setHost(e.target.value)} />
        </label>
        <label className="text-xs">
          Port
          <input className={inputCls} value={port} onChange={(e) => setPort(e.target.value)} />
        </label>
        <label className="text-xs">
          Username
          <input
            className={inputCls}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
        </label>
        <label className="text-xs">
          Password / App Password
          <input
            type="password"
            className={inputCls}
            value={password}
            placeholder={initial?.password_set ? "•••••••• (unchanged)" : ""}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
          />
        </label>
        <label className="text-xs">
          Encryption
          <select
            className={inputCls}
            value={encryption}
            onChange={(e) => setEncryption(e.target.value)}
          >
            <option value="tls">TLS (STARTTLS)</option>
            <option value="ssl">SSL</option>
            <option value="none">None</option>
          </select>
        </label>
        <label className="text-xs">
          From Email
          <input
            className={inputCls}
            value={fromEmail}
            onChange={(e) => setFromEmail(e.target.value)}
            placeholder={username || "info@company.de"}
          />
        </label>
        <label className="text-xs">
          From Name
          <input
            className={inputCls}
            value={fromName}
            onChange={(e) => setFromName(e.target.value)}
            placeholder="Nordlicht Möbel GmbH"
          />
        </label>
        <label className="text-xs">
          Reply-To
          <input className={inputCls} value={replyTo} onChange={(e) => setReplyTo(e.target.value)} />
        </label>
        <label className="text-xs">
          Support Email
          <input
            className={inputCls}
            value={supportEmail}
            onChange={(e) => setSupportEmail(e.target.value)}
          />
        </label>
        <label className="text-xs">
          Sales Email
          <input
            className={inputCls}
            value={salesEmail}
            onChange={(e) => setSalesEmail(e.target.value)}
          />
        </label>
      </div>

      {vectorHint ? (
        <p className={`text-sm ${dark ? "text-emerald-300" : "text-emerald-800"}`}>{vectorHint}</p>
      ) : null}

      {testResult ? (
        <div
          className={`rounded-xl border px-3 py-2 text-xs ${
            testResult.ok
              ? dark
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
                : "border-emerald-200 bg-emerald-50 text-emerald-900"
              : dark
                ? "border-rose-500/30 bg-rose-500/10 text-rose-100"
                : "border-rose-200 bg-rose-50 text-rose-900"
          }`}
        >
          {testResult.ok ? (
            <>
              <p className="font-semibold">✓ Test Email sent</p>
              <p>To: {testResult.to || "—"}</p>
              <p>Time: {fmtTime(testResult.sent_at)}</p>
              <p>Status: {testResult.status || "Delivered"}</p>
            </>
          ) : (
            <>
              <p className="font-semibold">{testResult.title || "SMTP send failed"}</p>
              <p>Reason: {testResult.reason || "—"}</p>
            </>
          )}
        </div>
      ) : null}

      {error ? (
        <p className="text-xs text-rose-400" role="alert">
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => void save()}
          className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50 ${
            dark ? "bg-emerald-500/90 text-black" : "bg-emerald-700 text-white"
          }`}
        >
          {busy ? "Saving…" : "Save & Connect"}
        </button>
        <button
          type="button"
          disabled={testing}
          onClick={() => void sendTest()}
          className={`rounded-xl px-3 py-2 text-xs font-semibold ${
            dark ? "border border-white/15" : "border border-slate-200"
          }`}
        >
          {testing ? "Sending…" : "Send Test Email"}
        </button>
      </div>
    </div>
  );
}
