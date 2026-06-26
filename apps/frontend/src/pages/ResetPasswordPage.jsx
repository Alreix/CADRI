import { useEffect, useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import Modal from "../components/common/Modal";
import PasswordRequirementsModal from "../components/common/PasswordRequirementsModal";
import PasswordInput from "../components/common/PasswordInput";
import { resetPassword } from "../api/authApi";
import { Info } from "lucide-react";
import "../styles/AuthLayout.css";

function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPasswordHint, setShowPasswordHint] = useState(false);

  useEffect(() => {
    setPassword("");
    setConfirmPassword("");
  }, [token]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      setModal({ title: "Erreur", message: "Les mots de passe ne correspondent pas." });
      return;
    }
    setLoading(true);
    try {
      await resetPassword({ token, password });
      setPassword("");
      setConfirmPassword("");
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

      {showPasswordHint && (
        <PasswordRequirementsModal onClose={() => setShowPasswordHint(false)} />
      )}

      <div className="auth-card">
        <h1 className="auth-card-title">Réinitialiser le mot de passe</h1>

        <form onSubmit={handleSubmit} autoComplete="off" noValidate>
          <div className="auth-field">
            <label className="auth-label" htmlFor="reset-new-password">
              Nouveau mot de passe<span className="auth-label-required">*</span>
            </label>
            <PasswordInput
              id="reset-new-password"
              name="reset-new-password"
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
            <label className="auth-label" htmlFor="reset-confirm-password">
              Confirmer le mot de passe<span className="auth-label-required">*</span>
            </label>
            <PasswordInput
              id="reset-confirm-password"
              name="reset-confirm-password"
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
