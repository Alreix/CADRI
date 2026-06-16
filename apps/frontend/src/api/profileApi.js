const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function mapProfileFromBackend(profile) {
  if (!profile) return profile;
  return {
    ...profile,
    firstName: profile.prenom ?? profile.firstName,
    lastName: profile.nom ?? profile.lastName,
  };
}

function mapProfileToBackend(profile) {
  if (!profile) return profile;
  return {
    ...profile,
    prenom: profile.firstName ?? profile.prenom,
    nom: profile.lastName ?? profile.nom,
  };
}

export async function getProfile() {
  const response = await fetch(`${API_BASE_URL}/profile`);
  if (!response.ok) {
    throw new Error("Impossible de récupérer le profil utilisateur.");
  }
  const data = await response.json();
  return mapProfileFromBackend(data);
}

export async function updateProfile(profileData) {
  const body = mapProfileToBackend(profileData);
  const response = await fetch(`${API_BASE_URL}/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error("Impossible de mettre à jour le profil utilisateur.");
  }

  const data = await response.json();
  return mapProfileFromBackend(data);
}
