// API calls for reference/lookup data (dropdown options) used across forms and filters:
// roles, services, mission priorities and statuses.
import { apiRequest } from "./apiClient";

// Normalizes a single backend option into a consistent { id, value, label, name } shape,
// so dropdowns can rely on the same fields regardless of which list they render.
function mapOption(option) {
  if (!option || typeof option !== "object") return option;
  return {
    id: option.id,
    value: option.name,
    label: option.label ?? option.name,
    name: option.name,
  };
}

function mapOptions(data) {
  return Array.isArray(data) ? data.map(mapOption) : [];
}

export async function metadataHealth() {
  return apiRequest("/metadata/health");
}
// List of available user roles (admin, responsable, agent).
export async function getRoles() {
  const data = await apiRequest("/metadata/roles");
  return mapOptions(data);
}

// List of municipal services/departments.
export async function getServices() {
  const data = await apiRequest("/metadata/services");
  return mapOptions(data);
}

// List of mission priority levels.
export async function getPriorities() {
  const data = await apiRequest("/metadata/priorities");
  return mapOptions(data);
}

// List of possible mission statuses (to_do, in_progress, etc.).
export async function getStatuses() {
  const data = await apiRequest("/metadata/statuses");
  return mapOptions(data);
}
