import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import PasswordRequirementsModal from "../components/common/PasswordRequirementsModal";
import { activateAccount } from "../api/authApi";
import "../styles/AuthLayout.css";

function WelcomeModal({ onClose }) {
  return (
    <div className="auth-modal-overlay" role="dialog" aria-modal="true">
      <div className="auth-modal">
        <div className="auth-modal-header">
          <span className="auth-modal-title">Bienvenue sur CADRI !</span>
          <button className="auth-modal-close" onClick={onClose} aria-label="Fermer">✕</button>
        </div>
        <div className="auth-modal-body" style={{ display: "block", padding: "20px 24px" }}>
          <p style={{ fontSize: "0.9rem", color: "#1a2332", lineHeight: "1.6" }}>
            Veuillez définir un mot de passe sécurisé pour
            activer votre compte et commencer.
          </p>
        </div>
        <div className="auth-modal-footer">
          <button className="auth-modal-btn-ok" onClick={onClose}>Continuer</button>
        </div>
      </div>
    </div>
  );
}

function ActivateAccountPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const token = searchParams.get("token") || "";

  const [showWelcome, setShowWelcome] = useState(true);
  const [showPasswordHint, setShowPasswordHint] = useState(false);

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }
    setLoading(true);
      setError(null);
    try {
      await activateAccount({ token, password });
      navigate("/login");
    } catch (err) {
      setError(err.message || "Une erreur s'est produite.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      {showWelcome && <WelcomeModal onClose={() => setShowWelcome(false)} />}

      {showPasswordHint && (
        <PasswordRequirementsModal onClose={() => setShowPasswordHint(false)} />
      )}

      <div className="auth-card">
        <h1 className="auth-card-title">Activer votre compte</h1>

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label className="auth-label" htmlFor="password">
              Mot de passe<span className="auth-label-required">*</span>
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

          {error && (
            <p style={{ color: "var(--auth-required)", fontSize: "0.875rem", marginBottom: "12px" }}>
              {error}
            </p>
          )}

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Activation…" : "Activer le compte"}
          </button>
        </form>
      </div>
    </AuthLayout>
  );
}

export default ActivateAccountPage;
