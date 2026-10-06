"use client";

/** Honest product mockups — not screenshots of other product types. */

export function BotChatMock({
  variant = "receptionist",
  compact = false,
}: {
  variant?: "receptionist" | "support" | "sales" | "booking" | "faq";
  compact?: boolean;
}) {
  const threads: Record<string, { who: "u" | "b"; text: string }[]> = {
    receptionist: [
      { who: "u", text: "Need a quote for a bathroom remodel — Berlin." },
      { who: "b", text: "Got it. Area in m², preferred week, and photos if you have them?" },
      { who: "u", text: "About 8 m² · next month · sending photos." },
      { who: "b", text: "Lead ready for the owner — Telegram + website chat." },
    ],
    support: [
      { who: "u", text: "Do you ship to Austria?" },
      { who: "b", text: "Yes — shipping options are listed on Checkout (owner Stripe)." },
      { who: "u", text: "And returns?" },
      { who: "b", text: "Return policy is on your Widerruf page — I only use confirmed facts." },
    ],
    sales: [
      { who: "u", text: "Which website package fits a local café?" },
      { who: "b", text: "Business is the usual fit — contact, menu, booking CTA." },
      { who: "u", text: "Can I edit after purchase?" },
      { who: "b", text: "From Business: Client Workspace for content & media." },
    ],
    booking: [
      { who: "u", text: "Book a cut Saturday morning." },
      { who: "b", text: "Which stylist, and phone for confirmation?" },
      { who: "u", text: "Any · +49 …" },
      { who: "b", text: "Request sent to the shop — owner confirms the slot." },
    ],
    faq: [
      { who: "u", text: "Which channels work today?" },
      { who: "b", text: "Telegram and website chat — I only use your confirmed product facts." },
    ],
  };
  const msgs = threads[variant] || threads.receptionist;

  return (
    <div
      className={`flex flex-col overflow-hidden rounded-2xl border border-emerald-400/25 bg-[#0c1210] shadow-[0_24px_60px_-28px_rgba(0,0,0,0.9)] ${
        compact ? "h-full min-h-[160px]" : "min-h-[280px] sm:min-h-[320px]"
      }`}
    >
      <div className="flex items-center gap-2 border-b border-white/10 bg-emerald-950/50 px-3 py-2.5">
        <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-100/90">
          Virtus AI · Chat
        </span>
        <span className="ml-auto text-[10px] text-emerald-200/50">Showcase</span>
      </div>
      <div className={`flex flex-1 flex-col gap-2 overflow-hidden p-3 ${compact ? "text-[10px]" : "text-xs sm:text-sm"}`}>
        {msgs.map((m, i) => (
          <div
            key={`${variant}-${i}`}
            className={`max-w-[88%] rounded-2xl px-3 py-2 leading-snug ${
              m.who === "u"
                ? "self-end rounded-br-md bg-white/10 text-zinc-100"
                : "self-start rounded-bl-md bg-emerald-600/90 text-white"
            }`}
          >
            {m.text}
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-1.5 border-t border-white/10 px-3 py-2">
        {["Quote", "Booking", "FAQ"].map((a) => (
          <span
            key={a}
            className="rounded-full border border-emerald-400/30 px-2 py-0.5 text-[10px] text-emerald-100/80"
          >
            {a}
          </span>
        ))}
      </div>
    </div>
  );
}

export function OfficeDocsMock({ compact = false }: { compact?: boolean }) {
  const steps = [
    { label: "PDF", tone: "bg-rose-500/90" },
    { label: "Understand", tone: "bg-sky-500/80" },
    { label: "Translate", tone: "bg-violet-500/80" },
    { label: "Calculate", tone: "bg-amber-500/80" },
    { label: "Create", tone: "bg-emerald-500/80" },
    { label: "DOCX · XLSX", tone: "bg-blue-600/90" },
  ];
  const formats = [
    { id: "PDF", sub: "Upload" },
    { id: "DOCX", sub: "Word" },
    { id: "XLSX", sub: "Excel" },
    { id: "CSV", sub: "Tables" },
    { id: "OCR", sub: "Scan" },
    { id: "Σ", sub: "Calc" },
  ];

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-sky-400/20 bg-gradient-to-br from-[#0a1220] via-[#0d1524] to-[#12101a] p-4 sm:p-5 ${
        compact ? "min-h-[160px]" : "min-h-[280px] sm:min-h-[320px]"
      }`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-sky-200/70">
        Virtus Office · Digital Office
      </p>
      <p className="mt-1 text-sm font-semibold text-white sm:text-base">
        Your documents → structured work
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-1.5 sm:gap-2">
        {steps.map((s, i) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <span
              className={`rounded-lg px-2 py-1 text-[10px] font-bold text-white sm:text-[11px] ${s.tone}`}
            >
              {s.label}
            </span>
            {i < steps.length - 1 ? (
              <span className="text-zinc-500" aria-hidden>
                →
              </span>
            ) : null}
          </div>
        ))}
      </div>
      <div className="mt-5 grid grid-cols-3 gap-2 sm:grid-cols-6">
        {formats.map((f) => (
          <div
            key={f.id}
            className="rounded-xl border border-white/10 bg-white/[0.04] px-2 py-3 text-center"
          >
            <p className="text-sm font-bold tracking-tight text-white">{f.id}</p>
            <p className="mt-0.5 text-[10px] text-zinc-400">{f.sub}</p>
          </div>
        ))}
      </div>
      {!compact ? (
        <p className="mt-4 text-[11px] leading-relaxed text-zinc-400">
          Translation · CV · Excel extract · DOCX — from client data only. Drafts, not legal advice.
        </p>
      ) : null}
      <span className="absolute right-3 top-3 text-[10px] text-zinc-500">Showcase</span>
    </div>
  );
}

export function AutomationFlowMock({ compact = false }: { compact?: boolean }) {
  const nodes = ["Inquiry", "Qualify", "CRM", "Task", "Follow-up"];
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-violet-400/20 bg-gradient-to-br from-[#120f1c] to-[#0a0a12] p-4 sm:p-5 ${
        compact ? "min-h-[160px]" : "min-h-[280px] sm:min-h-[320px]"
      }`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-violet-200/70">
        Business Automation
      </p>
      <p className="mt-1 text-sm font-semibold text-white sm:text-base">
        Inquiry → qualify → task → follow-up
      </p>
      <div className="mt-6 flex flex-wrap items-center gap-2">
        {nodes.map((n, i) => (
          <div key={n} className="flex items-center gap-2">
            <div className="rounded-xl border border-violet-400/35 bg-violet-500/15 px-3 py-2 text-xs font-semibold text-violet-100">
              {n}
            </div>
            {i < nodes.length - 1 ? (
              <span className="text-violet-400/60" aria-hidden>
                →
              </span>
            ) : null}
          </div>
        ))}
      </div>
      {!compact ? (
        <p className="mt-5 text-[11px] text-zinc-400">
          Set up once for your process — owner receives ready follow-ups.
        </p>
      ) : null}
      <span className="absolute right-3 top-3 text-[10px] text-zinc-500">Showcase</span>
    </div>
  );
}

export function ShopStorefrontMock({
  thumb,
  title,
}: {
  thumb: string;
  title: string;
}) {
  return (
    <div className="relative h-full min-h-[280px] overflow-hidden rounded-2xl border border-violet-400/25 bg-[#120e18] sm:min-h-[320px]">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={thumb} alt="" className="absolute inset-0 h-full w-full object-cover opacity-90" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 p-4">
        <div className="mb-3 grid grid-cols-3 gap-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="aspect-square rounded-lg border border-white/15 bg-white/10 backdrop-blur-sm"
              aria-hidden
            />
          ))}
        </div>
        <div className="flex items-center justify-between gap-2 rounded-xl border border-white/15 bg-black/50 px-3 py-2 backdrop-blur-md">
          <span className="text-xs font-semibold text-white">{title}</span>
          <span className="rounded-lg bg-violet-600 px-2.5 py-1 text-[10px] font-bold text-white">
            Cart · Checkout
          </span>
        </div>
      </div>
      <span className="absolute left-3 top-3 rounded-full bg-violet-600/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-white">
        Online Shop
      </span>
    </div>
  );
}

export function WebsiteBrowserMock({
  thumb,
  title,
}: {
  thumb: string;
  title: string;
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-sky-400/25 bg-[#0c1018] shadow-[0_24px_60px_-28px_rgba(0,0,0,0.9)]">
      <div className="flex items-center gap-1.5 border-b border-white/10 bg-white/[0.04] px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-rose-400/80" />
        <span className="h-2 w-2 rounded-full bg-amber-400/80" />
        <span className="h-2 w-2 rounded-full bg-emerald-400/80" />
        <span className="ml-2 truncate text-[10px] text-zinc-500">{title}</span>
      </div>
      <div className="relative aspect-[16/10] min-h-[240px] sm:min-h-[300px]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={thumb} alt="" className="absolute inset-0 h-full w-full object-cover" />
        <span className="absolute left-3 top-3 rounded-full bg-sky-600/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-white">
          Website
        </span>
      </div>
    </div>
  );
}
