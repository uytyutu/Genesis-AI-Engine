import { useState } from "react";
import { AppSettingsProvider } from "./context/AppSettingsContext";
import { Shell } from "./components/Shell";
import type { NavId } from "./components/Sidebar";
import { HomePage } from "./pages/HomePage";
import { SettingsPage } from "./pages/SettingsPage";
import "./styles/globals.css";

function AppRoutes() {
  const [nav, setNav] = useState<NavId>("home");

  return (
    <Shell active={nav} onNavigate={setNav}>
      {nav === "home" ? <HomePage /> : <SettingsPage />}
    </Shell>
  );
}

export default function App() {
  return (
    <AppSettingsProvider>
      <AppRoutes />
    </AppSettingsProvider>
  );
}
