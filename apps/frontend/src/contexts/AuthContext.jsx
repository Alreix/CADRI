import { createContext, useState, useEffect } from "react";
import { ACCESS_TOKEN_STORAGE_KEY } from "../api/apiClient";
import { logout as logoutApi } from "../api/authApi";

export const AuthContext = createContext({
  user: null,
  loading: true,
  login: () => {},
  logout: () => {},
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
    const stored = localStorage.getItem(storage_key);
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem(storage_key);
      }
    }
    setLoading(false);
  }, []);

  const login = ({ user: userData, accessToken }) => {
    const normalizedUser = normalizeUser(userData);

    setUser(normalizedUser);
    localStorage.setItem(storage_key, JSON.stringify(normalizedUser));

    if (accessToken) {
      localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken);
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
    localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthProvider;
