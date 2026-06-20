import { apiRequest } from "./apiClient";

export async function authHealth() {
  return apiRequest("/auth/health");
}

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

export async function requestPasswordReset({ email }) {
  return apiRequest("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword({ token, password }) {
  return apiRequest("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}

export async function activateAccount({ token, password }) {
  return apiRequest("/auth/activate-account", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}

export async function changePassword({ currentPassword, newPassword }) {
  return apiRequest("/auth/change-password", {
    method: "PATCH",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

export async function logout() {
  return apiRequest("/auth/logout", { method: "POST" });
}
