"use client";

import { PublicPageShell } from "../../components/PublicPageShell";
import { VirtusCoreWebsiteAuditorPanel } from "../../components/VirtusCoreWebsiteAuditorPanel";

export default function WebsiteAuditorPage() {
  return (
    <PublicPageShell>
      <main className="px-4 py-10 sm:px-6 lg:px-8">
        <VirtusCoreWebsiteAuditorPanel locale="de" />
      </main>
    </PublicPageShell>
  );
}
