import { useState, useEffect, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Trash2, X } from "lucide-react";
import Layout from "../components/layout/Layout";
import { AuthContext } from "../contexts/AuthContext";
import { getUser, createUser, updateUser, deleteUser } from "../api/usersApi";
import { getRoles, getServices } from "../api/metadataApi";
import "../styles/ConfirmModals.css";

function DeleteConfirmModal({ onConfirm, onCancel }) {
  return (
    <div className="confirm-modal-overlay" role="dialog" aria-modal="true">
      <div className="confirm-modal">
        <div className="confirm-modal-header">
          <span className="confirm-modal-title">Supprimer l'utilisateur</span>
          <button className="confirm-modal-close" onClick={onCancel} aria-label="Fermer">
            <X size={18} />
          </button>
        </div>
        <div className="confirm-modal-body">
          Êtes-vous sûr de vouloir supprimer cet utilisateur ?
          Cette action ne peut pas être annulée.
        </div>
        <div className="confirm-modal-footer">
          <button className="confirm-modal-cancel" onClick={onCancel}>Non, conserver</button>
          <button
            className="confirm-modal-confirm-danger"
            onClick={onConfirm}
            aria-label="confirm"
          >
            Oui, supprimer
          </button>
        </div>
      </div>
    </div>
  );
}

function UserFormPage({ mode = "create" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useContext(AuthContext);

  const isAdmin = currentUser?.role === "admin";
  const isManager = currentUser?.role === "responsable";
  const [serviceOptions, setServiceOptions] = useState([]);
  const [roleOptionsSource, setRoleOptionsSource] = useState([
    { value: "agent", label: "Agent" },
    { value: "responsable", label: "Responsable" },
    { value: "admin", label: "Admin" },
  ]);
  const [form, setForm] = useState({
    role: isManager ? "agent" : "",
    service: "",
    firstName: "",
    lastName: "",
    email: "",
  });

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getServices()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) setServiceOptions(data);
      })
      .catch(() => {});

    getRoles()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setRoleOptionsSource(
            data.map((role) => ({ value: role.value, label: role.label }))
          );
        }
      })
      .catch(() => {});

    if ((mode === "view" || mode === "edit") && id) {
      getUser(id).then((data) => {
        setForm({
          role: data.role || "",
          service: data.serviceId || "",
          firstName: data.firstName || "",
          lastName: data.lastName || "",
          email: data.email || "",
        });
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

  const roleOptions = isAdmin
    ? roleOptionsSource
    : roleOptionsSource.filter((role) => role.value !== "admin");
  const selectedServiceLabel = (
    serviceOptions.find((service) => service.id === form.service)?.label || form.service
  );

  const titles = {
    create: isManager ? "Créer un nouvel agent" : "Créer un nouvel utilisateur",
    view: "Profil utilisateur",
    edit: "Modifier le profil utilisateur",
  };

  const isReadOnly = mode === "view";

  return (
    <Layout>
      {showDeleteModal && (
        <DeleteConfirmModal
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteModal(false)}
        />
      )}

      <div className="user-form-page">
        <button className="back-link" onClick={() => navigate(-1)}>
          ← Retour
        </button>

        <div className="profile-card">
          <p className="profile-section-title">{titles[mode]}</p>

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
                    value={form.role}
                    readOnly
                    placeholder={isManager ? "Agent" : ""}
                    aria-label="role"
                  />
                ) : (
                  <select
                    id="role"
                    className="profile-field-select"
                    value={form.role}
                    onChange={(event) => setForm((formData) => ({ ...formData, role: event.target.value }))}
                    required
                    aria-label="role"
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
                    onChange={(event) => setForm((formData) => ({ ...formData, service: event.target.value }))}
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
                  onChange={(event) => setForm((formData) => ({ ...formData, firstName: event.target.value }))}
                  readOnly={isReadOnly}
                  required={!isReadOnly}
                  placeholder={isReadOnly ? "" : "Jean"}
                  aria-label="first name"
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
                  onChange={(event) => setForm((formData) => ({ ...formData, lastName: event.target.value }))}
                  readOnly={isReadOnly}
                  required={!isReadOnly}
                  placeholder={isReadOnly ? "" : "Dupont"}
                  aria-label="last name"
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
                  onChange={(event) => setForm((formData) => ({ ...formData, email: event.target.value }))}
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
                  aria-label="delete"
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
