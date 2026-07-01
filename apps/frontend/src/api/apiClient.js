// Central HTTP client: every API call in the app goes through apiRequest().
// Handles attaching the auth token and silently refreshing it on expiry.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const ACCESS_TOKEN_STORAGE_KEY = "cadri_access_token";

// Shared in-flight refresh promise: prevents firing multiple parallel
// /auth/refresh calls if several requests get a 401 at the same time.
let refreshRequest = null;

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
}

export function setAccessToken(token) {
  if (token) {
    localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
  }
}

export function clearAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
}

// Merges default headers (JSON content type, Bearer token) with any custom headers.
function buildHeaders(headers = {}) {
  const token = getAccessToken();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...headers,
  };
}

// Some responses may not have a JSON body (e.g. 204 No Content); fail gracefully to null.
async function parseResponse(response) {
  return response.json().catch(() => null);
}

// Auth endpoints themselves must never trigger a refresh attempt,
// otherwise a failed login could loop into a refresh call.
function shouldRefresh(path) {
  return !["/auth/login", "/auth/logout", "/auth/refresh"].includes(path);
}

// Calls /auth/refresh using the HTTP-only refresh cookie to get a new access token.
// Reuses an in-flight request if one is already running (see refreshRequest above).
async function refreshAccessToken() {
  if (!refreshRequest) {
    refreshRequest = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include", // sends the HTTP-only refresh token cookie
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(async (response) => {
        const data = await parseResponse(response);

        if (!response.ok || !data?.access_token) {
          // Refresh failed: the session is dead, clear everything locally.
          localStorage.removeItem("cadri_user");
          clearAccessToken();
          return null;
        }

        setAccessToken(data.access_token);
        return data.access_token;
      })
      .finally(() => {
        refreshRequest = null;
      });
  }

  return refreshRequest;
}

// Generic request helper used by every api/*.js module.
// On a 401, it transparently refreshes the access token and retries once
// (retryOnUnauthorized guards against infinite retry loops).
export async function apiRequest(path, options = {}, retryOnUnauthorized = true) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    ...options,
    headers: buildHeaders(options.headers),
  });

  const data = await parseResponse(response);

  if (
    response.status === 401 &&
    retryOnUnauthorized &&
    shouldRefresh(path)
  ) {
    const refreshedToken = await refreshAccessToken();

    if (refreshedToken) {
      // Retry the original request once with the fresh token; retryOnUnauthorized=false
      // prevents a second refresh attempt if it fails again.
      return apiRequest(path, options, false);
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      // Refresh didn't help (or wasn't attempted): force logout locally.
      localStorage.removeItem("cadri_user");
      clearAccessToken();
    }

      const error = new Error(data?.message || data?.error || "API request failed.");
      error.status = response.status;
      throw error;
    }

    return data;
  }
