"use client";

type Props = {
  values: number[];
  height?: number;
  className?: string;
  positive?: boolean;
};

export function Sparkline({ values, height = 48, className = "", positive = true }: Props) {
  if (!values.length) {
    return (
      <div
        className={`flex items-center justify-center rounded-xl border border-dashed border-genesis-border/60 text-xs text-genesis-muted ${className}`}
        style={{ height }}
      >
        Нет данных
      </div>
    );
  }

  const w = 200;
  const pad = 4;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = pad + (i / Math.max(1, values.length - 1)) * (w - pad * 2);
      const y = pad + (1 - (v - min) / range) * (height - pad * 2);
      return `${x},${y}`;
    })
    .join(" ");

  const stroke = positive ? "#34d399" : "#fb7185";
  const fillId = `spark-${positive ? "g" : "r"}`;

  return (
    <svg viewBox={`0 0 ${w} ${height}`} className={`w-full ${className}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`${pad},${height - pad} ${pts} ${w - pad},${height - pad}`} fill={`url(#${fillId})`} />
      <polyline
        points={pts}
        fill="none"
        stroke={stroke}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
