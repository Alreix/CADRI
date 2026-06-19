import { useState, useEffect, useContext } from "react";
import { User, Info, X } from "lucide-react";
import Layout from "../components/layout/Layout";
import { AuthContext } from "../contexts/AuthContext";
import { getProfile, updateProfile } from "../api/profileApi";
import { changePassword } from "../api/authApi";
import PasswordRequirementsModal from "../components/common/PasswordRequirementsModal";
import "../styles/ProfilePage.css";

function LogoutConfirmModal({ onConfirm, onCancel }) {
  return (
    <div className="confirm-modal-overlay" role="dialog" aria-modal="true">
      <div className="confirm-modal">
        <div className="confirm-modal-header">
          <span className="confirm-modal-title">Déconnexion</span>
          <button className="confirm-modal-close" onClick={onCancel} aria-label="Fermer">
            <X size={18} />
          </button>
        </div>
        <div className="confirm-modal-body">
          Êtes-vous sûr de vouloir vous déconnecter ?
        </div>
        <div className="confirm-modal-footer">
          <button className="confirm-modal-cancel" onClick={onCancel}>Non</button>
          <button className="profile-btn-primary" onClick={onConfirm}>Oui</button>
        </div>
      </div>
    </div>
  );
}

function ProfilePage() {
  const { user, logout } = useContext(AuthContext);

  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [showLogout, setShowLogout] = useState(false);
  const [showPasswordHint, setShowPasswordHint] = useState(false);

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    currentPassword: "",
    password: "",
    confirmPassword: "",
  });

  useEffect(() => {
    getProfile().then((data) => {
      setProfile(data);
      setForm({
        firstName: data.firstName || "",
        lastName: data.lastName || "",
        email: data.email || "",
        currentPassword: "",
        password: "",
        confirmPassword: "",
      });
    });
  }, []);

  const clearPasswordFields = () => {
    setForm((prevForm) => ({
      ...prevForm,
      currentPassword: "",
      password: "",
      confirmPassword: "",
    }));
  };

  const handleSave = async (event) => {
    event.preventDefault();
    const wantsPasswordChange = form.password || form.confirmPassword;

    if (wantsPasswordChange) {
      if (form.password !== form.confirmPassword) {
        window.alert("Les mots de passe ne correspondent pas.");
        return;
      }
      if (!form.currentPassword) {
        window.alert("Le mot de passe actuel est obligatoire pour changer le mot de passe.");
        return;
      }
      await changePassword({
        currentPassword: form.currentPassword,
        newPassword: form.password,
      });
    }

    const updatedProfile = await updateProfile(form);
    setProfile((prevProfile) => ({ ...prevProfile, ...updatedProfile }));
    clearPasswordFields();
    setEditing(false);
  };

  const handleCancel = () => {
    setForm({
      firstName: profile.firstName || "",
      lastName: profile.lastName || "",
      email: profile.email || "",
      currentPassword: "",
      password: "",
      confirmPassword: "",
    });
    setEditing(false);
  };

  if (!profile) return null;

  return (
    <Layout>
      {showLogout && (
        <LogoutConfirmModal
          onConfirm={logout}
          onCancel={() => setShowLogout(false)}
        />
      )}
      {showPasswordHint && (
        <PasswordRequirementsModal onClose={() => setShowPasswordHint(false)} />
      )}

      <div className="profile-page">
        <div className="profile-title">
          <div className="profile-title-icon">
            <User size={22} />
          </div>
          <h1>Profil</h1>
        </div>

        <div className="profile-card">
          {!editing && (
            <>
              <p className="profile-section-title">Informations personnelles</p>
              <div className="profile-info-grid">
                <div className="profile-info-item">
                  <span className="profile-info-label">Rôle</span>
                  <span className="profile-info-value">{profile.role}</span>
                </div>
                <div className="profile-info-item">
                  <span className="profile-info-label">Service</span>
                  <span className="profile-info-value">{profile.service}</span>
                </div>
                <div className="profile-info-item">
                  <span className="profile-info-label">Prénom</span>
                  <span className="profile-info-value">{profile.firstName}</span>
                </div>
                <div className="profile-info-item">
                  <span className="profile-info-label">Nom</span>
                  <span className="profile-info-value">{profile.lastName}</span>
                </div>
                <div className="profile-info-item profile-info-grid--full">
                  <span className="profile-info-label">Email</span>
                  <span className="profile-info-value">{profile.email}</span>
                </div>
              </div>

              <hr className="profile-divider" />

              <div className="profile-actions">
                <button
                  className="profile-btn-primary"
                  onClick={() => setEditing(true)}
                >
                  Modifier le profil
                </button>
                <button
                  className="profile-btn-cancel"
                  onClick={() => setShowLogout(true)}
                  aria-label="Log out"
                >
                  Déconnexion
                </button>
              </div>
            </>
          )}

          {editing && (
            <form onSubmit={handleSave} autoComplete="off" noValidate>
              <p className="profile-section-title">Informations personnelles</p>

              <div className="profile-form-grid">
                <div className="profile-field">
                  <label className="profile-field-label">Rôle</label>
                  <input className="profile-field-input" value={profile.role} readOnly />
                </div>

                <div className="profile-field">
                  <label className="profile-field-label">Service</label>
                  <input className="profile-field-input" value={profile.service} readOnly />
                </div>

                <div className="profile-field">
                  <label className="profile-field-label" htmlFor="firstName">
                    Prénom<span className="profile-field-required">*</span>
                  </label>
                  <input
                    id="firstName"
                    className="profile-field-input"
                    value={form.firstName}
                    onChange={(event) => setForm((prevForm) => ({ ...prevForm, firstName: event.target.value }))}
                    required
                    aria-label="first name"
                  />
                </div>

                <div className="profile-field">
                  <label className="profile-field-label" htmlFor="lastName">
                    Nom<span className="profile-field-required">*</span>
                  </label>
                  <input
                    id="lastName"
                    className="profile-field-input"
                    value={form.lastName}
                    onChange={(event) => setForm((prevForm) => ({ ...prevForm, lastName: event.target.value }))}
                    required
                    aria-label="last name"
                  />
                </div>

                <div className="profile-field profile-form-grid--full">
                  <label className="profile-field-label" htmlFor="email">
                    Email<span className="profile-field-required">*</span>
                  </label>
                  <input
                    id="email"
                    type="email"
                    className="profile-field-input"
                    value={form.email}
                    onChange={(event) => setForm((prevForm) => ({ ...prevForm, email: event.target.value }))}
                    required
                  />
                </div>
              </div>

              <hr className="profile-divider" />
              <p className="profile-section-title">Changer le mot de passe (optionnel)</p>

              <div className="profile-form-grid">
                <div className="profile-field profile-form-grid--full">
                  <label className="profile-field-label" htmlFor="profile-current-password">
                    Mot de passe actuel
                  </label>
                  <input
                    id="profile-current-password"
                    name="profile-current-password"
                    type="password"
                    className="profile-field-input"
                    placeholder="Saisir votre mot de passe actuel"
                    value={form.currentPassword}
                    onChange={(event) => setForm((prevForm) => ({ ...prevForm, currentPassword: event.target.value }))}
                    autoComplete="current-password"
                  />
                </div>

                <div className="profile-field">
                  <label className="profile-field-label" htmlFor="profile-new-password">
                    Nouveau mot de passe
                  </label>
                  <div className="profile-input-wrapper">
                    <input
                      id="profile-new-password"
                      name="profile-new-password"
                      type="password"
                      className="profile-field-input"
                      placeholder="Laisser vide pour conserver l'actuel"
                      value={form.password}
                      onChange={(event) => setForm((prevForm) => ({ ...prevForm, password: event.target.value }))}
                      aria-label="new password"
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      className="profile-input-info"
                      onClick={() => setShowPasswordHint(true)}
                      aria-label="Voir les exigences du mot de passe"
                    >
                      <Info size={16} />
                    </button>
                  </div>
                </div>

                <div className="profile-field">
                  <label className="profile-field-label" htmlFor="profile-confirm-password">
                    Confirmer le nouveau mot de passe
                  </label>
                  <input
                    id="profile-confirm-password"
                    name="profile-confirm-password"
                    type="password"
                    className="profile-field-input"
                    placeholder="Laisser vide pour conserver l'actuel"
                    value={form.confirmPassword}
                    onChange={(event) => setForm((prevForm) => ({ ...prevForm, confirmPassword: event.target.value }))}
                    autoComplete="new-password"
                  />
                </div>
              </div>

              <div className="profile-actions">
                <button type="submit" className="profile-btn-primary">
                  Mettre à jour le profil
                </button>
                <button type="button" className="profile-btn-cancel" onClick={handleCancel}>
                  Annuler
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </Layout>
  );
}

export default ProfilePage;
