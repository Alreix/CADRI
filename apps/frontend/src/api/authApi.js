const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function authHealth() {
  const response = await fetch(`${API_BASE_URL}/auth/health`);
  return response.json();
}

export async function login({ email, password }) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) throw new Error('Identifiants invalides');
  return response.json();
}

export async function requestPasswordReset({ email }) {
  const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  if (!response.ok) throw new Error('Une erreur s\'est produite');
  return response.json();
}

export async function resetPassword({ token, email, password }) {
  const response = await fetch(`${API_BASE_URL}/auth/reset-password/${token}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) throw new Error('Une erreur s\'est produite');
  return response.json();
}

export async function activateAccount({ token, email, password }) {
  const response = await fetch(`${API_BASE_URL}/auth/activate/${token}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) throw new Error('Une erreur s\'est produite');
  return response.json();
}

export async function getActivationInfo(token) {
  const response = await fetch(`${API_BASE_URL}/auth/activate/${token}`, {
    method: 'GET'
  });
  if (!response.ok) throw new Error('Lien d\'activation invalide ou expiré');
  return response.json();
}
