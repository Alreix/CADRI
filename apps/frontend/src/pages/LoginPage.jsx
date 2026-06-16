import { useState, useContext } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import Modal from "../components/common/Modal";
import { AuthContext } from "../contexts/AuthContext";
import { login as loginApi } from "../api/authApi";
import "../styles/AuthLayout.css";

function LoginPage() {
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const userData = await loginApi({ email, password });
      login(userData);
      navigate("/");
    } catch (err) {
      setModal({
        title: "Erreur de connexion",
        message: err.message || "Mot de passe erroné",
      });
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

      <div className="auth-card">
        <h1 className="auth-card-title">Connexion à CADRI</h1>

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
              Mot de passe<span className="auth-label-required">*</span>
            </label>
            <input
              id="password"
              type="password"
              className="auth-input"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <Link to="/forgot-password" className="auth-forgot-link">
            Mot de passe oublié ?
          </Link>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </div>
    </AuthLayout>
  );
}

export default LoginPage;
