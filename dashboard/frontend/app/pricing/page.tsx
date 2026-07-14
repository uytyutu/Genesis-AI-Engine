import { redirect } from "next/navigation";

/** Legacy URL — public pricing lives on /services. */
export default function PricingPage() {
  redirect("/services");
}
