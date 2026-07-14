import { redirect } from "next/navigation";

/** Legacy path — farm journal lives at /journal (M3 master workshop). */
export default function OpportunitiesRedirect() {
  redirect("/journal");
}
