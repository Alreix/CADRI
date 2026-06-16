import { useState } from "react";
import { Link } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import { requestPasswordReset } from "../api/authApi";
import "../styles/AuthLayout.css";

function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await requestPasswordReset({ email });
      setSubmitted(true);
    } catch (err) {
      setError(err.message || "Une erreur s'est produite. Veuillez réessayer.");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <AuthLayout>
        <div className="auth-card">
          <div className="auth-icon-circle" aria-hidden="true">✉</div>
          <h1 className="auth-card-title">Lien envoyé !</h1>
          <p className="auth-card-subtitle">
            Un lien de réinitialisation a été envoyé à <strong>{email}</strong>.
            Vérifiez votre boîte de réception.
          </p>
          <Link to="/connexion" className="auth-back-link">
            Retour à la connexion
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="auth-card">
        <div className="auth-icon-circle" aria-hidden="true">✉</div>

        <h1 className="auth-card-title">Mot de passe oublié ?</h1>
        <p className="auth-card-subtitle">
          Entrez votre adresse email et nous vous enverrons
          un lien pour réinitialiser votre mot de passe.
        </p>

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

          {error && (
            <p style={{ color: "var(--auth-required)", fontSize: "0.875rem", marginBottom: "12px" }}>
              {error}
            </p>
          )}

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Envoi…" : "Envoyer le lien"}
          </button>
        </form>

        <Link to="/connexion" className="auth-back-link">
          Retour à la connexion
        </Link>
      </div>
    </AuthLayout>
  );
}

export default ForgotPasswordPage;