import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import ErrorPage from '../src/pages/ErrorPage';
import ProtectedRoute from '../src/components/ProtectedRoute';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const DummyPage = () => <div>Protected page</div>;

const renderProtected = ({ isAuthenticated = false, role = 'agent', requiredRole = null } = {}) =>
  render(
    <AuthContext.Provider value={{ user: isAuthenticated ? { role } : null }}>
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute requiredRole={requiredRole}>
                <DummyPage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login page</div>} />
          <Route path="/403"   element={<ErrorPage code={403} />} />
          <Route path="/404"   element={<ErrorPage code={404} />} />
          <Route path="*"      element={<ErrorPage code={404} />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );

// ---------------------------------------------------------------------------
// ErrorPage
// ---------------------------------------------------------------------------
describe('ErrorPage', () => {
  test('renders 404 code and a descriptive message', () => {
    render(<MemoryRouter><ErrorPage code={404} /></MemoryRouter>);
    expect(screen.getByText(/404/)).toBeInTheDocument();
    expect(screen.getByText(/page not found/i)).toBeInTheDocument();
  });

  test('renders 403 code and a descriptive message', () => {
    render(<MemoryRouter><ErrorPage code={403} /></MemoryRouter>);
    expect(screen.getByText(/403/)).toBeInTheDocument();
    expect(screen.getByText(/access denied|forbidden/i)).toBeInTheDocument();
  });

  test('renders a back button pointing to the Dashboard or previous page', () => {
    render(<MemoryRouter><ErrorPage code={404} /></MemoryRouter>);
    expect(
      screen.queryByRole('link',   { name: /back|dashboard|home/i }) ||
      screen.queryByRole('button', { name: /back|dashboard|home/i })
    ).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ProtectedRoute — authentication
// ---------------------------------------------------------------------------
describe('ProtectedRoute — authentication', () => {
  test('redirects to /login when the user is not authenticated', () => {
    renderProtected({ isAuthenticated: false });
    expect(screen.getByText(/login page/i)).toBeInTheDocument();
    expect(screen.queryByText(/protected page/i)).not.toBeInTheDocument();
  });

  test('renders the page when the user is authenticated', () => {
    renderProtected({ isAuthenticated: true });
    expect(screen.getByText(/protected page/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ProtectedRoute — role-based access
// ---------------------------------------------------------------------------
describe('ProtectedRoute — role-based access', () => {
  test('blocks access and redirects when the role is insufficient', () => {
    renderProtected({ isAuthenticated: true, role: 'agent', requiredRole: 'admin' });
    expect(screen.queryByText(/protected page/i)).not.toBeInTheDocument();
  });

  test('grants access when the role matches the requirement', () => {
    renderProtected({ isAuthenticated: true, role: 'admin', requiredRole: 'admin' });
    expect(screen.getByText(/protected page/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Unknown routes
// ---------------------------------------------------------------------------
describe('Unknown routes', () => {
  test('an unknown route renders the 404 ErrorPage', () => {
    render(
      <AuthContext.Provider value={{ user: { role: 'agent' } }}>
        <MemoryRouter initialEntries={['/this-route-does-not-exist']}>
          <Routes>
            <Route path="*" element={<ErrorPage code={404} />} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
    expect(screen.getByText(/404/)).toBeInTheDocument();
  });
});
