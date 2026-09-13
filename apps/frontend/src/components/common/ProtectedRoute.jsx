// Route guard: blocks access to a page unless the user is logged in,
// and optionally unless they hold a sufficient role.
// Note: this is a UX convenience only — the backend always re-checks permissions.
import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../../contexts/AuthContext";
import ErrorPage from "../../pages/ErrorPage";

// Numeric hierarchy used to compare roles (higher number = more privileges).
const role_levels = {
  agent: 1,
  responsable: 2,
  admin: 3,
};

function ProtectedRoute({ children, requiredRole = null }) {
  const { user, loading } = useContext(AuthContext);

  // Still checking the session (see AuthContext): render nothing visible yet
  // to avoid a flash, but still announce it for screen reader users in case
  // the check takes a moment (e.g. a slow network).
  if (loading) return <p role="status" className="sr-only">Chargement…</p>;

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const userLevel = role_levels[user.role] || 0;
    const requiredLevel = role_levels[requiredRole] || 0;
    if (userLevel < requiredLevel) {
      return <ErrorPage code={403} />;
    }
  }

  return children;
}

export default ProtectedRoute;