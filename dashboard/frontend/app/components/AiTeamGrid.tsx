"use client";

type Employee = {
  id: string;
  label: string;
  icon: string;
  status: string;
  status_label: string;
  message: string;
};

const STATUS_STYLES: Record<string, { dot: string; ring: string; bg: string }> = {
  online: {
    dot: "status-dot-online",
    ring: "ring-emerald-500/20",
    bg: "from-emerald-500/10 to-transparent",
  },
  degraded: {
    dot: "status-dot-degraded",
    ring: "ring-amber-500/20",
    bg: "from-amber-500/10 to-transparent",
  },
  offline: {
    dot: "status-dot-offline",
    ring: "ring-zinc-500/20",
    bg: "from-zinc-500/5 to-transparent",
  },
};

export function AiTeamGrid({ employees }: { employees: Employee[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {employees.map((emp) => {
        const style = STATUS_STYLES[emp.status] ?? STATUS_STYLES.offline;
        return (
          <div
            key={emp.id}
            className={`group relative overflow-hidden rounded-xl border border-genesis-border-subtle bg-gradient-to-br ${style.bg} p-4 ring-1 ${style.ring} transition-transform duration-200 hover:scale-[1.01]`}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-medium">{emp.label}</p>
                <p className="mt-1 flex items-center gap-2 text-xs text-genesis-muted">
                  <span className={`inline-block h-2 w-2 rounded-full ${style.dot}`} />
                  {emp.status_label}
                </p>
              </div>
              <span className="text-lg opacity-80">{emp.icon}</span>
            </div>
            {emp.message && (
              <p className="mt-3 text-xs leading-relaxed text-genesis-muted/90 line-clamp-2">
                «{emp.message}»
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
