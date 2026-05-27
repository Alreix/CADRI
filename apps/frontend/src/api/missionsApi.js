const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function missionsHealth() {
  const response = await fetch(`${API_BASE_URL}/missions/health`);
  return response.json();
}
