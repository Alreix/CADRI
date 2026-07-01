// Authentication context: holds the currently logged-in user and exposes
// login/logout actions to the rest of the application via React Context,
// avoiding the need to pass the user manually through every component.
import { createContext, useState, useEffect } from "react";
import {
  apiRequest,
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "../api/apiClient";
import { logout as logoutApi } from "../api/authApi";

// Default shape of the context, used before AuthProvider has mounted.
export const AuthContext = createContext({
  user: null,
  loading: true,
  login: () => { },
  logout: () => { },
});

// Key used to persist the user object in localStorage between page reloads.
const storage_key = "cadri_user";

// Backend may return role/service as nested objects ({ name: "admin" })
// or as plain strings depending on the endpoint; this flattens both cases
// into a single consistent shape for the rest of the frontend.
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
    // Guards against setting state after the component has unmounted
    // (e.g. if the user navigates away while the /me request is still in flight).
    let isMounted = true;

    // On app startup, try to restore a previous session from localStorage,
    // then re-validate it against the backend before fully trusting it.
    async function restoreSession() {
      const stored = localStorage.getItem(storage_key);
      const token = getAccessToken();
      let storedUser = null;

      if (stored) {
        try {
          storedUser = normalizeUser(JSON.parse(stored));
        } catch {
          // Corrupted localStorage entry: discard it and start fresh.
          localStorage.removeItem(storage_key);
        }
      }

      if (storedUser && token) {
        // Optimistic UI: show the cached user immediately so the app doesn't
        // flash a logged-out state while we confirm the session is still valid.
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
          // Session is no longer valid on the server: clear everything locally.
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

      // No cached user and no token: nothing to restore, app starts logged out.
      if (!storedUser && !token) {
        if (isMounted) {
          setLoading(false);
        }
        return;
      }

      // Edge case: only one of (cached user / token) is present.
      // Still attempt to fetch the profile in case the session is actually valid.
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

  // Called after a successful login request: stores the user and access token.
  const login = ({ user: userData, accessToken }) => {
    const normalizedUser = normalizeUser(userData);

    setUser(normalizedUser);
    localStorage.setItem(storage_key, JSON.stringify(normalizedUser));

    if (accessToken) {
      setAccessToken(accessToken);
    }
  };

  // Revokes the refresh token on the server, then always clears local state,
  // even if the server call fails (e.g. token already expired).
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
