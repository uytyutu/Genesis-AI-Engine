"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useI18n } from "@/components/I18nProvider";

export default function SettingsPage() {
  const router = useRouter();
  const { locale, setLocale, locales, t } = useI18n();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [suggested, setSuggested] = useState("");
  const [bio, setBio] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [sharePath, setSharePath] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [copied, setCopied] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [credMsg, setCredMsg] = useState("");
  const [credErr, setCredErr] = useState("");

  async function load() {
    const r = await fetch("/api/profile", { credentials: "include" });
    if (!r.ok) {
      router.replace("/auth/login?next=/settings");
      return;
    }
    const d = await r.json();
    const p = d.profile;
    setEmail(p.email);
    setNewEmail(p.email);
    setUsername(p.username || "");
    setSuggested(p.suggestedUsername || "");
    setBio(p.bio || "");
    setDisplayName(p.displayName || "");
    setSharePath(p.sharePath);
  }

  useEffect(() => {
    load();
  }, [router]);

  async function save() {
    setErr("");
    setMsg("");
    const r = await fetch("/api/profile", {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: username || suggested || undefined,
        bio,
        displayName,
      }),
    });
    const d = await r.json();
    if (!r.ok) {
      setErr(d.error || t("error.generic"));
      return;
    }
    setSharePath(d.profile.sharePath);
    setUsername(d.profile.username || "");
    setMsg(t("settings.saved"));
  }

  async function saveCredentials() {
    setCredErr("");
    setCredMsg("");
    if (!currentPassword) {
      setCredErr(t("settings.credErrCurrentPassword"));
      return;
    }
    const payload: Record<string, string> = { currentPassword };
    if (newEmail && newEmail.toLowerCase() !== email.toLowerCase()) {
      payload.newEmail = newEmail;
    }
    if (newPassword) payload.newPassword = newPassword;
    if (!payload.newEmail && !payload.newPassword) {
      setCredErr(t("settings.credErrChangeFirst"));
      return;
    }
    const r = await fetch("/api/account/credentials", {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const d = await r.json();
    if (!r.ok) {
      setCredErr(d.error || t("error.generic"));
      return;
    }
    setEmail(d.email || newEmail);
    setCurrentPassword("");
    setNewPassword("");
    setCredMsg(
      [
        d.emailChanged ? t("settings.credEmailUpdated") : "",
        d.passwordChanged ? t("settings.credPasswordUpdated") : "",
      ]
        .filter(Boolean)
        .join(" ") || t("settings.credSaved")
    );
  }

  function copyLink() {
    if (!sharePath) return;
    navigator.clipboard.writeText(`${window.location.origin}${sharePath}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <main className="anim-in mx-auto max-w-lg space-y-4">
      <section className="anon-card p-6">
        <h1 className="text-2xl font-semibold">⚙️ {t("settings.title")}</h1>
        <p className="mt-2 text-sm anon-muted">{email}</p>
        <p className="mt-1 text-xs anon-muted">{t("settings.credHint")}</p>

        <label className="mt-6 block text-sm">
          {t("settings.displayName")}
          <input
            className="anon-input mt-2"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </label>

        <label className="mt-4 block text-sm">
          {t("settings.username")}
          <div className="mt-2 flex gap-2">
            <span className="flex items-center text-violet-300">@</span>
            <input
              className="anon-input"
              value={username || suggested}
              onChange={(e) => setUsername(e.target.value.toLowerCase())}
              placeholder={suggested || "yourname"}
            />
          </div>
          <p className="mt-1 text-xs anon-muted">{t("settings.usernameHint")}</p>
        </label>

        <label className="mt-4 block text-sm">
          {t("settings.bio")}
          <textarea
            className="anon-input mt-2 min-h-20"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            maxLength={160}
          />
        </label>

        <label className="mt-4 block text-sm">
          🌐 {t("settings.language")}
          <select
            className="anon-input mt-2"
            value={locale}
            onChange={(e) => setLocale(e.target.value as typeof locale)}
          >
            {locales.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
                {l.code === locale ? " ✓" : ""}
              </option>
            ))}
          </select>
        </label>

        {err && <p className="mt-3 text-sm text-rose-300">{err}</p>}
        {msg && <p className="mt-3 text-sm text-emerald-300">{msg}</p>}

        <button type="button" className="anon-btn anon-btn-primary mt-5 w-full" onClick={save}>
          {t("settings.save")}
        </button>
      </section>

      <section className="anon-card space-y-3 p-6">
        <h2 className="text-lg font-semibold">{t("settings.credTitle")}</h2>
        <p className="text-xs anon-muted">{t("settings.credSub")}</p>
        <label className="block text-sm">
          {t("settings.credCurrentPassword")}
          <input
            className="anon-input mt-2"
            type="password"
            autoComplete="current-password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          {t("settings.credNewEmail")}
          <input
            className="anon-input mt-2"
            type="email"
            autoComplete="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          {t("settings.credNewPassword")}
          <input
            className="anon-input mt-2"
            type="password"
            autoComplete="new-password"
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </label>
        {credErr && <p className="text-sm text-rose-300">{credErr}</p>}
        {credMsg && <p className="text-sm text-emerald-300">{credMsg}</p>}
        <button type="button" className="anon-btn anon-btn-primary w-full" onClick={saveCredentials}>
          {t("settings.credUpdate")}
        </button>
      </section>

      {sharePath && (
        <section className="overflow-hidden rounded-3xl border border-violet-300/25 bg-gradient-to-br from-[#3d2a68] via-[#2a1848] to-[#1a1230] p-5">
          <h2 className="font-semibold">{t("secrets.yourLink")}</h2>
          <p className="mt-2 font-mono text-sm text-violet-200">
            {typeof window !== "undefined" ? window.location.origin : ""}
            {sharePath}
          </p>
          <button type="button" className="anon-btn anon-btn-primary mt-4 w-full" onClick={copyLink}>
            {copied ? t("room.copied") : t("secrets.copyLink")}
          </button>
        </section>
      )}

      <p className="text-center text-xs anon-muted">{t("footer.privacy")}</p>
    </main>
  );
}
