# Frontend Tests — Cadri Intranet

Test suite using Vitest + React Testing Library, covering all pages of the intranet.

## Project structure

```
frontend/
├── src/
│   ├── pages/
│   ├── components/
│   └── contexts/
├── tests/
│   ├── auth.test.jsx
│   ├── dashboard.test.jsx
│   ├── missions.test.jsx
│   ├── users.test.jsx
│   ├── profile.test.jsx
│   └── errorAndRouting.test.jsx
├── vitest.config.js
├── vitest.setup.js
└── package.json
```

## Setup
### Install dependencies

```bash
npm install -D \
  vitest \
  @vitest/ui \
  @vitest/coverage-v8 \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  jsdom
```

## Running tests

```bash
# Run all tests once
npm test

# Watch mode (re-runs on file save)
npm run test:watch

# Coverage report
npm run test:coverage

# Browser UI
npm run test:ui
```

## Expected file paths

The tests assume the following structure in your project:

| Test import                        | Expected path in your project       |
|------------------------------------|-------------------------------------|
| `../src/pages/LoginPage`           | `src/pages/LoginPage.jsx`           |
| `../src/pages/ForgotPasswordPage`  | `src/pages/ForgotPasswordPage.jsx`  |
| `../src/pages/ResetPasswordPage`   | `src/pages/ResetPasswordPage.jsx`   |
| `../src/pages/ActivateAccountPage` | `src/pages/ActivateAccountPage.jsx` |
| `../src/pages/DashboardPage`       | `src/pages/DashboardPage.jsx`       |
| `../src/pages/MissionDetailPage`   | `src/pages/MissionDetailPage.jsx`   |
| `../src/pages/MissionFormPage`     | `src/pages/MissionFormPage.jsx`     |
| `../src/pages/UserManagementPage`  | `src/pages/UserManagementPage.jsx`  |
| `../src/pages/UserFormPage`        | `src/pages/UserFormPage.jsx`        |
| `../src/pages/ProfilePage`         | `src/pages/ProfilePage.jsx`         |
| `../src/pages/ErrorPage`           | `src/pages/ErrorPage.jsx`           |
| `../src/components/common/ProtectedRoute` | `src/components/common/ProtectedRoute.jsx` |
| `../src/contexts/AuthContext`      | `src/contexts/AuthContext.jsx`      |

Update the import paths if your folder structure differs.

Note: the UI is in French, so all test assertions target the actual French
labels and button text rendered by the app (e.g. "Se connecter", "Titre",
"Statut", "Supprimer la mission") rather than English placeholders.

## Coverage

| File                         | Tests | Scope                                                   |
|------------------------------|-------|---------------------------------------------------------|
| `auth.test.jsx`              | 13    | Login, error states, forgot/reset password, activation  |
| `dashboard.test.jsx`         | 9     | Rendering, filters, navigation, pagination, badges       |
| `missions.test.jsx`          | 16    | Detail view, create/edit form, role restrictions, delete |
| `users.test.jsx`             | 15    | List, filters, create/view/edit/delete, role restrictions |
| `profile.test.jsx`           | 12    | Rendering, settings, password change, logout            |
| `errorAndRouting.test.jsx`   | 9     | 404/403 pages, ProtectedRoute, unknown routes           |
| **Total**                    | **74**|                                                         |