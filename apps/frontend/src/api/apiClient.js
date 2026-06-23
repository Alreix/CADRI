const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const ACCESS_TOKEN_STORAGE_KEY = "cadri_access_token";

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

function buildHeaders(headers = {}) {
  const token = getAccessToken();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...headers,
  };
}

async function parseResponse(response) {
  return response.json().catch(() => null);
}

function shouldRefresh(path) {
  return !["/auth/login", "/auth/logout", "/auth/refresh"].includes(path);
}

async function refreshAccessToken() {
  if (!refreshRequest) {
    refreshRequest = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(async (response) => {
        const data = await parseResponse(response);

        if (!response.ok || !data?.access_token) {
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
      return apiRequest(path, options, false);
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("cadri_user");
      clearAccessToken();
    }

      const error = new Error(data?.message || data?.error || "API request failed.");
      error.status = response.status;
      throw error;
    }

    return data;
  }
