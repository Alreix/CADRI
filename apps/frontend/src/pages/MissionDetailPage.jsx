import { useState, useEffect, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import Layout from "../components/layout/Layout";
import { AuthContext } from "../contexts/AuthContext";
import { formatDateFR } from "../api/missionsApi";
import "../styles/MissionDetailPage.css";
import "../styles/ConfirmModals.css";
import {
  getMission,
  validateMission,
  updateMissionStatus,
  completeMission,
} from "../api/missionsApi";

function AlertModal({ message, onClose }) {
  return (
    <div className="confirm-modal-overlay" role="dialog" aria-modal="true">
      <div className="confirm-modal">
        <div className="confirm-modal-header">
          <span className="confirm-modal-title">Attention</span>
          <button className="confirm-modal-close" onClick={onClose} aria-label="Fermer">
            <X size={16} />
          </button>
        </div>
        <div className="confirm-modal-body">{message}</div>
        <div className="confirm-modal-footer">
          <button className="confirm-modal-confirm-primary" onClick={onClose}>OK</button>
        </div>
      </div>
    </div>
  );
}

function MissionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);

  const isAgent = user?.role === "agent";
  const isManager = user?.role === "responsable" || user?.role === "admin";

  const [mission, setMission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [savingAction, setSavingAction] = useState(false);
  const [alertMessage, setAlertMessage] = useState(null);

  useEffect(() => {
    getMission(id)
      .then(setMission)
      .finally(() => setLoading(false));
  }, [id]);

  const refreshMission = async () => {
    const updatedMission = await getMission(id);
    setMission(updatedMission);
  };

  const handleStartMission = async () => {
    setSavingAction(true);
    try {
      const updatedMission = await updateMissionStatus(id, "in_progress");
      setMission(updatedMission);
    } catch (err) {
      setAlertMessage(err.message || "Impossible de démarrer la mission.");
    } finally {
      setSavingAction(false);
    }
  };

  const handleCompleteMission = async () => {
    if (!hasActualDuration) {
      setAlertMessage("Veuillez renseigner la durée réelle avant de clôturer la mission.");
      return;
    }

    setSavingAction(true);
    try {
      await completeMission(id);
      await refreshMission();
    } catch (err) {
      setAlertMessage(err.message || "Impossible de terminer la mission.");
    } finally {
      setSavingAction(false);
    }
  };

  const handleValidate = async () => {
    setValidating(true);
    try {
      await validateMission(id);
      await refreshMission();
    } catch (err) {
      setAlertMessage(err.message || "Impossible de valider la mission.");
    } finally {
      setValidating(false);
    }
  };

  if (loading) return null;
  if (!mission) return null;

  const priorityIsUrgent = mission.priority === "high";
  const isAssignedToMission = (mission.assignedUsers || []).some(
    (assignedUserId) => String(assignedUserId) === String(user?.id),
  );
  const canActOnMission = isManager || (isAgent && isAssignedToMission);
  const hasActualDuration =
    mission.actualDuration !== null &&
    mission.actualDuration !== undefined &&
    mission.actualDuration !== "";
  const canStartMission =
    canActOnMission &&
    mission.status === "to_do";
  const canEditMission =
    mission.status !== "completed" &&
    (
      isManager ||
      (
        isAgent &&
        isAssignedToMission &&
        mission.status === "in_progress" &&
        !mission.remark
      )
    );
  const canRequestCompleteMission =
    canActOnMission &&
    mission.status === "in_progress" &&
    !mission.remark;
  const canValidateMission =
    isManager &&
    mission.status === "remark_pending_validation" &&
    mission.remark &&
    hasActualDuration;

  return (
    <>
      {alertMessage && (
        <AlertModal
          message={alertMessage}
          onClose={() => setAlertMessage(null)}
        />
      )}
      <Layout>
        <div className="mission-detail-page">
          <button className="back-link" onClick={() => navigate("/missions")}>
            ← Retour
          </button>

          <div className="mission-detail-card">
            <h1 className="mission-detail-title">{mission.title}</h1>

            <div className="mission-detail-badges">
              {priorityIsUrgent && (
                <span className="mission-badge mission-badge--urgente">Urgente</span>
              )}
              {mission.status && (
                <span
                  className={`mission-badge mission-badge--status${mission.statusLabel === "En cours" ? " mission-badge--in-progress" : ""
                    }`}
                >
                  {mission.statusLabel}
                </span>
              )}
            </div>

            <div className="mission-detail-grid">
              <div className="mission-detail-item">
                <span className="mission-detail-label">Service</span>
                <div className="mission-service-tags">
                  {(mission.services || []).map((service) => (
                    <span key={service.id ?? service.name} className="mission-service-tag">
                      {service.label ?? service.name}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mission-detail-item">
                <span className="mission-detail-label">Type d'intervention</span>
                <span className="mission-detail-value">{mission.interventionType}</span>
              </div>

              <div className="mission-detail-item">
                <span className="mission-detail-label">Localisation</span>
                <span className="mission-detail-value">{mission.location}</span>
              </div>

              <div className="mission-detail-item">
                <span className="mission-detail-label">Signalisation requise</span>
                <span className="mission-detail-value">
                  {mission.signageRequired ? "Oui" : "Non"}
                </span>
              </div>

              <div className="mission-detail-item">
                <span className="mission-detail-label">Date de début</span>
                <span className="mission-detail-value">{formatDateFR(mission.startDate)}</span>
              </div>

              <div className="mission-detail-item">
                <span className="mission-detail-label">Date de fin</span>
                <span className="mission-detail-value">{formatDateFR(mission.endDate)}</span>
              </div>

              <div className="mission-detail-item">
                <span className="mission-detail-label">Durée estimée</span>
                <span className="mission-detail-value">{mission.estimatedDuration} heures</span>
              </div>

              <div className="mission-detail-item mission-detail-item--full">
                <span className="mission-detail-label">Description</span>
                <span className="mission-detail-value">{mission.description}</span>
              </div>

              <div className="mission-detail-item mission-detail-item--full">
                <span className="mission-detail-label">Équipement requis</span>
                <span className="mission-detail-value">{mission.equipment}</span>
              </div>

              {mission.actualDuration && (
                <div className="mission-detail-item">
                  <span className="mission-detail-label">Durée réelle</span>
                  <span className="mission-detail-value">{mission.actualDuration} heures</span>
                </div>
              )}

              {mission.remark && (
                <div className="mission-detail-item mission-detail-item--full">
                  <span className="mission-detail-label">Remarque</span>
                  <span className="mission-detail-value">{mission.remark}</span>
                </div>
              )}
            </div>

            <hr className="mission-detail-divider" />

            <div className="mission-detail-actions">
              {canEditMission && (
                <button
                  className="profile-btn-primary"
                  onClick={() => navigate(`/missions/${id}/edit`)}
                >
                  Modifier
                </button>
              )}

              {canStartMission && (
                <button
                  className="profile-btn-primary"
                  onClick={handleStartMission}
                  disabled={savingAction}
                >
                  {savingAction ? "Démarrage…" : "Démarrer la mission"}
                </button>
              )}

              {canRequestCompleteMission && (
                <button
                  className="mission-btn-validate"
                  onClick={handleCompleteMission}
                  disabled={savingAction}
                >
                  {savingAction ? "Finalisation…" : "Terminer la mission"}
                </button>
              )}

              {canValidateMission && (
                <button
                  className="mission-btn-validate"
                  onClick={handleValidate}
                  disabled={validating}
                >
                  {validating ? "Validation…" : "Valider la mission"}
                </button>
              )}
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}

export default MissionDetailPage;