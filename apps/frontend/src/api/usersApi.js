const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function usersHealth() {
  const response = await fetch(`${API_BASE_URL}/users/health`);
  return response.json();
}
