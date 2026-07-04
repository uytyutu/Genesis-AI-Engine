import { PublicSiteFooter } from "./PublicSiteFooter";
import { PublicSiteHeader } from "./PublicSiteHeader";

export function PublicPageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-genesis-accent focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
      >
        Перейти к содержимому
      </a>
      <PublicSiteHeader />
      <div id="main-content" className="animate-fade-up" role="main">
        {children}
      </div>
      <PublicSiteFooter />
    </div>
  );
}
