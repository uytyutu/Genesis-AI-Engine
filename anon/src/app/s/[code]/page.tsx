import { redirect } from "next/navigation";

/** Every ANON object is its own door: /s/abc123 → viral space. */
export default async function ShareEntryPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  redirect(`/v/${code}`);
}
