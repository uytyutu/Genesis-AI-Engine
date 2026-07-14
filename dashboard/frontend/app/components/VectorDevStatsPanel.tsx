"use client";

export type VectorDevStats = {
  planner?: string;
  llm_capability?: string | null;
  proof_pin?: string | null;
  worker?: string;
  worker_model?: string | null;
  elapsed_sec?: number;
  fallback_label?: string;
  reasons?: string[] | null;
  cloud_llm_used?: boolean;
};

type Props = {
  stats: VectorDevStats | null;
  className?: string;
};

/** Developer-only — last Vector turn routing summary (not visible to clients). */
export function VectorDevStatsPanel({ stats, className = "" }: Props) {
  if (!stats?.planner) return null;

  return (
    <div
      className={`rounded-xl border border-amber-500/25 bg-amber-950/30 px-3 py-2 font-mono text-[10px] leading-relaxed text-amber-100/90 ${className}`}
      aria-label="Vector developer stats"
    >
      <p className="mb-1 font-semibold uppercase tracking-wider text-amber-300/90">
        Последний ответ
      </p>
      <p>
        <span className="text-amber-400/80">Planner:</span> {stats.planner}
      </p>
      {stats.llm_capability ? (
        <p>
          <span className="text-amber-400/80">Capability:</span> {stats.llm_capability}
        </p>
      ) : null}
      <p>
        <span className="text-amber-400/80">Provider:</span> {stats.worker}
        {stats.worker_model ? (
          <span className="text-amber-200/50"> · {stats.worker_model}</span>
        ) : null}
      </p>
      <p>
        <span className="text-amber-400/80">Время:</span>{" "}
        {typeof stats.elapsed_sec === "number" ? `${stats.elapsed_sec} s` : "—"}
      </p>
      <p>
        <span className="text-amber-400/80">Fallback:</span>{" "}
        {stats.fallback_label ?? (stats.cloud_llm_used === false ? "да" : "нет")}
      </p>
      {stats.proof_pin ? (
        <p>
          <span className="text-amber-400/80">Proof:</span> {stats.proof_pin}
        </p>
      ) : null}
      {stats.reasons && stats.reasons.length > 0 ? (
        <div className="mt-1 border-t border-amber-500/20 pt-1">
          <p className="text-amber-400/80">Причина:</p>
          {stats.reasons.map((r) => (
            <p key={r} className="pl-2 text-amber-100/75">
              {r}
            </p>
          ))}
        </div>
      ) : null}
    </div>
  );
}
