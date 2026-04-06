import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useAuth } from "./AuthContext";
import {
  getProfile,
  getUserSettings,
  getServiceCatalog,
  getResourceCatalog,
} from "@/lib/api";
import type { Profile } from "@/types/profile";
import type {
  UserSettings,
  ServiceCatalog,
  ResourceCatalog,
} from "@/types/settings";

const PROFILE_KEY = "user_profile";
const SETTINGS_KEY = "user_settings";
const SERVICES_KEY = "service_catalog";
const RESOURCES_KEY = "resource_catalog";

interface UserDataContextValue {
  profile: Profile | null;
  settings: UserSettings | null;
  services: ServiceCatalog[] | null;
  resources: ResourceCatalog[] | null;
  isLoading: boolean;
  refreshProfile: () => Promise<void>;
  refreshSettings: () => Promise<void>;
  refreshServices: () => Promise<void>;
  refreshResources: () => Promise<void>;
  updateProfileCache: (profile: Profile) => void;
  updateSettingsCache: (settings: UserSettings) => void;
  clearUserData: () => void;
}

const UserDataContext = createContext<UserDataContextValue | undefined>(
  undefined,
);

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

export const UserDataProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const { accessToken, user } = useAuth();

  const [profile, setProfile] = useState<Profile | null>(() =>
    readStoredJson<Profile>(PROFILE_KEY),
  );
  const [settings, setSettings] = useState<UserSettings | null>(() =>
    readStoredJson<UserSettings>(SETTINGS_KEY),
  );
  const [services, setServices] = useState<ServiceCatalog[] | null>(() =>
    readStoredJson<ServiceCatalog[]>(SERVICES_KEY),
  );
  const [resources, setResources] = useState<ResourceCatalog[] | null>(() =>
    readStoredJson<ResourceCatalog[]>(RESOURCES_KEY),
  );
  const [isLoading, setIsLoading] = useState(false);

  // Clear user data when user logs out
  const clearUserData = useCallback(() => {
    setProfile(null);
    setSettings(null);
    setServices(null);
    setResources(null);
    storeJson(PROFILE_KEY, null);
    storeJson(SETTINGS_KEY, null);
    storeJson(SERVICES_KEY, null);
    storeJson(RESOURCES_KEY, null);
  }, []);

  // Update profile cache
  const updateProfileCache = useCallback((newProfile: Profile) => {
    setProfile(newProfile);
    storeJson(PROFILE_KEY, newProfile);
  }, []);

  // Update settings cache
  const updateSettingsCache = useCallback((newSettings: UserSettings) => {
    setSettings(newSettings);
    storeJson(SETTINGS_KEY, newSettings);
  }, []);

  // Refresh profile from server
  const refreshProfile = useCallback(async () => {
    if (!accessToken) return;

    try {
      const data = await getProfile(accessToken);
      if (data) {
        setProfile(data);
        storeJson(PROFILE_KEY, data);
      }
    } catch (error) {
      console.error("Failed to fetch profile:", error);
    }
  }, [accessToken]);

  // Refresh settings from server
  const refreshSettings = useCallback(async () => {
    if (!accessToken) return;

    try {
      const data = await getUserSettings(accessToken);
      setSettings(data);
      storeJson(SETTINGS_KEY, data);
    } catch (error) {
      console.error("Failed to fetch settings:", error);
    }
  }, [accessToken]);

  // Refresh services from server
  const refreshServices = useCallback(async () => {
    if (!accessToken) return;

    try {
      const data = await getServiceCatalog(accessToken);
      setServices(data);
      storeJson(SERVICES_KEY, data);
    } catch (error) {
      console.error("Failed to fetch services:", error);
      // Set to empty array on error to prevent infinite retries
      setServices([]);
      storeJson(SERVICES_KEY, []);
    }
  }, [accessToken]);

  // Refresh resources from server
  const refreshResources = useCallback(async () => {
    if (!accessToken) return;

    try {
      const data = await getResourceCatalog(accessToken);
      setResources(data);
      storeJson(RESOURCES_KEY, data);
    } catch (error) {
      console.error("Failed to fetch resources:", error);
      // Set to empty array on error to prevent infinite retries
      setResources([]);
      storeJson(RESOURCES_KEY, []);
    }
  }, [accessToken]);

  // Fetch data on mount or when user logs in
  useEffect(() => {
    if (!accessToken || !user) {
      clearUserData();
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch all data in parallel for better performance
        const promises = [];

        if (!profile) {
          promises.push(refreshProfile());
        }
        if (!settings) {
          promises.push(refreshSettings());
        }
        if (!services) {
          promises.push(refreshServices());
        }
        if (!resources) {
          promises.push(refreshResources());
        }

        // Wait for all fetches to complete (or fail)
        await Promise.allSettled(promises);
      } catch (error) {
        console.error("Error fetching user data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [accessToken, user]); // eslint-disable-line react-hooks/exhaustive-deps

  const value = useMemo(
    () => ({
      profile,
      settings,
      services,
      resources,
      isLoading,
      refreshProfile,
      refreshSettings,
      refreshServices,
      refreshResources,
      updateProfileCache,
      updateSettingsCache,
      clearUserData,
    }),
    [
      profile,
      settings,
      services,
      resources,
      isLoading,
      refreshProfile,
      refreshSettings,
      refreshServices,
      refreshResources,
      updateProfileCache,
      updateSettingsCache,
      clearUserData,
    ],
  );

  return (
    <UserDataContext.Provider value={value}>
      {children}
    </UserDataContext.Provider>
  );
};

export const useUserData = () => {
  const context = useContext(UserDataContext);
  if (context === undefined) {
    throw new Error("useUserData must be used within a UserDataProvider");
  }
  return context;
};
