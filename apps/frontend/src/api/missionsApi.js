const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function mapMissionFromBackend(mission) {
  if (!mission) return mission;
  return {
    ...mission,
    title: mission.titre ?? mission.title,
  };
}

export async function getMissions() {
  const response = await fetch(`${API_BASE_URL}/missions`);
  if (!response.ok) {
    throw new Error("Impossible de récupérer la liste des missions.");
  }
  const data = await response.json();
  if (Array.isArray(data)) return data.map(mapMissionFromBackend);
  return mapMissionFromBackend(data);
}

export async function getMission(id) {
  const response = await fetch(`${API_BASE_URL}/missions/${id}`);
  if (!response.ok) {
    throw new Error("Impossible de récupérer la mission.");
  }
  const data = await response.json();
  return mapMissionFromBackend(data);
}

export async function validateMission(id) {
  const response = await fetch(`${API_BASE_URL}/missions/${id}/validate`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Impossible de valider la mission.");
  }
  return response.json();
}

export async function missionsHealth() {
  const response = await fetch(`${API_BASE_URL}/missions/health`);
  return response.json();
}

export async function createMission(missionData) {
  const response = await fetch(`${API_BASE_URL}/missions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(missionData),
  });
  if (!response.ok) {
    throw new Error("Impossible de créer la mission.");
  }
  const data = await response.json();
  return mapMissionFromBackend(data);
}

export async function updateMission(id, missionData) {
  const response = await fetch(`${API_BASE_URL}/missions/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(missionData),
  });
  if (!response.ok) {
    throw new Error("Impossible de mettre à jour la mission.");
  }
  const data = await response.json();
  return mapMissionFromBackend(data);
}

export async function deleteMission(id) {
  const response = await fetch(`${API_BASE_URL}/missions/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Impossible de supprimer la mission.");
  }
  return response.json();
}
