import { useState, useContext } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import Sidebar from "./Sidebar";
import { AuthContext } from "../../contexts/AuthContext";
import logo from "../../assets/logo.png";
import "../../styles/Layout.css";


const nav_items = [
  { to: "/", label: "Accueil", end: true },
  { to: "/profile", label: "Profil" },
];

const manager_items = [
  { to: "/missions/new", label: "Création de mission" },
  { to: "/users/new", label: "Création d'utilisateur" },
];

const admin_items = [
  { to: "/users", label: "Liste des utilisateurs" },
];

function LogoutModal({ onConfirm, onCancel }) {
  return (
    <div className="logout-modal-overlay" role="dialog" aria-modal="true">
      <div className="logout-modal">
        <div className="logout-modal-header">
          <span className="logout-modal-title">Déconnexion</span>
          <button className="logout-modal-close" onClick={onCancel} aria-label="Fermer">✕</button>
        </div>
        <div className="logout-modal-body">
          Êtes-vous sûr de vouloir vous déconnecter ?
        </div>
        <div className="logout-modal-footer">
          <button className="logout-modal-cancel" onClick={onCancel}>Non</button>
          <button className="logout-modal-confirm" onClick={onConfirm}>Oui</button>
        </div>
      </div>
    </div>
  );
}

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useContext(AuthContext);

  const isManager = user?.role === "responsable" || user?.role === "admin";
  const isAdmin = user?.role === "admin";

  const handleLogoutConfirm = () => {
    setLogoutOpen(false);
    logout();
    navigate("/login");
  };

  return (
    <div className="intranet-shell">

      {logoutOpen && (
        <LogoutModal
          onConfirm={handleLogoutConfirm}
          onCancel={() => setLogoutOpen(false)}
        />
      )}

      <header className="intranet-header">
        <button
          className="intranet-hamburger"
          onClick={() => setSidebarOpen(true)}
          aria-label="Ouvrir le menu"
          aria-expanded={sidebarOpen}
        >
          ☰
        </button>

        <span className="intranet-logo">
          <img src={logo} alt="" className="intranet-logo-image" />
          CADRI
        </span>

        <nav className="intranet-nav" aria-label="Navigation principale">
          {nav_items.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                "intranet-nav-link" + (isActive ? " intranet-nav-link--active" : "")
              }
            >
              {label}
            </NavLink>
          ))}

          {isManager && manager_items.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                "intranet-nav-link" + (isActive ? " intranet-nav-link--active" : "")
              }
            >
              {label}
            </NavLink>
          ))}

          {isAdmin && admin_items.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                "intranet-nav-link" + (isActive ? " intranet-nav-link--active" : "")
              }
            >
              {label}
            </NavLink>
          ))}

          <button
            className="intranet-nav-link intranet-logout"
            onClick={() => setLogoutOpen(true)}
          >
            Déconnexion
          </button>
        </nav>
      </header>

      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onLogout={() => setLogoutOpen(true)}
      />

      <main className="intranet-main">
        {children}
      </main>

      <footer className="intranet-footer">
        <a href="/mentions-legales">Mentions légales</a>
        <span className="intranet-footer-dot" aria-hidden="true" />
        <span>© 2026 CADRI. Tous droits réservés.</span>
      </footer>

    </div>
  );
}

export default Layout;
