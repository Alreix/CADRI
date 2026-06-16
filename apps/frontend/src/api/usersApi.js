const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function mapUserFromBackend(u) {
  if (!u) return u;
  return {
    ...u,
    firstName: u.prenom ?? u.firstName,
    lastName: u.nom ?? u.lastName,
  };
}

function mapUserToBackend(u) {
  if (!u) return u;
  return {
    ...u,
    prenom: u.firstName ?? u.prenom,
    nom: u.lastName ?? u.nom,
  };
}

export async function getUsers() {
  const response = await fetch(`${API_BASE_URL}/users`);
  if (!response.ok) {
    throw new Error("Impossible de récupérer la liste des utilisateurs.");
  }
  const data = await response.json();
  if (Array.isArray(data)) return data.map(mapUserFromBackend);
  return mapUserFromBackend(data);
}

export async function getUser(id) {
  const response = await fetch(`${API_BASE_URL}/users/${id}`);
  if (!response.ok) {
    throw new Error("Impossible de récupérer l'utilisateur.");
  }
  const data = await response.json();
  return mapUserFromBackend(data);
}

export async function createUser(userData) {
  const body = mapUserToBackend(userData);
  const response = await fetch(`${API_BASE_URL}/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Impossible de créer l'utilisateur.");
  }
  const data = await response.json();
  return mapUserFromBackend(data);
}

export async function updateUser(id, userData) {
  const body = mapUserToBackend(userData);
  const response = await fetch(`${API_BASE_URL}/users/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Impossible de mettre à jour l'utilisateur.");
  }
  const data = await response.json();
  return mapUserFromBackend(data);
}

export async function deleteUser(id) {
  const response = await fetch(`${API_BASE_URL}/users/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Impossible de supprimer l'utilisateur.");
  }
  const data = await response.json();
  return mapUserFromBackend(data);
}

export async function usersHealth() {
  const response = await fetch(`${API_BASE_URL}/users/health`);
  return response.json();
}
