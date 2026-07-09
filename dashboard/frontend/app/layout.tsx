import type { Metadata } from "next";
import { AppShell } from "./components/AppShell";
import { LocaleProvider } from "./context/LocaleContext";
import { ToastProvider } from "./components/ToastProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Virtus Core",
    template: "%s · Virtus Core",
  },
  description: "Virtus Core — intelligent platform with Vector AI assistant",
  icons: {
    icon: [
      { url: "/brand/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/brand/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/brand/vector-mark.svg", type: "image/svg+xml" },
    ],
    apple: [{ url: "/brand/apple-touch-icon.png", sizes: "180x180" }],
  },
  manifest: "/manifest.webmanifest",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className="genesis-os-shell overflow-x-hidden antialiased">
        <LocaleProvider>
          <ToastProvider>
            <AppShell>{children}</AppShell>
          </ToastProvider>
        </LocaleProvider>
      </body>
    </html>
  );
}
