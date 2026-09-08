// "Reset password" form, reached via the emailed link (?token=...).
// Reads the token from the URL query string rather than from route params.
import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import Modal from "../components/common/Modal";
import PasswordRequirementsModal from "../components/common/PasswordRequirementsModal";
import PasswordFieldWithHint from "../components/common/PasswordFieldWithHint";
import { usePasswordConfirmation } from "../hooks/usePasswordConfirmation";
import { resetPassword } from "../api/authApi";
import "../styles/AuthLayout.css";

function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Reset token comes from the URL, e.g. /reset-password?token=abc123
  const token = searchParams.get("token") || "";

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
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (mismatch) {
      setModal({ title: "Erreur", message: "Les mots de passe ne correspondent pas." });
      return;
    }
    setLoading(true);
    try {
      await resetPassword({ token, password });
      reset();
      navigate("/login");
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

      {showHint && (
        <PasswordRequirementsModal onClose={closeHint} />
      )}

      <div className="auth-card">
        <h1 className="auth-card-title">Réinitialiser le mot de passe</h1>

        <form onSubmit={handleSubmit} autoComplete="off" noValidate>
          <PasswordFieldWithHint
            id="reset-new-password"
            label="Nouveau mot de passe"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onShowHint={openHint}
          />

          <PasswordFieldWithHint
            id="reset-confirm-password"
            label="Confirmer le mot de passe"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            onShowHint={openHint}
          />

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Réinitialisation…" : "Réinitialiser le mot de passe"}
          </button>
        </form>

        <Link to="/login" className="auth-back-link">
          Retour à la connexion
        </Link>
      </div>
    </AuthLayout>
  );
}

export default ResetPasswordPage;
