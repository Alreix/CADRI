// Central route table: maps each URL to a page component.
// Routes wrapped in ProtectedRoute require authentication, and optionally a minimum role.
import { RouterProvider, createBrowserRouter } from "react-router-dom";

import ProtectedRoute from "../components/common/ProtectedRoute";

import LoginPage from "../pages/LoginPage";
import ForgotPasswordPage from "../pages/ForgotPasswordPage";
import ResetPasswordPage from "../pages/ResetPasswordPage";
import ActivateAccountPage from "../pages/ActivateAccountPage";
import DashboardPage from "../pages/DashboardPage";
import MissionDetailPage from "../pages/MissionDetailPage";
import MissionFormPage from "../pages/MissionFormPage";
import UserManagementPage from "../pages/UserManagementPage";
import UserFormPage from "../pages/UserFormPage";
import ProfilePage from "../pages/ProfilePage";
import ErrorPage from "../pages/ErrorPage";

const router = createBrowserRouter([
  // Public routes (no authentication required). French aliases are kept for user-facing URLs.
  { path: "/login", element: <LoginPage />, errorElement: <ErrorPage /> },
  { path: "/connexion", element: <LoginPage />, errorElement: <ErrorPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage />, errorElement: <ErrorPage /> },
  { path: "/mot-de-passe-oublie", element: <ForgotPasswordPage />, errorElement: <ErrorPage /> },
  { path: "/reset-password", element: <ResetPasswordPage />, errorElement: <ErrorPage /> },
  { path: "/activate", element: <ActivateAccountPage />, errorElement: <ErrorPage /> },

  // Routes available to any authenticated user, regardless of role.
  { path: "/", element: <ProtectedRoute><DashboardPage /></ProtectedRoute>, errorElement: <ErrorPage /> },
  { path: "/missions", element: <ProtectedRoute><DashboardPage /></ProtectedRoute>, errorElement: <ErrorPage /> },
  { path: "/profile", element: <ProtectedRoute><ProfilePage /></ProtectedRoute>, errorElement: <ErrorPage /> },

  // Mission routes: creation requires "responsable", edit only requires being logged in
  // (the page itself further restricts which fields an agent vs a manager can change).
  { path: "/missions/new", element: <ProtectedRoute requiredRole="responsable"><MissionFormPage /></ProtectedRoute>, errorElement: <ErrorPage /> },
  { path: "/missions/:id", element: <ProtectedRoute><MissionDetailPage /></ProtectedRoute>, errorElement: <ErrorPage /> },
  { path: "/missions/:id/edit", element: <ProtectedRoute requiredRole="agent"><MissionFormPage mode="edit" /></ProtectedRoute>, errorElement: <ErrorPage /> },

  // User management routes: listing and viewing require "admin", creation only requires "responsable".
  { path: "/users", element: <ProtectedRoute requiredRole="admin"><UserManagementPage /></ProtectedRoute>, errorElement: <ErrorPage /> },
  { path: "/users/new", element: <ProtectedRoute requiredRole="responsable"><UserFormPage mode="create" /></ProtectedRoute>, errorElement: <ErrorPage /> },
  { path: "/users/:id", element: <ProtectedRoute requiredRole="admin"><UserFormPage mode="view" /></ProtectedRoute>, errorElement: <ErrorPage /> },
  { path: "/users/:id/edit", element: <ProtectedRoute requiredRole="admin"><UserFormPage mode="edit" /></ProtectedRoute>, errorElement: <ErrorPage /> },

  // Fallback route: anything that doesn't match above renders the error page.
  { path: "*", element: <ErrorPage />, errorElement: <ErrorPage /> },
]);

function AppRouter() {
  return <RouterProvider router={router} />;
}

export default AppRouter;
