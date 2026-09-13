// API calls for user account management (CRUD), used by UserManagementPage and UserFormPage.
import { apiRequest } from "./apiClient";

// Converts a backend user (snake_case, nested role/service objects) into the flat
// camelCase shape used by the UI.
function mapUserFromBackend(user) {
  if (!user) return user;
  return {
    ...user,
    firstName: user.first_name ?? user.firstName,
    lastName: user.last_name ?? user.lastName,
    role: user.role?.name ?? user.role,
    roleLabel: user.role?.label ?? user.role?.name ?? user.role,
    service: user.service?.label ?? user.service?.name ?? user.service,
    serviceId: user.service?.id ?? user.service_id ?? user.serviceId,
  };
}

// Converts a frontend user object back into the snake_case payload expected by the backend.
function mapUserToBackend(user) {
  if (!user) return user;
  return {
    first_name: user.firstName,
    last_name: user.lastName,
    email: user.email,
    role: user.role,
    service_id: user.serviceId ?? user.service,
  };
}

// The backend rejects any per_page above 100 (see UserService._validate_pagination),
// so fetching "everyone" means walking every page rather than requesting a huge one.
const MAX_PAGE_SIZE = 100;

// Fetches the full list of users (admin only) by walking the backend's
// pagination until every page has been collected. Handles both a plain array
// response and a paginated { items, pagination } response from the backend.
export async function getUsers() {
  let page = 1;
  let totalPages = 1;
  let allUsers = [];

  do {
    const data = await apiRequest(`/users?page=${page}&per_page=${MAX_PAGE_SIZE}`);
    const items = Array.isArray(data) ? data : data.items ?? [];
    allUsers = allUsers.concat(items);
    totalPages = data?.pagination?.total_pages ?? 1;
    page += 1;
  } while (page <= totalPages);

  return allUsers.map(mapUserFromBackend);
}

// Fetches a single user by id, used for the view/edit forms.
export async function getUser(id) {
  const data = await apiRequest(`/users/${id}`);
  return mapUserFromBackend(data);
}

// Creates a new user account (triggers an activation email on the backend).
export async function createUser(userData) {
  const body = mapUserToBackend(userData);
  const data = await apiRequest("/users", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return mapUserFromBackend(data.user);
}

// Updates an existing user's profile/role/service.
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

// Fetches the list of users that can be assigned to a mission (used in MissionFormPage).
export async function getAssignableUsers() {
  const data = await apiRequest("/users/assignable");
  return data.map(mapUserFromBackend);
}

export async function usersHealth() {
  return apiRequest("/users/health");
}
