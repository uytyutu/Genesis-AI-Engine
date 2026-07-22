"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Badge, Button, Field, Input, Textarea } from "./ui";
import {
  PortalApiError,
  portalFetch,
  portalFetchAllow404,
} from "../lib/portalApi";

const DEMO_EMAIL = "client@virtus.local";
const DEMO_PASSWORD = "demo-vector";

const CHANNELS = [
  "website",
  "telegram",
  "instagram",
  "facebook",
  "whatsapp",
  "email",
] as const;

const PROVIDER_LABEL: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  ollama: "Ollama",
  kimi: "Kimi",
  custom: "Custom",
};

type WizardStep =
  | "gate"
  | "welcome"
  | "profile"
  | "bootstrap"
  | "knowledge"
  | "channels"
  | "provider"
  | "finish";

type TemplateRow = {
  industry: string;
  label: string;
  description?: string;
};

type ProfileRow = {
  business_name: string;
  industry: string;
  language: string;
  timezone: string;
};

type ProviderRow = {
  provider_id: string;
  provider_type: string;
  display_name: string;
  status: string;
  is_active?: boolean;
};

type ChannelRow = {
  connection_id: string;
  channel: string;
  display_name: string;
  status: string;
};

const STEPS: { id: WizardStep; label: string }[] = [
  { id: "welcome", label: "Welcome" },
  { id: "profile", label: "Business" },
  { id: "bootstrap", label: "Template" },
  { id: "knowledge", label: "Knowledge" },
  { id: "channels", label: "Channels" },
  { id: "provider", label: "AI" },
  { id: "finish", label: "Ready" },
];

function stepIndex(step: WizardStep): number {
  if (step === "gate") return -1;
  return STEPS.findIndex((s) => s.id === step);
}

export function ChatbotFirstRunWizard() {
  const [step, setStep] = useState<WizardStep>("gate");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [owned, setOwned] = useState(false);

  const [templates, setTemplates] = useState<TemplateRow[]>([]);
  const [businessName, setBusinessName] = useState("");
  const [industry, setIndustry] = useState("dental");
  const [language, setLanguage] = useState("ru");
  const [timezone, setTimezone] = useState("Europe/Berlin");
  const [profile, setProfile] = useState<ProfileRow | null>(null);
  const [bootstrapNote, setBootstrapNote] = useState<string | null>(null);

  const [services, setServices] = useState("");
  const [hours, setHours] = useState("");
  const [contacts, setContacts] = useState("");
  const [faq, setFaq] = useState("");
  const [knowledgeCount, setKnowledgeCount] = useState(0);

  const [channels, setChannels] = useState<ChannelRow[]>([]);
  const [providers, setProviders] = useState<ProviderRow[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(
    null,
  );

  const activeStep = stepIndex(step);

  const run = useCallback(async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (err) {
      if (err instanceof PortalApiError) {
        setError(err.detail);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("unexpected_error");
      }
    } finally {
      setBusy(false);
    }
  }, []);

  const refreshOwnership = useCallback(async () => {
    const products = await portalFetch<
      Array<{ product_type?: string; catalog_product_id?: string; product_id?: string }>
    >("/portal/my-products");
    const has = products.some(
      (p) =>
        p.product_type === "chatbot" ||
        p.catalog_product_id === "prod_chatbot" ||
        p.product_id === "prod_chatbot",
    );
    setOwned(has);
    return has;
  }, []);

  const bootstrapGate = useCallback(async () => {
    await run(async () => {
      // Probe session via profile or my-products
      try {
        const has = await refreshOwnership();
        const existing = await portalFetchAllow404<ProfileRow>(
          "/portal/chatbot/profile",
        );
        if (existing) {
          setProfile(existing);
          setBusinessName(existing.business_name || "");
          setIndustry(existing.industry || "dental");
          setLanguage(existing.language || "ru");
          setTimezone(existing.timezone || "Europe/Berlin");
        }
        const t = await portalFetch<TemplateRow[]>("/portal/chatbot/templates");
        setTemplates(t);
        if (!has) {
          setStep("gate");
          return;
        }
        setStep(existing ? "knowledge" : "welcome");
      } catch (err) {
        if (err instanceof PortalApiError && err.status === 401) {
          setStep("gate");
          return;
        }
        throw err;
      }
    });
  }, [refreshOwnership, run]);

  useEffect(() => {
    void bootstrapGate();
  }, [bootstrapGate]);

  const login = () =>
    run(async () => {
      const res = await portalFetch<{ authenticated: boolean }>("/portal/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      if (!res.authenticated) {
        throw new PortalApiError(401, "login_failed");
      }
      const has = await refreshOwnership();
      const t = await portalFetch<TemplateRow[]>("/portal/chatbot/templates");
      setTemplates(t);
      if (!has) return;
      setStep("welcome");
    });

  const activateDemo = () =>
    run(async () => {
      await portalFetch("/portal/products/prod_chatbot/activate", {
        method: "POST",
        body: JSON.stringify({ activation_code: "DEMO-CHATBOT" }),
      });
      await refreshOwnership();
      setStep("welcome");
    });

  const purchaseStub = () =>
    run(async () => {
      await portalFetch("/portal/products/prod_chatbot/purchase", {
        method: "POST",
      });
      await refreshOwnership();
      setStep("welcome");
    });

  const applyBootstrap = () =>
    run(async () => {
      if (!businessName.trim()) {
        throw new PortalApiError(400, "business_name_required");
      }
      const view = await portalFetch<
        ProfileRow & { initial_configuration?: { greeting?: string } }
      >("/portal/chatbot/profile/bootstrap", {
        method: "POST",
        body: JSON.stringify({
          industry,
          business_name: businessName.trim(),
          language,
          timezone,
        }),
      });
      setProfile(view);
      setBootstrapNote(
        view.initial_configuration?.greeting ||
          "Industry template applied.",
      );
      setStep("knowledge");
    });

  const saveKnowledge = () =>
    run(async () => {
      const entries: Array<{ category: string; title: string; content: string }> =
        [];
      if (services.trim()) {
        entries.push({
          category: "services",
          title: "Services",
          content: services.trim(),
        });
      }
      if (hours.trim()) {
        entries.push({
          category: "working_hours",
          title: "Working hours",
          content: hours.trim(),
        });
      }
      if (contacts.trim()) {
        entries.push({
          category: "contacts",
          title: "Contacts",
          content: contacts.trim(),
        });
      }
      if (faq.trim()) {
        entries.push({
          category: "faq",
          title: "FAQ",
          content: faq.trim(),
        });
      }
      for (const entry of entries) {
        await portalFetch("/portal/chatbot/knowledge", {
          method: "POST",
          body: JSON.stringify(entry),
        });
      }
      const rows = await portalFetch<unknown[]>("/portal/chatbot/knowledge");
      setKnowledgeCount(rows.length);
      setStep("channels");
    });

  const ensureChannels = () =>
    run(async () => {
      let existing = await portalFetch<ChannelRow[]>("/portal/chatbot/channels");
      const have = new Set(existing.map((c) => c.channel));
      for (const channel of CHANNELS) {
        if (have.has(channel)) continue;
        await portalFetch("/portal/chatbot/channels", {
          method: "POST",
          body: JSON.stringify({
            channel,
            status: "not_configured",
          }),
        });
      }
      existing = await portalFetch<ChannelRow[]>("/portal/chatbot/channels");
      setChannels(existing);
      setStep("provider");
    });

  const loadProviders = useCallback(async () => {
    const rows = await portalFetch<ProviderRow[]>("/portal/chatbot/providers");
    setProviders(rows);
    const enabled = rows.find((r) => r.status === "enabled");
    setSelectedProviderId(enabled?.provider_id ?? rows[0]?.provider_id ?? null);
  }, []);

  useEffect(() => {
    if (step === "provider") {
      void run(loadProviders);
    }
  }, [step, loadProviders, run]);

  const selectProvider = () =>
    run(async () => {
      if (!selectedProviderId) {
        throw new PortalApiError(400, "provider_required");
      }
      await portalFetch(`/portal/chatbot/providers/${selectedProviderId}`, {
        method: "PUT",
        body: JSON.stringify({ status: "enabled" }),
      });
      await loadProviders();
      setStep("finish");
    });

  const summary = useMemo(
    () => [
      {
        label: "Business",
        ok: Boolean(profile?.business_name),
        detail: profile?.business_name || "—",
      },
      {
        label: "Knowledge",
        ok: knowledgeCount > 0 || Boolean(services || hours || contacts || faq),
        detail:
          knowledgeCount > 0
            ? `${knowledgeCount} facts`
            : "Template ready — add more anytime",
      },
      {
        label: "Channels",
        ok: channels.length > 0,
        detail: channels.length
          ? `${channels.length} channels registered`
          : "—",
      },
      {
        label: "AI",
        ok: providers.some((p) => p.status === "enabled"),
        detail:
          providers.find((p) => p.status === "enabled")?.display_name ||
          PROVIDER_LABEL[
            providers.find((p) => p.status === "enabled")?.provider_type || ""
          ] ||
          "—",
      },
    ],
    [profile, knowledgeCount, services, hours, contacts, faq, channels, providers],
  );

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 px-1 py-2">
      <header className="space-y-2">
        <Badge>Vector · First Run</Badge>
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Prepare your AI Business Employee
        </h1>
        <p className="text-sm text-[var(--genesis-muted,#a1a1aa)]">
          Orchestrates existing Virtus Core components — no new business logic.
        </p>
      </header>

      {step !== "gate" ? (
        <ol className="flex flex-wrap gap-2" aria-label="First Run steps">
          {STEPS.map((item, index) => {
            const done = activeStep > index;
            const current = activeStep === index;
            return (
              <li
                key={item.id}
                className={`rounded-full px-3 py-1 text-xs ${
                  current
                    ? "bg-white/15 text-white"
                    : done
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "bg-white/5 text-zinc-500"
                }`}
              >
                {index + 1}. {item.label}
              </li>
            );
          })}
        </ol>
      ) : null}

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      {step === "gate" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-lg font-medium text-white">Portal access</h2>
          <p className="text-sm text-zinc-400">
            Sign in, then activate Vector. Demo credentials are prefilled for local
            Genesis.exe verification.
          </p>
          <Field label="Email">
            <Input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </Field>
          <Field label="Password">
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </Field>
          <div className="flex flex-wrap gap-2">
            <Button onClick={login} disabled={busy}>
              Sign in
            </Button>
            <Button variant="secondary" onClick={activateDemo} disabled={busy}>
              Activate DEMO-CHATBOT
            </Button>
            <Button variant="ghost" onClick={purchaseStub} disabled={busy}>
              Stub purchase
            </Button>
          </div>
          {owned ? (
            <p className="text-sm text-emerald-300">Vector ownership detected.</p>
          ) : (
            <p className="text-sm text-zinc-500">
              After sign-in, activate with code DEMO-CHATBOT (or stub purchase).
            </p>
          )}
        </section>
      ) : null}

      {step === "welcome" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-xl font-medium text-white">Meet Vector.</h2>
          <p className="text-base text-zinc-300">
            Let&apos;s prepare your AI Business Employee.
          </p>
          <Button onClick={() => setStep("profile")} disabled={busy}>
            Continue
          </Button>
        </section>
      ) : null}

      {step === "profile" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-lg font-medium text-white">Business Profile</h2>
          <Field label="Company name">
            <Input
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="Smile Clinic"
            />
          </Field>
          <Field label="Industry">
            <select
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
            >
              {templates.map((t) => (
                <option key={t.industry} value={t.industry}>
                  {t.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Language">
            <Input
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="ru"
            />
          </Field>
          <Field label="Timezone">
            <Input
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              placeholder="Europe/Berlin"
            />
          </Field>
          <Button onClick={() => setStep("bootstrap")} disabled={busy || !businessName.trim()}>
            Next — apply template
          </Button>
        </section>
      ) : null}

      {step === "bootstrap" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-lg font-medium text-white">Industry Template</h2>
          <p className="text-sm text-zinc-400">
            Apply the <strong className="text-zinc-200">{industry}</strong> template to{" "}
            <strong className="text-zinc-200">{businessName}</strong>. Uses existing
            bootstrap API only.
          </p>
          {bootstrapNote ? (
            <p className="rounded-lg bg-white/5 px-3 py-2 text-sm text-zinc-300">
              {bootstrapNote}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button onClick={applyBootstrap} disabled={busy}>
              Apply template
            </Button>
            <Button variant="ghost" onClick={() => setStep("profile")} disabled={busy}>
              Back
            </Button>
          </div>
        </section>
      ) : null}

      {step === "knowledge" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-lg font-medium text-white">Business Knowledge</h2>
          <p className="text-sm text-zinc-400">
            Facts only — Vector will use these later. You can skip empty fields.
          </p>
          <Field label="Services">
            <Textarea
              value={services}
              onChange={(e) => setServices(e.target.value)}
              rows={2}
              placeholder="Cleaning, whitening, implants…"
            />
          </Field>
          <Field label="Working hours">
            <Textarea
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              rows={2}
              placeholder="Mon–Fri 09:00–19:00"
            />
          </Field>
          <Field label="Contacts">
            <Textarea
              value={contacts}
              onChange={(e) => setContacts(e.target.value)}
              rows={2}
              placeholder="Phone, address, email"
            />
          </Field>
          <Field label="FAQ">
            <Textarea
              value={faq}
              onChange={(e) => setFaq(e.target.value)}
              rows={2}
              placeholder="Do you accept insurance?"
            />
          </Field>
          <div className="flex flex-wrap gap-2">
            <Button onClick={saveKnowledge} disabled={busy}>
              Save & continue
            </Button>
            <Button
              variant="ghost"
              onClick={() => setStep("channels")}
              disabled={busy}
            >
              Skip for now
            </Button>
          </div>
        </section>
      ) : null}

      {step === "channels" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-lg font-medium text-white">Channels</h2>
          <p className="text-sm text-zinc-400">
            These channels will become part of Vector. Connection stays a stub for
            now — visibility is the goal.
          </p>
          <ul className="grid gap-2 sm:grid-cols-2">
            {CHANNELS.map((channel) => {
              const row = channels.find((c) => c.channel === channel);
              return (
                <li
                  key={channel}
                  className="rounded-xl border border-white/10 bg-black/20 px-3 py-3"
                >
                  <p className="text-sm font-medium capitalize text-white">
                    {channel}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {row?.status || "will register as not_configured"}
                  </p>
                </li>
              );
            })}
          </ul>
          <Button onClick={ensureChannels} disabled={busy}>
            Register channel stubs
          </Button>
        </section>
      ) : null}

      {step === "provider" ? (
        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-lg font-medium text-white">AI Provider</h2>
          <p className="text-sm text-zinc-400">
            Choose where Vector thinks. Keys stay in the environment — not in this
            wizard.
          </p>
          <ul className="space-y-2">
            {providers.map((p) => {
              const selected = selectedProviderId === p.provider_id;
              return (
                <li key={p.provider_id}>
                  <button
                    type="button"
                    onClick={() => setSelectedProviderId(p.provider_id)}
                    className={`flex w-full items-center justify-between rounded-xl border px-3 py-3 text-left text-sm ${
                      selected
                        ? "border-emerald-400/40 bg-emerald-500/10 text-white"
                        : "border-white/10 bg-black/20 text-zinc-300"
                    }`}
                  >
                    <span>
                      {PROVIDER_LABEL[p.provider_type] || p.display_name}
                    </span>
                    <span className="text-xs text-zinc-500">{p.status}</span>
                  </button>
                </li>
              );
            })}
          </ul>
          <Button onClick={selectProvider} disabled={busy || !selectedProviderId}>
            Enable selected provider
          </Button>
        </section>
      ) : null}

      {step === "finish" ? (
        <section className="space-y-4 rounded-2xl border border-emerald-400/20 bg-emerald-500/[0.06] p-5">
          <h2 className="text-xl font-medium text-white">Vector is ready.</h2>
          <ul className="space-y-2">
            {summary.map((item) => (
              <li
                key={item.label}
                className="flex items-center justify-between rounded-lg bg-black/20 px-3 py-2 text-sm"
              >
                <span className="text-zinc-300">
                  {item.label} {item.ok ? "✓" : "·"}
                </span>
                <span className="text-zinc-500">{item.detail}</span>
              </li>
            ))}
          </ul>
          <div className="flex flex-wrap gap-2">
            <ButtonLink href="/projects/chatbot/knowledge">
              Manage knowledge
            </ButtonLink>
            <ButtonLink href="/projects">Back to projects</ButtonLink>
            <Button variant="ghost" onClick={() => setStep("welcome")} disabled={busy}>
              Run again
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function ButtonLink({
  href,
  children,
}: {
  href: string;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center justify-center rounded-xl bg-white px-4 py-2 text-sm font-medium text-black hover:bg-zinc-200"
    >
      {children}
    </Link>
  );
}
