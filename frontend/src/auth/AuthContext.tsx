import { useEffect, useMemo, useState, type ReactNode } from "react";
import type { PublicUser } from "../api/client";
import { AuthContext, STORAGE_KEY, type AuthState } from "./context";

// Only the non-sensitive PublicUser is ever kept — no password, no hash, no
// token. This is display state so the UI knows who is signed in.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<PublicUser | null>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as PublicUser) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    else localStorage.removeItem(STORAGE_KEY);
  }, [user]);

  const value = useMemo<AuthState>(
    () => ({
      user,
      setUser: setUserState,
      logout: () => setUserState(null),
    }),
    [user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
