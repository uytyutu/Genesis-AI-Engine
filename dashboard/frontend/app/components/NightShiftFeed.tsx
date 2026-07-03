"use client";

type Event = {
  at: string;
  department: string;
  message: string;
  icon: string;
};

export function NightShiftFeed({ feed }: { feed: Event[] }) {
  if (!feed.length) return null;

  return (
    <ul className="space-y-3">
      {feed.map((e, i) => (
        <li
          key={`${e.at}-${e.department}-${i}`}
          className="border-b border-genesis-border-subtle/60 pb-3 last:border-0"
        >
          <div className="flex items-baseline gap-3 text-xs">
            <span className="w-10 shrink-0 tabular-nums text-genesis-purple">{e.at}</span>
            <span className="font-semibold text-genesis-text">{e.department}</span>
          </div>
          <p className="mt-1.5 pl-[3.25rem] text-sm text-genesis-muted">
            {e.icon} {e.message}
          </p>
        </li>
      ))}
    </ul>
  );
}
