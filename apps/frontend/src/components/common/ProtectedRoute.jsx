import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../../contexts/AuthContext";
import ErrorPage from "../../pages/ErrorPage";

const role_levels = {
  agent: 1,
  responsable: 2,
  admin: 3,
};

function ProtectedRoute({ children, requiredRole = null }) {
  const { user, loading } = useContext(AuthContext);

  if (loading) return null;

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