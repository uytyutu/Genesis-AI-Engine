import { redirect } from "next/navigation";

/** Folder URL without index.html used to 404 — send to static gallery. */
export default function RealityGalleryPage() {
  redirect("/reality-gallery/index.html");
}
