import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  apiRequest,
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  USER_KEY,
} from "@/lib/api";
import {
  AuthResponse,
  AuthUser,
  LoginPayload,
  RegisterPayload,
} from "@/types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  accessToken: string | null;
  isBootstrapping: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  handleAuthResponse: (response: AuthResponse) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const readStoredJson = <T,>(key: string): T | null => {
  try {
    const raw =
      typeof window !== "undefined" ? window.localStorage.getItem(key) : null;
    return raw ? (JSON.parse(raw) as T) : null;
  } catch (error) {
    return null;
  }
};

const storeJson = (key: string, value: unknown) => {
  if (typeof window === "undefined") return;
  if (value === null || value === undefined) {
    window.localStorage.removeItem(key);
    return;
  }
  window.localStorage.setItem(key, JSON.stringify(value));
};

const storeValue = (key: string, value: string | null) => {
  if (typeof window === "undefined") return;
  if (value) {
    window.localStorage.setItem(key, value);
  } else {
    window.localStorage.removeItem(key);
  }
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(() =>
    readStoredJson<AuthUser>(USER_KEY),
  );
  const [accessToken, setAccessToken] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
  });
  const [refreshToken, setRefreshToken] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(REFRESH_TOKEN_KEY);
  });
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  const persistAuth = useCallback(
    (payload: {
      user: AuthUser;
      access_token: string;
      refresh_token?: string | null;
    }) => {
      setUser(payload.user);
      setAccessToken(payload.access_token);
      setRefreshToken(payload.refresh_token ?? null);
      storeJson(USER_KEY, payload.user);
      storeValue(ACCESS_TOKEN_KEY, payload.access_token);
      storeValue(REFRESH_TOKEN_KEY, payload.refresh_token ?? null);
    },
    [],
  );

  const clearAuth = useCallback(() => {
    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);
    storeValue(ACCESS_TOKEN_KEY, null);
    storeValue(REFRESH_TOKEN_KEY, null);
    storeJson(USER_KEY, null);
  }, []);

  const bootstrap = useCallback(async () => {
    if (!accessToken) {
      setIsBootstrapping(false);
      return;
    }

    try {
      await apiRequest("/profile", { token: accessToken });
    } catch (error) {
      clearAuth();
    } finally {
      setIsBootstrapping(false);
    }
  }, [accessToken, clearAuth]);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const handleAuthResponse = useCallback(
    (response: AuthResponse) => {
      persistAuth({
        user: response.user,
        access_token: response.access_token,
        refresh_token: response.refresh_token,
      });
    },
    [persistAuth],
  );

  const login = useCallback(
    async (payload: LoginPayload) => {
      const response = await apiRequest<AuthResponse>("/auth/login", {
        method: "POST",
        body: payload,
        auth: false,
      });
      handleAuthResponse(response);
    },
    [handleAuthResponse],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      await apiRequest("/auth/register", {
        method: "POST",
        body: payload,
        auth: false,
      });
      await login({ email: payload.email, password: payload.password });
    },
    [login],
  );

  const loginWithGoogle = useCallback(async () => {
    const response = await apiRequest<{
      authorization_url: string;
      state: string;
    }>("/auth/google/login", { auth: false });
    // Store state for verification in callback
    sessionStorage.setItem("google_oauth_state", response.state);
    // Redirect to Google
    window.location.href = response.authorization_url;
  }, []);

  const logout = useCallback(async () => {
    try {
      if (accessToken) {
        await apiRequest("/auth/logout", {
          method: "POST",
          token: accessToken,
        });
      }
    } catch (error) {
      // Ignore logout errors to prevent locking the UI.
    } finally {
      clearAuth();
    }
  }, [accessToken, clearAuth]);

  const value = useMemo(
    () => ({
      user,
      accessToken,
      isBootstrapping,
      login,
      register,
      loginWithGoogle,
      logout,
      handleAuthResponse,
    }),
    [
      user,
      accessToken,
      isBootstrapping,
      login,
      register,
      loginWithGoogle,
      logout,
      handleAuthResponse,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
};
