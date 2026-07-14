import { useEffect, useRef, useState } from "react";
import { AppSettingsProvider, useAppSettings } from "./context/AppSettingsContext";
import { CustomerAuthProvider, useCustomerAuth } from "./context/CustomerAuthContext";
import { SessionProvider, useSession } from "./context/SessionContext";
import { NavigationProvider, useNavigation } from "./context/NavigationContext";
import {
  CommandPalette,
  useCommandPaletteShortcut,
} from "./components/CommandPalette";
import { Shell } from "./components/Shell";
import { ConnectPage } from "./pages/ConnectPage";
import { RegisterPage } from "./pages/RegisterPage";
import { WelcomePage } from "./pages/WelcomePage";
import { CompanyHomePage } from "./pages/CompanyHomePage";
import { HomePage } from "./pages/HomePage";
import { ChatPage } from "./pages/ChatPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { DevStudioPage } from "./pages/DevStudioPage";
import { SettingsPage } from "./pages/SettingsPage";
import { I18nProvider } from "./i18n/I18nProvider";
import { useI18n } from "./i18n/I18nProvider";
import "./styles/globals.css";

function CustomerAppRoutes() {
  const { session, logout } = useCustomerAuth();
  const { nav, setNav } = useNavigation();
  const booted = useRef(false);
  const [vectorThinking, setVectorThinking] = useState(false);

  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    setNav("chat");
  }, [setNav]);

  const label = session?.name ?? "Компания";

  return (
    <>
      <Shell
        active={nav}
        ownerLabel={label}
        connected
        customerMode
        vectorThinking={vectorThinking}
        onNavigate={setNav}
        onDisconnect={logout}
        onOpenPalette={() => undefined}
      >
        {nav === "home" && <CompanyHomePage />}
        {nav === "chat" && <ChatPage onBusyChange={setVectorThinking} />}
        {nav === "projects" && <ProjectsPage />}
        {nav === "settings" && <SettingsPage />}
      </Shell>
    </>
  );
}

function DevAppRoutes() {
  const { t } = useI18n();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const { connected, connecting, ownerLabel, disconnect, refresh } = useSession();
  const { nav, setNav, openChat } = useNavigation();

  useCommandPaletteShortcut(() => setPaletteOpen(true));

  if (connecting) {
    return (
      <div className="boot">
        <p>{t("boot.connecting")}</p>
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
        {nav === "studio" && <DevStudioPage />}
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

function AppRoutes() {
  const { settings } = useAppSettings();
  const { phase } = useCustomerAuth();

  if (settings.devMode) {
    return <DevAppRoutes />;
  }

  if (phase === "register") {
    return <RegisterPage />;
  }

  if (phase === "welcome") {
    return <WelcomePage />;
  }

  return <CustomerAppRoutes />;
}

export default function App() {
  return (
    <AppSettingsProvider>
      <AppWithLocale />
    </AppSettingsProvider>
  );
}

function AppWithLocale() {
  const { settings, updateSettings } = useAppSettings();
  return (
    <I18nProvider
      locale={settings.locale}
      onLocaleChange={(locale: import("@genesis/i18n/types").LocaleId) =>
        updateSettings({ locale })
      }
    >
      <CustomerAuthProvider>
        <SessionProvider>
          <NavigationProvider>
            <AppRoutes />
          </NavigationProvider>
        </SessionProvider>
      </CustomerAuthProvider>
    </I18nProvider>
  );
}
