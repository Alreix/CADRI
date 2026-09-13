// Single form used for creating, viewing and editing a user (mode="create" | "view" | "edit").
// Same "mode" pattern as MissionFormPage: one component, fields become
// read-only inputs in "view" mode instead of duplicating three near-identical forms.
import { useState, useEffect, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Trash2 } from "lucide-react";
import Layout from "../components/layout/Layout";
import ConfirmModal from "../components/common/ConfirmModal";
import { AuthContext } from "../contexts/AuthContext";
import { getUser, createUser, updateUser, deleteUser } from "../api/usersApi";
import { getRoles, getServices } from "../api/metadataApi";
import { useMetadataOptions } from "../hooks/useMetadataOptions";
import { useFormState } from "../hooks/useFormState";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import "../styles/ConfirmModals.css";

function UserFormPage({ mode = "create" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useContext(AuthContext);

  const isAdmin = currentUser?.role === "admin";
  const isManager = currentUser?.role === "responsable";

  const [serviceOptions] = useMetadataOptions(getServices, []);

  // Hardcoded fallback roles, replaced by the backend list once it loads.
  const [roleOptionsSource] = useMetadataOptions(
    () => getRoles().then((data) => data.map((role) => ({ value: role.value, label: role.label }))),
    [
      { value: "agent", label: "Agent" },
      { value: "responsable", label: "Responsable" },
      { value: "admin", label: "Admin" },
    ]
  );

  const [form, setForm, setField] = useFormState({
    // A "responsable" creating a user can only create agents (see backend rules),
    // so the role is pre-filled and locked to "agent" for them.
    role: isManager ? "agent" : "",
    service: "",
    firstName: "",
    lastName: "",
    email: "",
  });

  // Backend-provided display label for the role, used in "view" mode instead
  // of re-deriving it from roleOptionsSource (more reliable if labels differ).
  const [loadedRoleLabel, setLoadedRoleLabel] = useState("");

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Loads the target user in view/edit mode.
  useEffect(() => {
    if ((mode === "view" || mode === "edit") && id) {
      getUser(id).then((data) => {
        setForm({
          role: data.role || "",
          service: data.serviceId || "",
          firstName: data.firstName || "",
          lastName: data.lastName || "",
          email: data.email || "",
        });
        setLoadedRoleLabel(data.roleLabel || "");
      });
    }
  }, [mode, id]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      if (mode === "create") {
        await createUser(form);
      } else if (mode === "edit") {
        await updateUser(id, form);
      }
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    await deleteUser(id);
    navigate("/users");
  };

  // A "responsable" can never assign the "admin" role, even when editing.
  const roleOptions = isAdmin
    ? roleOptionsSource
    : roleOptionsSource.filter((role) => role.value !== "admin");
  const selectedServiceLabel = (
    serviceOptions.find((service) => service.id === form.service)?.label || form.service
  );
  const selectedRoleLabel =
    loadedRoleLabel ||
    roleOptionsSource.find((role) => role.value === form.role)?.label ||
    form.role;

  const titles = {
    create: isManager ? "Créer un nouvel agent" : "Créer un nouvel utilisateur",
    view: "Profil utilisateur",
    edit: "Modifier le profil utilisateur",
  };

  useDocumentTitle(titles[mode]);

  const isReadOnly = mode === "view";

  return (
    <Layout>
      {showDeleteModal && (
        <ConfirmModal
          title="Supprimer l'utilisateur"
          message="Êtes-vous sûr de vouloir supprimer cet utilisateur ? Cette action ne peut pas être annulée."
          cancelLabel="Non, conserver"
          confirmLabel="Oui, supprimer"
          danger
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteModal(false)}
        />
      )}

      <div className="user-form-page">
        <button className="back-link" onClick={() => navigate(-1)}>
          ← Retour
        </button>

        <div className="profile-card">
          <h1 className="profile-section-title">{titles[mode]}</h1>

          <form onSubmit={handleSubmit} noValidate>
            <div className="profile-form-grid">

              <div className="profile-field">
                <label className="profile-field-label" htmlFor="role">
                  Rôle
                  {!isReadOnly && <span className="profile-field-required">*</span>}
                </label>
                {isReadOnly || isManager ? (
                  <input
                    id="role"
                    className="profile-field-input"
                    value={selectedRoleLabel}
                    readOnly
                    placeholder={isManager ? "Agent" : ""}
                  />
                ) : (
                  <select
                    id="role"
                    className="profile-field-select"
                    value={form.role}
                    onChange={(event) => setField("role", event.target.value)}
                    required
                  >
                    <option value="" />
                    {roleOptions.map((roleOption) => (
                      <option key={roleOption.value} value={roleOption.value}>{roleOption.label}</option>
                    ))}
                  </select>
                )}
              </div>

              <div className="profile-field">
                <label className="profile-field-label" htmlFor="service">
                  Service
                  {!isReadOnly && <span className="profile-field-required">*</span>}
                </label>
                {isReadOnly ? (
                  <input
                    id="service"
                    className="profile-field-input"
                    value={selectedServiceLabel}
                    readOnly
                  />
                ) : (
                  <select
                    id="service"
                    className="profile-field-select"
                    value={form.service}
                    onChange={(event) => setField("service", event.target.value)}
                    required
                  >
                    <option value="" />
                    {serviceOptions.map((service) => (
                      <option key={service.id} value={service.id}>{service.label}</option>
                    ))}
                  </select>
                )}
              </div>

              <div className="profile-field">
                <label className="profile-field-label" htmlFor="firstName">
                  Prénom
                  {!isReadOnly && <span className="profile-field-required">*</span>}
                </label>
                <input
                  id="firstName"
                  className="profile-field-input"
                  value={form.firstName}
                  onChange={(event) => setField("firstName", event.target.value)}
                  readOnly={isReadOnly}
                  required={!isReadOnly}
                  placeholder={isReadOnly ? "" : "Jean"}
                />
              </div>

              <div className="profile-field">
                <label className="profile-field-label" htmlFor="lastName">
                  Nom
                  {!isReadOnly && <span className="profile-field-required">*</span>}
                </label>
                <input
                  id="lastName"
                  className="profile-field-input"
                  value={form.lastName}
                  onChange={(event) => setField("lastName", event.target.value)}
                  readOnly={isReadOnly}
                  required={!isReadOnly}
                  placeholder={isReadOnly ? "" : "Dupont"}
                />
              </div>

              <div className="profile-field profile-form-grid--full">
                <label className="profile-field-label" htmlFor="email">
                  Email
                  {!isReadOnly && <span className="profile-field-required">*</span>}
                </label>
                <input
                  id="email"
                  type="email"
                  className="profile-field-input"
                  value={form.email}
                  onChange={(event) => setField("email", event.target.value)}
                  readOnly={isReadOnly}
                  required={!isReadOnly}
                  placeholder={isReadOnly ? "" : "jean.dupont@municipality.fr"}
                />
              </div>
            </div>

            {mode === "create" && (
              <p className="form-note">
                <strong>Note :</strong> Le compte sera créé sans mot de passe.
                Un email d'activation sera envoyé automatiquement à l'adresse email de l'utilisateur.
              </p>
            )}

            {mode === "view" && (
              <div className="profile-actions">
                <button
                  type="button"
                  className="profile-btn-primary"
                  onClick={() => navigate(`/users/${id}/edit`)}
                >
                  Modifier le profil utilisateur
                </button>
              </div>
            )}

            {mode === "create" && (
              <div className="profile-actions">
                <button type="submit" className="profile-btn-primary" disabled={loading}>
                  {loading ? "Création…" : "Créer un nouvel utilisateur"}
                </button>
              </div>
            )}

            {mode === "edit" && (
              <div className="profile-actions profile-actions--spread">
                <button type="submit" className="profile-btn-primary" disabled={loading}>
                  {loading ? "Enregistrement…" : "Valider la modification"}
                </button>
                <button
                  type="button"
                  className="profile-btn-danger"
                  onClick={() => setShowDeleteModal(true)}
                >
                  <Trash2 size={16} />
                  Supprimer l'utilisateur
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </Layout>
  );
}

export default UserFormPage;