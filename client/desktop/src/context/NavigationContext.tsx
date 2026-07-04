import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { NavId } from "../components/Sidebar";

type NavigationContextValue = {
  nav: NavId;
  setNav: (id: NavId) => void;
  projectId: string | null;
  openProject: (id: string) => void;
  closeProject: () => void;
  chatPrefill: string | null;
  openChat: (prefill?: string) => void;
  clearChatPrefill: () => void;
};

const NavigationContext = createContext<NavigationContextValue | null>(null);

export function NavigationProvider({ children }: { children: ReactNode }) {
  const [nav, setNavState] = useState<NavId>("home");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [chatPrefill, setChatPrefill] = useState<string | null>(null);

  const setNav = (id: NavId) => {
    setNavState(id);
    if (id !== "projects") setProjectId(null);
  };

  const value = useMemo(
    () => ({
      nav,
      setNav,
      projectId,
      openProject: (id: string) => {
        setProjectId(id);
        setNavState("projects");
      },
      closeProject: () => setProjectId(null),
      chatPrefill,
      openChat: (prefill?: string) => {
        setChatPrefill(prefill ?? null);
        setNavState("chat");
      },
      clearChatPrefill: () => setChatPrefill(null),
    }),
    [nav, projectId, chatPrefill],
  );

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation(): NavigationContextValue {
  const ctx = useContext(NavigationContext);
  if (!ctx) throw new Error("useNavigation outside provider");
  return ctx;
}
