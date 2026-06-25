import { apiRequest } from "./apiClient";

function mapUserFromBackend(u) {
  if (!u) return u;
  return {
    ...u,
    firstName: u.first_name ?? u.firstName,
    lastName: u.last_name ?? u.lastName,
    role: u.role?.name ?? u.role,
    roleLabel: u.role?.label ?? u.role?.name ?? u.role,
    service: u.service?.label ?? u.service?.name ?? u.service,
    serviceId: u.service?.id ?? u.service_id ?? u.serviceId,
  };
}

function mapUserToBackend(u) {
  if (!u) return u;
  return {
    first_name: u.firstName,
    last_name: u.lastName,
    email: u.email,
    role: u.role,
    service_id: u.serviceId ?? u.service,
  };
}

export async function getUsers() {
  const data = await apiRequest("/users");
  const users = Array.isArray(data) ? data : data.items ?? [];
  return users.map(mapUserFromBackend);
}

export async function getUser(id) {
  const data = await apiRequest(`/users/${id}`);
  return mapUserFromBackend(data);
}

export async function createUser(userData) {
  const body = mapUserToBackend(userData);
  const data = await apiRequest("/users", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return mapUserFromBackend(data.user);
}

export async function updateUser(id, userData) {
  const body = mapUserToBackend(userData);
  const data = await apiRequest(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  return mapUserFromBackend(data.user);
}

export async function deleteUser(id) {
  return apiRequest(`/users/${id}`, {
    method: "DELETE",
  });
}

export async function getAssignableUsers() {
  const data = await apiRequest("/users/assignable");
  return data.map(mapUserFromBackend);
}

export async function usersHealth() {
  return apiRequest("/users/health");
}
