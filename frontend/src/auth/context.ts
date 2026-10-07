import { createContext, useContext } from "react";
import type { PublicUser } from "../api/client";

export type AuthState = {
  user: PublicUser | null;
  setUser: (user: PublicUser | null) => void;
  logout: () => void;
};

export const AuthContext = createContext<AuthState | null>(null);
export const STORAGE_KEY = "campus-customs-user";

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
