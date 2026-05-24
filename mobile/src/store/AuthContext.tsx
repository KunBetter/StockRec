import React, { createContext, useContext, useCallback, useState, useEffect } from "react";
import { getAccessToken, clearTokens } from "../services/api";
import type { UserInfo } from "../types/stock";

interface AuthState {
  isLoading: boolean;
  isSignedIn: boolean;
  user: UserInfo | null;
  signOut: () => void;
  setUser: (user: UserInfo) => void;
}

const AuthContext = createContext<AuthState>({
  isLoading: true,
  isSignedIn: false,
  user: null,
  signOut: () => {},
  setUser: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<UserInfo | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      // Token exists — user is signed in
      // In production, validate token by calling /profile/status or similar
      setIsLoading(false);
    } else {
      setIsLoading(false);
    }
  }, []);

  const signOut = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isLoading,
        isSignedIn: !!user || !!getAccessToken(),
        user,
        signOut,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  return useContext(AuthContext);
}
