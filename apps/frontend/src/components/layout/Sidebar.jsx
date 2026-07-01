// Mobile/collapsible version of the main navigation, shown via the hamburger button
// in Layout. Mirrors the same nav items as the desktop header.
import { useContext } from "react";
import { NavLink } from "react-router-dom";
import {
  Home,
  User,
  ClipboardList,
  UserPlus,
  Users,
  LogOut,
  X,
} from "lucide-react";
import { AuthContext } from "../../contexts/AuthContext";


const nav_items = [
  { to: "/", label: "Accueil", icon: Home, end: true },
  { to: "/profile", label: "Profil", icon: User },
];

const manager_items = [
  { to: "/missions/new", label: "Création de mission", icon: ClipboardList, end: true },
  { to: "/users/new", label: "Création d'utilisateur", icon: UserPlus, end: true },
];

const admin_items = [
  { to: "/users", label: "Liste des utilisateurs", icon: Users, end: true },
];

// isOpen/onClose are controlled by the parent Layout; this component holds no open/close state itself.
function Sidebar({ isOpen, onClose, onLogout }) {
  const { user } = useContext(AuthContext);

  const isManager = user?.role === "responsable" || user?.role === "admin";
  const isAdmin = user?.role === "admin";

  const handleLogoutClick = () => {
    onClose();
    onLogout();
  };

  // Build the final menu by combining the base items with role-specific ones.
  const allItems = [
    ...nav_items,
    ...(isManager ? manager_items : []),
    ...(isAdmin ? admin_items : []),
  ];

  return (
    <>
      {isOpen && (
        <div className="sidebar-overlay" onClick={onClose} aria-hidden="true" />
      )}

      <nav className={`sidebar ${isOpen ? "sidebar--open" : ""}`} aria-label="Navigation principale">
        <div className="sidebar-header">
          <button className="sidebar-close" onClick={onClose} aria-label="Fermer le menu">
            <X size={18} />
          </button>
          <span className="sidebar-logo">CADRI</span>
        </div>

        <ul className="sidebar-nav" role="list">
          {allItems.map(({ to, label, icon: Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  "sidebar-link" + (isActive ? " sidebar-link--active" : "")
                }
                onClick={onClose}
              >
                <Icon size={20} className="sidebar-link-icon" aria-hidden="true" />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="sidebar-footer">
          <button className="sidebar-link sidebar-logout" onClick={handleLogoutClick}>
            <LogOut size={20} className="sidebar-link-icon" aria-hidden="true" />
            Déconnexion
          </button>
        </div>
      </nav>
    </>
  );
}

export default Sidebar;