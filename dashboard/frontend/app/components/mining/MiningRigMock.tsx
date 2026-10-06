"use client";

/** Mining atmosphere mock — showcase layout, not live balances. */

export function MiningRigMock({ compact = false }: { compact?: boolean }) {
  const workers = [
    { name: "ASIC", kind: "SHA-256d Bitcoin worker", state: "NOT TESTED" },
    { name: "Server", kind: "SHA-256 specialized only", state: "NOT TESTED" },
    { name: "PC", kind: "Compute — not BTC", state: "FUTURE" },
    { name: "Mobile", kind: "Monitor only", state: "CONTROL" },
  ];

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-amber-400/25 bg-gradient-to-br from-[#120e08] via-[#0c1014] to-[#071018] p-4 sm:p-5 ${
        compact ? "min-h-[180px]" : "min-h-[280px] sm:min-h-[320px]"
      }`}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "linear-gradient(rgba(245,165,36,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(62,224,198,0.08) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />
      <p className="relative text-[10px] font-semibold uppercase tracking-[0.22em] text-amber-200/80">
        Virtus Mining · Hardware control
      </p>
      <p className="relative mt-1 text-sm font-semibold text-white sm:text-base">
        Connect hardware. Track real pool performance.
      </p>
      <div className="relative mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {workers.map((w) => (
          <div
            key={w.name}
            className="rounded-xl border border-amber-400/20 bg-black/35 px-3 py-3"
          >
            <p className="text-xs font-bold text-amber-100">{w.name}</p>
            <p className="mt-1 text-[11px] text-zinc-400">{w.kind}</p>
            <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-cyan-300/80">
              {w.state}
            </p>
          </div>
        ))}
      </div>
      {!compact ? (
        <div className="relative mt-4 flex items-end gap-1">
          {Array.from({ length: 18 }).map((_, i) => (
            <div
              key={i}
              className="flex-1 rounded-sm bg-amber-400/70"
              style={{ height: `${10 + ((i * 17) % 42)}px`, opacity: 0.35 + (i % 5) * 0.1 }}
              aria-hidden
            />
          ))}
        </div>
      ) : null}
      <span className="absolute right-3 top-3 rounded border border-amber-500/40 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-amber-200">
        Showcase
      </span>
    </div>
  );
}
