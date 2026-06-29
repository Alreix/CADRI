import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import PasswordRequirementsModal from "../components/common/PasswordRequirementsModal";
import PasswordInput from "../components/common/PasswordInput";
import { activateAccount } from "../api/authApi";
import { Info, X } from "lucide-react";
import "../styles/AuthLayout.css";

function WelcomeModal({ onClose }) {
  return (
    <div className="auth-modal-overlay" role="dialog" aria-modal="true">
      <div className="auth-modal">
        <div className="auth-modal-header">
          <span className="auth-modal-title">Bienvenue sur CADRI !</span>
          <button className="auth-modal-close" onClick={onClose} aria-label="Fermer">
            <X size={18} />
          </button>
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

  useEffect(() => {
    setPassword("");
    setConfirmPassword("");
  }, [token]);

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
      setPassword("");
      setConfirmPassword("");
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

        <form onSubmit={handleSubmit} autoComplete="off" noValidate>
          <div className="auth-field">
            <label className="auth-label" htmlFor="activation-new-password">
              Mot de passe<span className="auth-label-required">*</span>
            </label>
            <PasswordInput
              id="activation-new-password"
              name="activation-new-password"
              className="auth-input"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="new-password"
              rightIcon={
                <button
                  type="button"
                  className="auth-password-info-btn"
                  onClick={() => setShowPasswordHint(true)}
                  aria-label="Voir les exigences du mot de passe"
                >
                  <Info size={16} />
                </button>
              }
            />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="activation-confirm-password">
              Confirmer le mot de passe<span className="auth-label-required">*</span>
            </label>
            <PasswordInput
              id="activation-confirm-password"
              name="activation-confirm-password"
              className="auth-input"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
              autoComplete="new-password"
              rightIcon={
                <button
                  type="button"
                  className="auth-password-info-btn"
                  onClick={() => setShowPasswordHint(true)}
                  aria-label="Voir les exigences du mot de passe"
                >
                  <Info size={16} />
                </button>
              }
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
