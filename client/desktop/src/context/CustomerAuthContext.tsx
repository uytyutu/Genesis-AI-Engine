import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useAppSettings } from "./AppSettingsContext";
import {
  advanceWelcome,
  answerWelcome,
  loginCustomer,
  registerCustomer,
} from "../lib/customerApi";
import {
  applyWelcomeToSession,
  clearCustomerSession,
  loadCustomerSession,
  saveCustomerSession,
  sessionFromAuthResponse,
  type CustomerSession,
  type WelcomeState,
} from "../lib/customerSession";
import { setPlatformVisitorId, getPriorVisitorId } from "../lib/visitorId";

export type CustomerAuthPhase = "register" | "welcome" | "ready";

type CustomerAuthContextValue = {
  session: CustomerSession | null;
  welcome: WelcomeState | null;
  phase: CustomerAuthPhase;
  busy: boolean;
  error: string | null;
  register: (name: string, email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  startWelcome: () => Promise<void>;
  answerWizard: (answer: string, skip?: boolean) => Promise<void>;
  setWelcome: (welcome: WelcomeState) => void;
};

const CustomerAuthContext = createContext<CustomerAuthContextValue | null>(null);

function resolvePhase(session: CustomerSession | null): CustomerAuthPhase {
  if (!session) return "register";
  if (session.welcomePhase === "greeting" || session.welcomePhase === "wizard") {
    return "welcome";
  }
  return "ready";
}

export function CustomerAuthProvider({ children }: { children: ReactNode }) {
  const { settings } = useAppSettings();
  const [session, setSession] = useState<CustomerSession | null>(() =>
    loadCustomerSession(),
  );
  const [welcome, setWelcome] = useState<WelcomeState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const phase = resolvePhase(session);

  const applyAuth = useCallback((data: Parameters<typeof sessionFromAuthResponse>[0]) => {
    const next = sessionFromAuthResponse(data);
    if (next.platformVisitorId) {
      setPlatformVisitorId(next.platformVisitorId);
    }
    saveCustomerSession(next);
    setSession(next);
    setWelcome(data.welcome ?? null);
    setError(null);
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      setBusy(true);
      setError(null);
      try {
        const prior = getPriorVisitorId();
        const data = await registerCustomer(settings, {
          name,
          email,
          password,
          visitor_id: prior || undefined,
        });
        applyAuth(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка регистрации");
      } finally {
        setBusy(false);
      }
    },
    [settings, applyAuth],
  );

  const login = useCallback(
    async (email: string, password: string) => {
      setBusy(true);
      setError(null);
      try {
        const data = await loginCustomer(settings, { email, password });
        applyAuth(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка входа");
      } finally {
        setBusy(false);
      }
    },
    [settings, applyAuth],
  );

  const logout = useCallback(() => {
    clearCustomerSession();
    setSession(null);
    setWelcome(null);
    setError(null);
  }, []);

  const startWelcome = useCallback(async () => {
    if (!session?.token) return;
    setBusy(true);
    setError(null);
    try {
      const state = await advanceWelcome(settings, session.token);
      setWelcome(state);
      applyWelcomeToSession(session, state);
      setSession(loadCustomerSession());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }, [session, settings]);

  const answerWizard = useCallback(
    async (answer: string, skip = false) => {
      if (!session?.token) return;
      setBusy(true);
      setError(null);
      try {
        const state = await answerWelcome(settings, session.token, { answer, skip });
        setWelcome(state);
        const updated = applyWelcomeToSession(session, state);
        setSession(updated);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка");
      } finally {
        setBusy(false);
      }
    },
    [session, settings],
  );

  const value = useMemo(
    () => ({
      session,
      welcome,
      phase,
      busy,
      error,
      register,
      login,
      logout,
      startWelcome,
      answerWizard,
      setWelcome,
    }),
    [
      session,
      welcome,
      phase,
      busy,
      error,
      register,
      login,
      logout,
      startWelcome,
      answerWizard,
    ],
  );

  return (
    <CustomerAuthContext.Provider value={value}>
      {children}
    </CustomerAuthContext.Provider>
  );
}

export function useCustomerAuth(): CustomerAuthContextValue {
  const ctx = useContext(CustomerAuthContext);
  if (!ctx) throw new Error("useCustomerAuth outside provider");
  return ctx;
}
