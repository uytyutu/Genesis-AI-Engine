import Link from "next/link";

export default function DevModePage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-lg space-y-4">
        <h1 className="text-2xl font-bold text-yellow-500">Режим разработчика</h1>
        <p className="text-sm text-genesis-muted">
          Технические инструменты — только для диагностики. Владельцу обычно не нужны.
        </p>
        <div className="grid gap-2">
          <Link href="/monitor" className="rounded-lg border border-genesis-border bg-genesis-panel px-4 py-3 hover:border-genesis-accent">
            Мониторинг модулей (Kernel, Brain…)
          </Link>
          <Link href="/tasks" className="rounded-lg border border-genesis-border bg-genesis-panel px-4 py-3 hover:border-genesis-accent">
            Журнал задач
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-genesis-border bg-genesis-panel px-4 py-3 hover:border-genesis-accent"
          >
            API Swagger
          </a>
        </div>
        <Link href="/" className="text-sm text-genesis-accent hover:underline">
          ← Режим владельца
        </Link>
      </div>
    </main>
  );
}
