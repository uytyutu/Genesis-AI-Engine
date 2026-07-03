import Link from "next/link";

export default function MarketplacePage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-lg space-y-6 text-center">
        <h1 className="text-2xl font-bold">Genesis Marketplace</h1>
        <p className="text-genesis-muted">
          Магазин шаблонов и готовых продуктов появится после запуска Factory.
        </p>
        <div className="rounded-xl border border-dashed border-genesis-border bg-genesis-panel p-8 text-left text-sm text-genesis-muted">
          <p className="font-medium text-white">Скоро</p>
          <p className="mt-2">Landing #145 · ★★★★★ · 29 € · [ Купить ]</p>
          <p className="mt-2">Продать свой шаблон · комиссия платформы</p>
        </div>
        <Link href="/" className="text-sm text-genesis-accent hover:underline">
          ← На главную
        </Link>
      </div>
    </main>
  );
}
