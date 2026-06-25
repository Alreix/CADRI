import { useState, useEffect, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Trash2, X, UserPlus } from "lucide-react";
import Layout from "../components/layout/Layout";
import { AuthContext } from "../contexts/AuthContext";
import { getServices } from "../api/metadataApi";
import {
  getMission,
  createMission,
  updateMission,
  deleteMission,
  updateMissionActualDuration,
  addMissionRemark,
} from "../api/missionsApi";
import { getAssignableUsers } from "../api/usersApi";
import "../styles/MissionFormPage.css";
import "../styles/ConfirmModals.css";

const priorityOptions = [
  { value: "low", label: "Basse" },
  { value: "medium", label: "Moyenne" },
  { value: "high", label: "Urgente" },
];

const emptyForm = {
  title: "",
  description: "",
  serviceIds: [],
  startDate: "",
  endDate: "",
  estimatedDuration: "",
  interventionType: "",
  location: "",
  equipment: "",
  signageRequired: false,
  priority: "",
  status: "",
  actualDuration: "",
  remark: "",
  assignedUsers: [],
};

function DeleteConfirmModal({ onConfirm, onCancel }) {
  return (
    <div className="confirm-modal-overlay" role="dialog" aria-modal="true">
      <div className="confirm-modal">
        <div className="confirm-modal-header">
          <span className="confirm-modal-title">Supprimer la mission</span>
          <button className="confirm-modal-close" onClick={onCancel} aria-label="Fermer">
            <X size={16} />
          </button>
        </div>
        <div className="confirm-modal-body">
          Êtes-vous sûr de vouloir supprimer cette mission ? Cette action ne peut pas être annulée.
        </div>
        <div className="confirm-modal-footer">
          <button className="confirm-modal-cancel" onClick={onCancel}>Non, conserver</button>
          <button className="confirm-modal-confirm-danger" onClick={onConfirm}>Oui, supprimer</button>
        </div>
      </div>
    </div>
  );
}

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

function MissionFormPage({ mode = "create" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useContext(AuthContext);

  const isAgent = currentUser?.role === "agent";
  const isManager = currentUser?.role === "responsable" || currentUser?.role === "admin";
  const isEdit = mode === "edit";

  const [form, setForm] = useState(emptyForm);
  const [initialForm, setInitialForm] = useState(emptyForm);
  const [loadedMission, setLoadedMission] = useState(null);
  const [serviceOptions, setServiceOptions] = useState([]);
  const [assignableUsers, setAssignableUsers] = useState([]);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showAddUsers, setShowAddUsers] = useState(false);
  const [alertMessage, setAlertMessage] = useState(null);

  const titles = {
    create: "Créer une mission",
    edit: "Modifier la mission",
  };
  useEffect(() => {
    const requests = [
      getServices().then(setServiceOptions).catch(() => { }),
    ];

    if (isManager) {
      requests.push(
        getAssignableUsers()
          .then(setAssignableUsers)
          .catch(() => { })
      );
    }

    Promise.all(requests).then(() => {
      if (isEdit && id) {
        getMission(id)
          .then((mission) => {
            setLoadedMission(mission);
            const loadedForm = {
              title: mission.title || "",
              description: mission.description || "",
              serviceIds: mission.serviceIds || [],
              startDate: mission.startDate || "",
              endDate: mission.endDate || "",
              estimatedDuration: mission.estimatedDuration ?? "",
              interventionType: mission.interventionType || "",
              location: mission.location || "",
              equipment: mission.equipment || "",
              signageRequired: mission.signageRequired || false,
              priority: mission.priority || "",
              status: mission.status || "",
              actualDuration: mission.actualDuration ?? "",
              remark: mission.remark || "",
              assignedUsers: mission.assignedUsers || [],
            };
            setForm(loadedForm);
            setInitialForm(loadedForm);
          })
          .catch((err) => console.error("Failed to load mission:", err))
          .finally(() => setLoading(false));
      }
    });
  }, [id, isEdit, isManager]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((prevForm) => ({
      ...prevForm,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleServiceToggle = (serviceId) => {
    setForm((prevForm) => ({
      ...prevForm,
      serviceIds: prevForm.serviceIds.includes(serviceId)
        ? prevForm.serviceIds.filter((value) => value !== serviceId)
        : [...prevForm.serviceIds, serviceId],
    }));
  };

  const handleUserToggle = (userId) => {
    setForm((prevForm) => ({
      ...prevForm,
      assignedUsers: prevForm.assignedUsers.includes(userId)
        ? prevForm.assignedUsers.filter((value) => value !== userId)
        : [...prevForm.assignedUsers, userId],
    }));
  };

  const handleSave = async (event) => {
    event.preventDefault();

    if (isAgentEdit && !canAgentUpdateTracking) {
      setAlertMessage("Vous ne pouvez pas modifier cette mission.");
      return;
    }

    if (
      isAgentEdit &&
      (!form.actualDuration ||
        Number(form.actualDuration) <= 0)
    ) {
      setAlertMessage("La durée réelle doit être supérieure à 0.");
      return;
    }

    setSaving(true);

    try {
      if (isEdit) {
        if (!isAgent) {
          await updateMission(id, form);
        }
        if (
          form.actualDuration !== "" &&
          String(form.actualDuration) !== String(initialForm.actualDuration)
        ) {
          await updateMissionActualDuration(id, form.actualDuration);
        }
        if (
          canAddRemark &&
          form.remark.trim()
        ) {
          await addMissionRemark(
            id,
            form.remark.trim()
          );
        }
      } else {
        await createMission(form);
      }
      navigate(
        isEdit
          ? `/missions/${id}`
          : "/"
      );
    } catch (err) {
      console.error("Error saving mission:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setSaving(true);
    try {
      await deleteMission(id);
      navigate("/");
    } catch (err) {
      console.error("Error deleting mission:", err);
    } finally {
      setSaving(false);
      setShowDeleteModal(false);
    }
  };

  const isAgentEdit = isEdit && isAgent && !isManager;
  const lockMissionFields = isAgentEdit;

  const isAssignedToMission =
    (loadedMission?.assignedUsers || []).some(
      (assignedUserId) =>
        String(assignedUserId) === String(currentUser?.id)
    );

  // The backend only restricts actual-duration/remark updates by assignment
  // for agents; a manager/admin can always edit these fields regardless of
  // assignment (MissionService._require_agent_assignment_if_agent only
  // applies to the agent role).
  const canAgentUpdateTracking =
    isAgentEdit &&
    isAssignedToMission &&
    ["in_progress", "remark_pending_validation"].includes(
      loadedMission?.status
    );

  const canEditActualDuration = isManager || canAgentUpdateTracking;

  const canAgentAddRemark =
    canAgentUpdateTracking &&
    loadedMission?.status === "in_progress" &&
    !loadedMission?.remark;

  const isAssignedToMissionAsManager =
    isManager &&
    (loadedMission?.assignedUsers || []).some(
      (assignedUserId) =>
        String(assignedUserId) === String(currentUser?.id)
    );

  const canManagerAddRemark =
    isAssignedToMissionAsManager &&
    loadedMission?.status === "in_progress" &&
    !loadedMission?.remark;

  const canAddRemark = canAgentAddRemark || canManagerAddRemark;

  if (loading) return null;

  const assignedUserDetails = assignableUsers.filter((candidate) =>
    form.assignedUsers.includes(candidate.id)
  );
  const unassignedUsers = assignableUsers.filter(
    (candidate) => !form.assignedUsers.includes(candidate.id)
  );

  return (
    <Layout>
      <div className="mission-form-page">
        <button className="back-link" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} />
          Retour
        </button>

        {showDeleteModal && (
          <DeleteConfirmModal
            onConfirm={handleDelete}
            onCancel={() => setShowDeleteModal(false)}
          />
        )}

        {alertMessage && (
          <AlertModal
            message={alertMessage}
            onClose={() => setAlertMessage(null)}
          />
        )}

        <div className="mission-form-card">
          <p className="mission-form-title">{titles[mode]}</p>

          <form onSubmit={handleSave} noValidate>
            {/* Titre */}
            <div className="mission-field">
              <label className="mission-field-label" htmlFor="title">
                Titre
                {!isAgent && <span className="mission-field-required">*</span>}
              </label>
              <input
                className="mission-field-input"
                type="text"
                id="title"
                name="title"
                placeholder="Titre de la mission"
                value={form.title}
                onChange={handleChange}
                disabled={lockMissionFields}
                required={!isAgent}
              />
            </div>

            {/* Service (multi-sélection) */}
            <div className="mission-field">
              <label className="mission-field-label">
                Service
                {!isAgent && <span className="mission-field-required">*</span>}
              </label>
              <div className="mission-service-group">
                {serviceOptions.map((service) => (
                  <label key={service.id} className="mission-checkbox-item">
                    <input
                      type="checkbox"
                      checked={form.serviceIds.includes(service.id)}
                      onChange={() => handleServiceToggle(service.id)}
                      disabled={isAgent}
                    />
                    {service.label}
                  </label>
                ))}
              </div>
            </div>

            {/* Priorité + Type d'intervention */}
            <div className="mission-field-row">
              <div className="mission-field">
                <label className="mission-field-label" htmlFor="priority">
                  Priorité
                  {!isAgent && <span className="mission-field-required">*</span>}
                </label>
                <select
                  className="mission-field-select"
                  id="priority"
                  name="priority"
                  value={form.priority}
                  onChange={handleChange}
                  disabled={isAgent}
                  required={!isAgent}
                >
                  <option value="" />
                  {priorityOptions.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>

              <div className="mission-field">
                <label className="mission-field-label" htmlFor="interventionType">
                  Type d'intervention
                  {!isAgent && <span className="mission-field-required">*</span>}
                </label>
                <input
                  className="mission-field-input"
                  type="text"
                  id="interventionType"
                  name="interventionType"
                  placeholder="ex : Réparation, Entretien"
                  value={form.interventionType}
                  onChange={handleChange}
                  disabled={lockMissionFields}
                  required={!isAgent}
                />
              </div>
            </div>

            {/* Localisation */}
            <div className="mission-field">
              <label className="mission-field-label" htmlFor="location">
                Localisation
                {!isAgent && <span className="mission-field-required">*</span>}
              </label>
              <input
                className="mission-field-input"
                type="text"
                id="location"
                name="location"
                placeholder="Localisation de la mission"
                value={form.location}
                onChange={handleChange}
                disabled={lockMissionFields}
                required={!isAgent}
              />
            </div>

            {/* Description */}
            <div className="mission-field">
              <label className="mission-field-label" htmlFor="description">
                Description
                {!isAgent && <span className="mission-field-required">*</span>}
              </label>
              <textarea
                className="mission-field-textarea"
                id="description"
                name="description"
                placeholder="Description détaillée de la mission"
                value={form.description}
                onChange={handleChange}
                disabled={lockMissionFields}
                required={!isAgent}
              />
            </div>

            {/* Date de début + Date de fin */}
            <div className="mission-field-row">
              <div className="mission-field">
                <label className="mission-field-label" htmlFor="startDate">
                  Date de début
                  {!isAgent && <span className="mission-field-required">*</span>}
                </label>
                <input
                  className="mission-field-input"
                  type="date"
                  id="startDate"
                  name="startDate"
                  value={form.startDate}
                  onChange={handleChange}
                  disabled={lockMissionFields}
                  required={!isAgent}
                />
              </div>

              <div className="mission-field">
                <label className="mission-field-label" htmlFor="endDate">
                  Date de fin
                  {!isAgent && <span className="mission-field-required">*</span>}
                </label>
                <input
                  className="mission-field-input"
                  type="date"
                  id="endDate"
                  name="endDate"
                  value={form.endDate}
                  onChange={handleChange}
                  disabled={lockMissionFields}
                  required={!isAgent}
                  min={form.startDate || undefined}
                />
              </div>
            </div>

            {/* Durée estimée */}
            <div className="mission-field">
              <label className="mission-field-label" htmlFor="estimatedDuration">
                Durée estimée (heures)
                {!isAgent && <span className="mission-field-required">*</span>}
              </label>
              <input
                className="mission-field-input"
                type="number"
                id="estimatedDuration"
                name="estimatedDuration"
                placeholder="ex : 16"
                value={form.estimatedDuration}
                onChange={handleChange}
                disabled={lockMissionFields}
                required={!isAgent}
              />
            </div>

            {/* Équipement requis */}
            <div className="mission-field">
              <label className="mission-field-label" htmlFor="equipment">
                Équipement requis
                {!isAgent && <span className="mission-field-required">*</span>}
              </label>
              <textarea
                className="mission-field-textarea"
                id="equipment"
                name="equipment"
                placeholder="Lister l'équipement et le matériel requis"
                value={form.equipment}
                onChange={handleChange}
                disabled={lockMissionFields}
                required={!isAgent}
              />
            </div>

            {/* Signalisation requise */}
            <div className="mission-checkbox-standalone">
              <label className="mission-checkbox-item">
                <input
                  type="checkbox"
                  id="signageRequired"
                  name="signageRequired"
                  checked={form.signageRequired}
                  onChange={handleChange}
                  disabled={lockMissionFields}
                />
                Signalisation requise
              </label>
            </div>

            {/* Utilisateurs assignés — manager/admin only */}
            {isManager && (
              <div className="mission-field">
                <label className="mission-field-label">Utilisateurs assignés</label>

                {assignedUserDetails.length > 0 && (
                  <div className="mission-users-table-wrapper">
                    <table className="mission-users-table">
                      <thead>
                        <tr>
                          <th>Nom</th>
                          <th>Prénom</th>
                          <th>Service</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {assignedUserDetails.map((assignedUser) => (
                          <tr key={assignedUser.id}>
                            <td>{assignedUser.lastName}</td>
                            <td>{assignedUser.firstName}</td>
                            <td>{assignedUser.service}</td>
                            <td>
                              <button
                                type="button"
                                className="mission-user-remove"
                                onClick={() => handleUserToggle(assignedUser.id)}
                                aria-label={`Retirer ${assignedUser.firstName} ${assignedUser.lastName}`}
                              >
                                <X size={16} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <button
                  type="button"
                  className="mission-add-users-btn"
                  onClick={() => setShowAddUsers((isVisible) => !isVisible)}
                  aria-expanded={showAddUsers}
                >
                  <UserPlus size={16} />
                  Ajouter des utilisateurs
                </button>

                {showAddUsers && (
                  <div className="mission-users-table-wrapper" style={{ marginTop: "12px" }}>
                    <table className="mission-users-table">
                      <thead>
                        <tr>
                          <th>Nom</th>
                          <th>Prénom</th>
                          <th>Service</th>
                          <th>Assigner</th>
                        </tr>
                      </thead>
                      <tbody>
                        {unassignedUsers.map((candidate) => (
                          <tr key={candidate.id}>
                            <td>{candidate.lastName}</td>
                            <td>{candidate.firstName}</td>
                            <td>{candidate.service}</td>
                            <td>
                              <input
                                type="checkbox"
                                checked={false}
                                onChange={() => handleUserToggle(candidate.id)}
                                aria-label={`Assigner ${candidate.firstName} ${candidate.lastName}`}
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Durée réelle — edit mode only, editable by the assigned agent or a manager */}
            {isEdit && (
              <div className="mission-field">
                <label className="mission-field-label" htmlFor="actualDuration">
                  Durée réelle (heures)<span className="mission-field-required">*</span>
                </label>
                <input
                  className="mission-field-input"
                  type="number"
                  id="actualDuration"
                  name="actualDuration"
                  min="0.5"
                  step="0.5"
                  placeholder="Nombre d'heures réellement effectuées"
                  value={form.actualDuration}
                  onChange={handleChange}
                  disabled={!canEditActualDuration}
                  required
                />
              </div>
            )}

            {/* Remarque — edit mode only for Agent and Manager. */}
            {isEdit && (isAgent || isManager) && (
              <div className="mission-field">
                <label className="mission-field-label" htmlFor="remark">
                  Remarque
                  {isAgent && <span className="mission-field-required">*</span>}
                </label>
                <textarea
                  className="mission-field-textarea"
                  id="remark"
                  name="remark"
                  placeholder="Ajouter une remarque si nécessaire"
                  value={form.remark}
                  onChange={handleChange}
                  disabled={!canAddRemark}
                />
              </div>
            )}

            <hr className="mission-divider" />

            {/* Actions */}
            <div className={`mission-form-actions${isEdit ? "" : " mission-form-actions--center"}`}>
              <button
                type="submit"
                className="profile-btn-primary"
                disabled={
                  saving ||
                  (isAgentEdit &&
                    !canAgentUpdateTracking)
                }
              >
                {saving
                  ? "Enregistrement…"
                  : isEdit
                    ? "Enregistrer les modifications"
                    : "Créer la mission"}
              </button>
              {isEdit && isManager && (
                <button
                  type="button"
                  className="profile-btn-danger"
                  onClick={() => setShowDeleteModal(true)}
                >
                  <Trash2 size={16} />
                  Supprimer la mission
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
}

export default MissionFormPage;