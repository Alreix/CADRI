import { apiRequest } from "./apiClient";

function mapProfileFromBackend(profile) {
  if (!profile) return profile;
  return {
    ...profile,
    firstName: profile.first_name ?? profile.firstName,
    lastName: profile.last_name ?? profile.lastName,
    role: profile.role?.label ?? profile.role?.name ?? profile.role,
    service: profile.service?.label ?? profile.service?.name ?? profile.service,
  };
}

function mapProfileToBackend(profile) {
  if (!profile) return profile;
  return {
    first_name: profile.firstName,
    last_name: profile.lastName,
    email: profile.email,
  };
}

export async function getProfile() {
  const data = await apiRequest("/me");
  return mapProfileFromBackend(data);
}

export async function updateProfile(profileData) {
  const body = mapProfileToBackend(profileData);
  const data = await apiRequest("/me", {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  return mapProfileFromBackend(data.user);
}
