import { createContext, useState, useEffect } from "react";
import {
  apiRequest,
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "../api/apiClient";
import { logout as logoutApi } from "../api/authApi";

export const AuthContext = createContext({
  user: null,
  loading: true,
  login: () => { },
  logout: () => { },
});

const storage_key = "cadri_user";

function normalizeUser(user) {
  if (!user) return null;

  return {
    ...user,
    role: user.role?.name ?? user.role,
    service: user.service?.label ?? user.service?.name ?? user.service,
  };
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      const stored = localStorage.getItem(storage_key);
      const token = getAccessToken();
      let storedUser = null;

      if (stored) {
        try {
          storedUser = normalizeUser(JSON.parse(stored));
        } catch {
          localStorage.removeItem(storage_key);
        }
      }

      if (storedUser && token) {
        if (isMounted) {
          setUser(storedUser);
          setLoading(false);
        }

        try {
          const profile = await apiRequest("/me");
          const normalizedUser = normalizeUser(profile);

          if (isMounted) {
            setUser(normalizedUser);
            localStorage.setItem(storage_key, JSON.stringify(normalizedUser));
          }
        } catch {
          if (isMounted) {
            setUser(null);
          }
          localStorage.removeItem(storage_key);
          clearAccessToken();
        } finally {
          if (isMounted) {
            setLoading(false);
          }
        }

        apiRequest("/me")
          .then((profile) => {
            if (isMounted) {
              setUser(normalizeUser(profile));
              localStorage.setItem(storage_key, JSON.stringify(normalizeUser(profile)));
            }
          })
          .catch(() => {
            if (isMounted) setUser(null);
            localStorage.removeItem(storage_key);
            clearAccessToken();
          });

        return;
      }

      if (!storedUser && !token) {
        if (isMounted) {
          setLoading(false);
        }
        return;
      }

      try {
        const profile = await apiRequest("/me");
        const normalizedUser = normalizeUser(profile);

        if (isMounted) {
          setUser(normalizedUser);
          localStorage.setItem(storage_key, JSON.stringify(normalizedUser));
        }
      } catch {
        if (isMounted) {
          setUser(null);
        }
        localStorage.removeItem(storage_key);
        clearAccessToken();
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    restoreSession();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = ({ user: userData, accessToken }) => {
    const normalizedUser = normalizeUser(userData);

    setUser(normalizedUser);
    localStorage.setItem(storage_key, JSON.stringify(normalizedUser));

    if (accessToken) {
      setAccessToken(accessToken);
    }
  };

  const logout = async () => {
    try {
      await logoutApi();
    } catch {
      // Local cleanup must still happen if the refresh cookie is already invalid.
    }

    setUser(null);
    localStorage.removeItem(storage_key);
    clearAccessToken();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthProvider;
