const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function metadataHealth() {
  const response = await fetch(`${API_BASE_URL}/metadata/health`);
  return response.json();
}
