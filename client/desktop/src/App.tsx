import { useState } from "react";
import { AppSettingsProvider } from "./context/AppSettingsContext";
import { SessionProvider, useSession } from "./context/SessionContext";
import { Shell } from "./components/Shell";
import type { NavId } from "./components/Sidebar";
import { ConnectPage } from "./pages/ConnectPage";
import { HomePage } from "./pages/HomePage";
import { ChatPage } from "./pages/ChatPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SettingsPage } from "./pages/SettingsPage";
import "./styles/globals.css";

function AppRoutes() {
  const [nav, setNav] = useState<NavId>("home");
  const { connected, connecting, ownerLabel, disconnect } = useSession();

  if (connecting) {
    return (
      <div className="boot">
        <p>Connecting to Genesis…</p>
      </div>
    );
  }

  if (!connected) {
    return <ConnectPage />;
  }

  return (
    <Shell
      active={nav}
      ownerLabel={ownerLabel}
      connected={connected}
      onNavigate={setNav}
      onDisconnect={disconnect}
    >
      {nav === "home" && <HomePage />}
      {nav === "chat" && <ChatPage />}
      {nav === "projects" && <ProjectsPage />}
      {nav === "settings" && <SettingsPage />}
    </Shell>
  );
}

export default function App() {
  return (
    <AppSettingsProvider>
      <SessionProvider>
        <AppRoutes />
      </SessionProvider>
    </AppSettingsProvider>
  );
}
