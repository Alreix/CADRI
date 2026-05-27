const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function authHealth() {
  const response = await fetch(`${API_BASE_URL}/auth/health`);
  return response.json();
}
