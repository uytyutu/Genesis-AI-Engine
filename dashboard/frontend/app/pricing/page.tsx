import { redirect } from "next/navigation";

/** Legacy URL — Products is the canonical subscription page. */
export default function PricingPage() {
  redirect("/products");
}
