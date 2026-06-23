import { apiRequest } from "./apiClient";

const priorityLabels = {
  low: "Basse",
  medium: "Moyenne",
  high: "Urgente",
};

const statusLabels = {
  to_do: "À faire",
  in_progress: "En cours",
  remark_pending_validation: "En attente de validation",
  completed: "Terminée",
};

function toDateInputValue(value) {
  if (!value) return "";
  return value.slice(0, 10);
}

export function formatDateFR(value) {
  if (!value) return "";
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${day}/${month}/${year}`;
}

function mapMissionFromBackend(mission) {
  if (!mission) return mission;

  const services = mission.services ?? [];
  const assignments = mission.assignments ?? [];

  return {
    ...mission,
    interventionType: mission.intervention_type ?? mission.interventionType,
    typeIntervention: mission.intervention_type ?? mission.typeIntervention,
    plannedAgentsCount: mission.planned_agents_count ?? mission.plannedAgentsCount,
    estimatedDuration: mission.estimated_duration ?? mission.estimatedDuration,
    actualDuration: mission.actual_duration ?? mission.actualDuration,
    startDate: toDateInputValue(mission.start_date ?? mission.startDate),
    endDate: toDateInputValue(mission.end_date ?? mission.endDate),
    priorityLabel: priorityLabels[mission.priority] ?? mission.priority,
    statusLabel: statusLabels[mission.status] ?? mission.status,
    equipment: mission.required_equipment ?? mission.equipment,
    signageRequired: mission.signage_required ?? mission.signageRequired,
    services,
    service: services.map((service) => service.label ?? service.name).join(", "),
    serviceIds: services.map((service) => service.id),
    assignments,
    assignedUsers: assignments.map((user) => user.id),
    requiresValidation: mission.status === "remark_pending_validation",
  };
}

function mapMissionToBackend(mission) {
  const assignedUserIds = mission.assignedUsers ?? mission.assigned_user_ids ?? [];
  const serviceIds = mission.serviceIds ?? (
    mission.service ? [mission.service] : []
  );

  return {
    title: mission.title,
    intervention_type: mission.interventionType,
    location: mission.location,
    description: mission.description,
    planned_agents_count: Number(mission.plannedAgentsCount || assignedUserIds.length || 1),
    estimated_duration: Number(mission.estimatedDuration),
    start_date: mission.startDate,
    end_date: mission.endDate,
    priority: mission.priority,
    required_equipment: mission.equipment,
    signage_required: Boolean(mission.signageRequired),
    service_ids: serviceIds,
    assigned_user_ids: assignedUserIds,
  };
}

export async function updateMissionStatus(id, status) {
  const data = await apiRequest(`/missions/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

  return mapMissionFromBackend(data.mission);
}

export async function updateMissionActualDuration(id, actualDuration) {
  const data = await apiRequest(`/missions/${id}/actual-duration`, {
    method: "PATCH",
    body: JSON.stringify({
      actual_duration: Number(actualDuration),
    }),
  });

  return mapMissionFromBackend(data.mission);
}

export async function addMissionRemark(id, remark) {
  const data = await apiRequest(`/missions/${id}/remark`, {
    method: "POST",
    body: JSON.stringify({ remark }),
  });

  return mapMissionFromBackend(data.mission);
}

export async function completeMission(id) {
  const data = await apiRequest(`/missions/${id}/complete`, {
    method: "POST",
  });

  return {
    ...data,
    status: "completed",
    statusLabel: "Terminée",
  };
}

export async function getMissions() {
  const data = await apiRequest("/missions");
  const missions = Array.isArray(data) ? data : data.items ?? [];
  return missions.map(mapMissionFromBackend);
}

export async function getMission(id) {
  const data = await apiRequest(`/missions/${id}`);
  return mapMissionFromBackend(data);
}

export async function validateMission(id) {
  const data = await apiRequest(`/missions/${id}/validate`, {
    method: "POST",
  });
  return mapMissionFromBackend(data.mission);
}

export async function missionsHealth() {
  return apiRequest("/missions/health");
}

export async function createMission(missionData) {
  const data = await apiRequest("/missions", {
    method: "POST",
    body: JSON.stringify(mapMissionToBackend(missionData)),
  });
  return mapMissionFromBackend(data.mission);
}

export async function updateMission(id, missionData) {
  const data = await apiRequest(`/missions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(mapMissionToBackend(missionData)),
  });
  return mapMissionFromBackend(data.mission);
}

export async function deleteMission(id) {
  return apiRequest(`/missions/${id}`, {
    method: "DELETE",
  });
}
