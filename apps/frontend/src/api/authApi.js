// Authentication-related API calls: login, logout, password reset/activation flows.
import { apiRequest } from "./apiClient";

// Used to check whether the backend is reachable (e.g. on app boot or for diagnostics).
export async function authHealth() {
  return apiRequest("/auth/health");
}

// Logs in with email/password and returns the access token + user profile,
// already mapped from the backend's snake_case response to camelCase.
export async function login({ email, password }) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  return {
    accessToken: data.access_token,
    user: data.user,
  };
}

// Triggers the "forgot password" email containing a reset link/token.
export async function requestPasswordReset({ email }) {
  return apiRequest("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

// Consumes a reset token (received by email) to set a new password.
export async function resetPassword({ token, password }) {
  return apiRequest("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}

// Consumes an activation token to set the initial password of a newly created account.
export async function activateAccount({ token, password }) {
  return apiRequest("/auth/activate-account", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}

// Lets a logged-in user change their own password (requires the current one).
export async function changePassword({ currentPassword, newPassword }) {
  return apiRequest("/auth/change-password", {
    method: "PATCH",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

// Revokes the refresh token on the server side; local cleanup happens in AuthContext.
export async function logout() {
  return apiRequest("/auth/logout", { method: "POST" });
}
