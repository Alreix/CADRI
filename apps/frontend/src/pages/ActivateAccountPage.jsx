// Account activation page, reached via the emailed activation link (?token=...).
// Lets a newly created user set their initial password.
import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import PasswordRequirementsModal from "../components/common/PasswordRequirementsModal";
import PasswordFieldWithHint from "../components/common/PasswordFieldWithHint";
import { usePasswordConfirmation } from "../hooks/usePasswordConfirmation";
import { activateAccount } from "../api/authApi";
import { X } from "lucide-react";
import "../styles/AuthLayout.css";

// One-time welcome modal shown automatically when the page first loads.
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

  // Activation token comes from the URL, e.g. /activate?token=abc123
  const token = searchParams.get("token") || "";

  const [showWelcome, setShowWelcome] = useState(true);

  const {
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    mismatch,
    reset,
    showHint,
    openHint,
    closeHint,
  } = usePasswordConfirmation(token);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (mismatch) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await activateAccount({ token, password });
      reset();
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

      {showHint && (
        <PasswordRequirementsModal onClose={closeHint} />
      )}

      <div className="auth-card">
        <h1 className="auth-card-title">Activer votre compte</h1>

        <form onSubmit={handleSubmit} autoComplete="off" noValidate>
          <PasswordFieldWithHint
            id="activation-new-password"
            label="Mot de passe"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onShowHint={openHint}
          />

          <PasswordFieldWithHint
            id="activation-confirm-password"
            label="Confirmer le mot de passe"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            onShowHint={openHint}
          />

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
