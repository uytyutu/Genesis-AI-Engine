import { redirect } from "next/navigation";

/** MC 2.0 — Virtus morning screen is Overview, not Farm. */
export default function HomePage() {
  redirect("/executive");
}
