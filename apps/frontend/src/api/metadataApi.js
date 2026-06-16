const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function metadataHealth() {
  const response = await fetch(`${API_BASE_URL}/metadata/health`);
  return response.json();
}

export async function getRoles() {
  const response = await fetch(`${API_BASE_URL}/metadata/roles`);
  return response.json();
}

export async function getServices() {
  const response = await fetch(`${API_BASE_URL}/metadata/services`);
  return response.json();
}

export async function getPriorities() {
  const response = await fetch(`${API_BASE_URL}/metadata/priorities`);
  return response.json();
}

export async function getStatuses() {
  const response = await fetch(`${API_BASE_URL}/metadata/statuses`);
  return response.json();
}
