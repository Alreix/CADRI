import { apiRequest } from "./apiClient";

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

export async function getRoles() {
  const data = await apiRequest("/metadata/roles");
  return mapOptions(data);
}

export async function getServices() {
  const data = await apiRequest("/metadata/services");
  return mapOptions(data);
}

export async function getPriorities() {
  const data = await apiRequest("/metadata/priorities");
  return mapOptions(data);
}

export async function getStatuses() {
  const data = await apiRequest("/metadata/statuses");
  return mapOptions(data);
}
