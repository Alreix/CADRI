import { BrowserRouter, Routes, Route } from "react-router-dom";

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

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/activate" element={<ActivateAccountPage />} />

        <Route path="/" element={<DashboardPage />} />
        <Route path="/missions/new" element={<MissionFormPage />} />
        <Route path="/missions/:id" element={<MissionDetailPage />} />
        <Route path="/missions/:id/edit" element={<MissionFormPage />} />
        <Route path="/users" element={<UserManagementPage />} />
        <Route path="/users/new" element={<UserFormPage />} />
        <Route path="/users/:id/edit" element={<UserFormPage />} />
        <Route path="/profile" element={<ProfilePage />} />

        <Route path="*" element={<ErrorPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
