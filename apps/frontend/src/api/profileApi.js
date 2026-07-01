// API calls for the currently logged-in user's own profile (the "/me" endpoint).
import { apiRequest } from "./apiClient";

// Converts the backend's snake_case profile fields into the camelCase shape used in the UI.
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

// Converts a frontend profile object back into the snake_case payload the backend expects.
function mapProfileToBackend(profile) {
  if (!profile) return profile;
  return {
    first_name: profile.firstName,
    last_name: profile.lastName,
    email: profile.email,
  };
}

// Fetches the current user's profile.
export async function getProfile() {
  const data = await apiRequest("/me");
  return mapProfileFromBackend(data);
}

// Updates the current user's profile (name, email) and returns the refreshed profile.
export async function updateProfile(profileData) {
  const body = mapProfileToBackend(profileData);
  const data = await apiRequest("/me", {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  return mapProfileFromBackend(data.user);
}
