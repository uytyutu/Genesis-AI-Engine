import { redirect } from "next/navigation";

/** Legacy URL — public pricing lives on /services and /order. */
export default function PricingPage() {
  redirect("/site");
}
