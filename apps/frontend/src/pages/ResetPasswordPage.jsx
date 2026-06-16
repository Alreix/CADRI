import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import Modal from "../components/common/Modal";
import PasswordRequirementsModal from "../components/common/PasswordRequirementsModal";
import { resetPassword } from "../api/authApi";
import "../styles/AuthLayout.css";

function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const token = searchParams.get("token") || "";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPasswordHint, setShowPasswordHint] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      setModal({ title: "Erreur", message: "Les mots de passe ne correspondent pas." });
      return;
    }
    setLoading(true);
    try {
      await resetPassword({ token, email, password });
      navigate("/connexion");
    } catch (err) {
      setModal({ title: "Erreur", message: err.message || "Une erreur s'est produite." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      {modal && (
        <Modal
          title={modal.title}
          message={modal.message}
          onClose={() => setModal(null)}
        />
      )}

      {showPasswordHint && (
        <PasswordRequirementsModal onClose={() => setShowPasswordHint(false)} />
      )}

      <div className="auth-card">
        <h1 className="auth-card-title">Réinitialiser le mot de passe</h1>

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label className="auth-label" htmlFor="email">
              Email<span className="auth-label-required">*</span>
            </label>
            <input
              id="email"
              type="email"
              className="auth-input"
              placeholder="votre.email@exemple.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="password">
              Nouveau mot de passe<span className="auth-label-required">*</span>
            </label>
            <div className="auth-input-wrapper">
              <input
                id="password"
                type="password"
                className="auth-input"
                placeholder="••••••••"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                autoComplete="new-password"
              />
              <span
                className="auth-input-icon"
                onClick={() => setShowPasswordHint(true)}
                title="Voir les exigences"
                aria-label="Voir les exigences du mot de passe"
                role="button"
                tabIndex={0}
              >
                ⓘ
              </span>
            </div>
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="confirmPassword">
              Confirmer le mot de passe<span className="auth-label-required">*</span>
            </label>
            <input
              id="confirmPassword"
              type="password"
              className="auth-input"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
              autoComplete="new-password"
            />
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Réinitialisation…" : "Réinitialiser le mot de passe"}
          </button>
        </form>

        <Link to="/connexion" className="auth-back-link">
          Retour à la connexion
        </Link>
      </div>
    </AuthLayout>
  );
}

export default ResetPasswordPage;