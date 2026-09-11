// Central HTTP client: every API call in the app goes through apiRequest().
// Handles attaching the auth token and silently refreshing it on expiry.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Shared in-flight refresh promise: prevents firing multiple parallel
// /auth/refresh calls if several requests get a 401 at the same time.
let refreshRequest = null;

// The access token lives only in this module-level variable, never in
// localStorage/sessionStorage: it's wiped on every reload, which limits what
// an XSS payload could steal. The refresh token (a separate HTTP-only cookie,
// see refreshAccessToken below) is what makes the session survive reloads.
let accessToken = null;

export function getAccessToken() {
  return accessToken;
}

export function setAccessToken(token) {
  if (token) {
    accessToken = token;
  }
}

export function clearAccessToken() {
  accessToken = null;
}

// Registered by AuthContext so this framework-agnostic module can announce a
// dead session without importing React state directly. AuthContext already
// imports apiClient, so importing AuthContext back here would create a
// circular dependency — a plain callback keeps the two decoupled.
let sessionExpiredHandler = null;

export function setSessionExpiredHandler(handler) {
  sessionExpiredHandler = handler;
}

// Clears the access token and tells whoever is listening (AuthContext) that
// the session is definitively over, so React state stays in sync with it.
function notifySessionExpired() {
  clearAccessToken();
  sessionExpiredHandler?.();
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
          // Refresh failed: the session is dead.
          notifySessionExpired();
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
    if (response.status === 401 && shouldRefresh(path)) {
      // Refresh didn't help (or wasn't attempted): the session is dead.
      // Auth endpoints (login/logout/refresh) are excluded so a wrong
      // password on login is never mistaken for an expired session.
      notifySessionExpired();
    }

    const error = new Error(data?.message || data?.error || data?.msg || "API request failed.");
    error.status = response.status;
    throw error;
  }

  return data;
}
