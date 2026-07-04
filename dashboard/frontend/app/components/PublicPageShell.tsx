import { PublicSiteFooter } from "./PublicSiteFooter";
import { PublicSiteHeader } from "./PublicSiteHeader";

export function PublicPageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
      <PublicSiteHeader />
      <div className="animate-fade-up">{children}</div>
      <PublicSiteFooter />
    </div>
  );
}
