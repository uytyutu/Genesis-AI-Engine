import type { Metadata } from "next";
import { AppShell } from "./components/AppShell";
import { ToastProvider } from "./components/ToastProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Genesis Mission Control",
  description: "Пульт управления вашей цифровой компанией",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className="genesis-os-shell overflow-x-hidden antialiased">
        <ToastProvider>
          <AppShell>{children}</AppShell>
        </ToastProvider>
      </body>
    </html>
  );
}
