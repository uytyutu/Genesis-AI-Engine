type Check = { id: string; label: string; ok: boolean; pending?: boolean };

export function ChecksList({ checks }: { checks: Check[] }) {
  if (!checks.length) return null;
  return (
    <ul className="space-y-2 text-sm">
      {checks.map((c) => (
        <li key={c.id} className="flex justify-between gap-4">
          <span>{c.label}</span>
          <span className={c.ok ? "text-emerald-400" : c.pending ? "text-amber-400" : "text-red-400"}>
            {c.ok ? "✔" : c.pending ? "Ожидается" : "✘"}
          </span>
        </li>
      ))}
    </ul>
  );
}
