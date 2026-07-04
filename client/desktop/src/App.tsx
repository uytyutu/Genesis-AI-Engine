import { useState } from "react";
import { AppSettingsProvider } from "./context/AppSettingsContext";
import { SessionProvider, useSession } from "./context/SessionContext";
import { NavigationProvider, useNavigation } from "./context/NavigationContext";
import {
  CommandPalette,
  useCommandPaletteShortcut,
} from "./components/CommandPalette";
import { Shell } from "./components/Shell";
import { ConnectPage } from "./pages/ConnectPage";
import { HomePage } from "./pages/HomePage";
import { ChatPage } from "./pages/ChatPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SettingsPage } from "./pages/SettingsPage";
import "./styles/globals.css";

function AppRoutes() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const { connected, connecting, ownerLabel, disconnect, refresh } = useSession();
  const { nav, setNav, openChat } = useNavigation();

  useCommandPaletteShortcut(() => setPaletteOpen(true));

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
    <>
      <Shell
        active={nav}
        ownerLabel={ownerLabel}
        connected={connected}
        onNavigate={setNav}
        onDisconnect={disconnect}
        onOpenPalette={() => setPaletteOpen(true)}
      >
        {nav === "home" && <HomePage />}
        {nav === "chat" && <ChatPage />}
        {nav === "projects" && <ProjectsPage />}
        {nav === "settings" && <SettingsPage />}
      </Shell>
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        onNavigate={setNav}
        onDisconnect={disconnect}
        onRefresh={() => void refresh()}
        onOpenChat={openChat}
      />
    </>
  );
}

export default function App() {
  return (
    <AppSettingsProvider>
      <SessionProvider>
        <NavigationProvider>
          <AppRoutes />
        </NavigationProvider>
      </SessionProvider>
    </AppSettingsProvider>
  );
}
