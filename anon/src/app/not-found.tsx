import Link from "next/link";

export default function NotFound() {
  return (
    <main className="anon-card mx-auto mt-20 max-w-md p-8 text-center">
      <p className="text-4xl">🌑</p>
      <h1 className="mt-4 text-2xl font-semibold">404</h1>
      <p className="mt-2 text-sm anon-muted">This page got lost in the veil.</p>
      <Link href="/" className="anon-btn anon-btn-primary mt-6 inline-flex">
        Back to ANON
      </Link>
    </main>
  );
}
