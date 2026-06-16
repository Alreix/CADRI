import { useState, useEffect, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { AuthContext } from "../contexts/AuthContext";
import { getServices } from "../api/metadataApi";
import { getMission, createMission, updateMission, deleteMission } from "../api/missionsApi";
import { getAssignableUsers } from "../api/usersApi";
import "../styles/MissionFormPage.css";

function DeleteConfirmModal({ onConfirm, onCancel }) {
  return (
    <div className="confirm-modal-overlay">
      <div className="confirm-modal">
        <div className="confirm-modal-content">
          <span className="confirm-modal-title">Supprimer la mission</span>
        </div>
        <div className="confirm-modal-footer">
          Êtes-vous sûr de vouloir supprimer cette mission ?
        </div>
        <div className="confirm-modal-actions">
          <button className="confirm-modal-cancel" onClick={onCancel}>Non, annuler</button>
          <button className="confirm-modal-confirm-danger" onClick={onConfirm}>Oui, supprimer</button>
        </div>
      </div>
    </div>
  );
}

function MissionFormPage({ mode = "create" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useContext(AuthContext);

  const isManager = currentUser?.role === "responsable" || currentUser?.role === "admin";

  const [form, setForm] = useState({
    title: "",
    description: "",
    service: "",
    startDate: "",
    endDate: "",
    estimatedDuration: "",
    interventionType: "",
    location: "",
    equipment: "",
    signageRequired: false,
    priority: "medium",
    assignedUsers: [],
  });

  const [serviceOptions, setServiceOptions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(mode === "edit");
  const [saving, setSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const isEdit = mode === "edit";

  const titles = {
    create: "Créer une mission",
    edit: "Modifier la mission",
  };

  useEffect(() => {
    Promise.all([
      getServices().then(setServiceOptions),
      getAssignableUsers().then(setUsers),
    ]).then(() => {
      if (isEdit && id) {
        getMission(id)
          .then((mission) => {
            setForm({
              title: mission.title || "",
              description: mission.description || "",
              service: mission.serviceIds?.[0] || "",
              startDate: mission.startDate || "",
              endDate: mission.endDate || "",
              estimatedDuration: mission.estimatedDuration || "",
              interventionType: mission.interventionType || "",
              location: mission.location || "",
              equipment: mission.equipment || "",
              signageRequired: mission.signageRequired || false,
              priority: mission.priority || "medium",
              assignedUsers: mission.assignedUsers || [],
            });
          })
          .catch((err) => console.error("Failed to load mission:", err))
          .finally(() => setLoading(false));
      }
    });
  }, [id, isEdit]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((prevForm) => ({
      ...prevForm,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleUserToggle = (userId) => {
    setForm((prevForm) => ({
      ...prevForm,
      assignedUsers: prevForm.assignedUsers.includes(userId)
        ? prevForm.assignedUsers.filter((id) => id !== userId)
        : [...prevForm.assignedUsers, userId],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (isEdit) {
        await updateMission(id, form);
      } else {
        await createMission(form);
      }
      navigate("/missions");
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
      navigate("/missions");
    } catch (err) {
      console.error("Error deleting mission:", err);
    } finally {
      setSaving(false);
      setShowDeleteModal(false);
    }
  };

  if (loading) return null;

  return (
    <Layout>
      <div className="page-wrapper">
        <h1>{titles[mode]}</h1>

        {showDeleteModal && (
          <DeleteConfirmModal
            onConfirm={handleDelete}
            onCancel={() => setShowDeleteModal(false)}
          />
        )}

        <form className="form-container">
          {/* Titre */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="title">
              Titre
            </label>
            <input
              className="mission-field-input"
              type="text"
              id="title"
              name="title"
              placeholder="Titre de la mission"
              value={form.title}
              onChange={handleChange}
              required
            />
          </div>

          {/* Service */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="service">
              Service
            </label>
            <select
              className="mission-field-input"
              id="service"
              name="service"
              value={form.service}
              onChange={handleChange}
            >
              <option value="">-- Sélectionner --</option>
              {serviceOptions.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.label}
                </option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="description">
              Description
            </label>
            <textarea
              className="mission-field-textarea"
              id="description"
              name="description"
              placeholder="Description détaillée de la mission"
              value={form.description}
              onChange={handleChange}
            />
          </div>

          {/* Localisation */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="location">
              Localisation
            </label>
            <input
              className="mission-field-input"
              type="text"
              id="location"
              name="location"
              placeholder="Lieu de la mission"
              value={form.location}
              onChange={handleChange}
            />
          </div>

          {/* Date de début */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="startDate">
              Date de début
            </label>
            <input
              className="mission-field-input"
              type="date"
              id="startDate"
              name="startDate"
              value={form.startDate}
              onChange={handleChange}
            />
          </div>

          {/* Date de fin */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="endDate">
              Date de fin
            </label>
            <input
              className="mission-field-input"
              type="date"
              id="endDate"
              name="endDate"
              value={form.endDate}
              onChange={handleChange}
            />
          </div>

          {/* Durée estimée */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="estimatedDuration">
              Durée estimée (heures)
            </label>
            <input
              className="mission-field-input"
              type="number"
              id="estimatedDuration"
              name="estimatedDuration"
              placeholder="Nombre d'heures"
              value={form.estimatedDuration}
              onChange={handleChange}
            />
          </div>

          {/* Type d'intervention */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="interventionType">
              Type d'intervention
            </label>
            <input
              className="mission-field-input"
              type="text"
              id="interventionType"
              name="interventionType"
              placeholder="Type d'intervention"
              value={form.interventionType}
              onChange={handleChange}
            />
          </div>

          {/* Équipement requis */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="equipment">
              Équipement requis
            </label>
            <input
              className="mission-field-input"
              type="text"
              id="equipment"
              name="equipment"
              placeholder="Équipement nécessaire"
              value={form.equipment}
              onChange={handleChange}
            />
          </div>

          {/* Priorité */}
          <div className="form-group">
            <label className="mission-field-label" htmlFor="priority">
              Priorité
            </label>
            <select
              className="mission-field-input"
              id="priority"
              name="priority"
              value={form.priority}
              onChange={handleChange}
            >
              <option value="low">Basse</option>
              <option value="medium">Moyenne</option>
              <option value="high">Urgente</option>
            </select>
          </div>

          {/* Signalisation requise */}
          <div className="form-group form-group--checkbox">
            <label htmlFor="signageRequired">
              <input
                type="checkbox"
                id="signageRequired"
                name="signageRequired"
                checked={form.signageRequired}
                onChange={handleChange}
              />
              Signalisation requise
            </label>
          </div>

          {/* Utilisateurs assignés — edit + manager/admin only */}
          {isEdit && (isManager) && (
            <div className="form-group">
              <label className="mission-field-label">Utilisateurs assignés</label>
              <table className="users-assignment-table">
                <thead>
                  <tr>
                    <th>Prénom</th>
                    <th>Nom</th>
                    <th>Assigné</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((assignedUser) => (
                    <tr key={assignedUser.id}>
                      <td>{assignedUser.firstName}</td>
                      <td>{assignedUser.lastName}</td>
                      <td>
                        <input
                          type="checkbox"
                          checked={form.assignedUsers.includes(assignedUser.id)}
                          onChange={() => handleUserToggle(assignedUser.id)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Actions */}
          <div className="form-actions">
            <button
              type="button"
              className="btn-cancel"
              onClick={() => navigate("/missions")}
            >
              Annuler
            </button>
            <button
              type="button"
              className="btn-save"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? "Sauvegarde…" : isEdit ? "Mettre à jour" : "Créer la mission"}
            </button>
            {isEdit && isManager && (
              <button
                type="button"
                className="btn-delete"
                onClick={() => setShowDeleteModal(true)}
              >
                Supprimer
              </button>
            )}
          </div>
        </form>
      </div>
    </Layout>
  );
}

export default MissionFormPage;
