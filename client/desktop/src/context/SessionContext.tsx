import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ApiError } from "../lib/apiClient";
import {
  fetchOwnerDashboard,
  fetchSystemStatus,
  type OwnerDashboard,
} from "../lib/endpoints";
import { useAppSettings } from "./AppSettingsContext";

type SessionContextValue = {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  dashboard: OwnerDashboard | null;
  systemVersion: string | null;
  ownerLabel: string;
  connect: () => Promise<boolean>;
  disconnect: () => void;
  refresh: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const { settings, updateSettings } = useAppSettings();
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<OwnerDashboard | null>(null);
  const [systemVersion, setSystemVersion] = useState<string | null>(null);

  const ownerLabel =
    settings.ownerName.trim() || dashboard?.owner_name || "Owner";

  const connect = useCallback(async (): Promise<boolean> => {
    setConnecting(true);
    setError(null);
    try {
      const status = await fetchSystemStatus(settings);
      const dash = await fetchOwnerDashboard(settings);
      setSystemVersion(status.version);
      setDashboard(dash);
      setConnected(true);
      updateSettings({ sessionActive: true });
      return true;
    } catch (e) {
      const message =
        e instanceof ApiError
          ? `API error ${e.status} — check URL and network`
          : e instanceof Error
            ? e.message
            : "Connection failed";
      setError(message);
      setConnected(false);
      setDashboard(null);
      return false;
    } finally {
      setConnecting(false);
    }
  }, [settings, updateSettings]);

  const disconnect = useCallback(() => {
    setConnected(false);
    setDashboard(null);
    setSystemVersion(null);
    setError(null);
    updateSettings({ sessionActive: false });
  }, [updateSettings]);

  const refresh = useCallback(async () => {
    if (!connected) return;
    try {
      const dash = await fetchOwnerDashboard(settings);
      setDashboard(dash);
      setError(null);
    } catch (e) {
      const message = e instanceof Error ? e.message : "Refresh failed";
      setError(message);
    }
  }, [connected, settings]);

  const booted = useRef(false);

  useEffect(() => {
    if (booted.current || !settings.sessionActive) return;
    booted.current = true;
    void connect();
  }, [settings.sessionActive, connect]);

  const value = useMemo(
    () => ({
      connected,
      connecting,
      error,
      dashboard,
      systemVersion,
      ownerLabel,
      connect,
      disconnect,
      refresh,
    }),
    [
      connected,
      connecting,
      error,
      dashboard,
      systemVersion,
      ownerLabel,
      connect,
      disconnect,
      refresh,
    ],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession outside provider");
  return ctx;
}
