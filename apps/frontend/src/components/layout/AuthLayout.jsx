
import logo from "../../assets/logo.png";

function AuthLayout({ children }) {
  return (
    <div className="auth-shell">
      <header className="auth-header">
        <span className="auth-header-logo">
          <img src={logo} alt="CADRI" className="auth-logo-image" />
          CADRI
        </span>
      </header>

      <main className="auth-body">
        {children}
      </main>

      <footer className="auth-footer">
        <a href="/mentions-legales">Mentions légales</a>
        <span className="auth-footer-dot" aria-hidden="true" />
        <span>© 2026 CADRI. Tous droits réservés.</span>
      </footer>
    </div>
  );
}

export default AuthLayout;