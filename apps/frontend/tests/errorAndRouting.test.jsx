import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import ErrorPage from '../src/pages/ErrorPage';
import ProtectedRoute from '../src/components/common/ProtectedRoute';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const DummyPage = () => <div>Page protégée</div>;

const renderProtected = ({ isAuthenticated = false, role = 'agent', requiredRole = null } = {}) =>
  render(
    <AuthContext.Provider value={{ user: isAuthenticated ? { role } : null, loading: false }}>
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
          <Route path="/login" element={<div>Page de connexion</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );

// ---------------------------------------------------------------------------
// ErrorPage
// ---------------------------------------------------------------------------
describe('ErrorPage', () => {
  test('affiche un message "page introuvable" par défaut (404)', () => {
    render(<MemoryRouter><ErrorPage /></MemoryRouter>);
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText(/cette page n'existe pas/i)).toBeInTheDocument();
  });

  test('affiche un message "accès refusé" quand la prop code vaut 403', () => {
    render(<MemoryRouter><ErrorPage code={403} /></MemoryRouter>);
    expect(screen.getByText('403')).toBeInTheDocument();
    expect(screen.getByText('Accès refusé')).toBeInTheDocument();
  });

  test('affiche un lien de retour à l\'accueil', () => {
    render(<MemoryRouter><ErrorPage /></MemoryRouter>);
    expect(screen.getByRole('link', { name: /retour à l'accueil/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ProtectedRoute — authentication
// ---------------------------------------------------------------------------
describe('ProtectedRoute — authentification', () => {
  test('redirige vers /login quand l\'utilisateur n\'est pas authentifié', () => {
    renderProtected({ isAuthenticated: false });
    expect(screen.getByText(/page de connexion/i)).toBeInTheDocument();
    expect(screen.queryByText(/page protégée/i)).not.toBeInTheDocument();
  });

  test('affiche la page quand l\'utilisateur est authentifié', () => {
    renderProtected({ isAuthenticated: true });
    expect(screen.getByText(/page protégée/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ProtectedRoute — role-based access
// ---------------------------------------------------------------------------
describe('ProtectedRoute — accès par rôle', () => {
  test('bloque l\'accès et affiche "Accès refusé" si le rôle est insuffisant', () => {
    renderProtected({ isAuthenticated: true, role: 'agent', requiredRole: 'admin' });
    expect(screen.queryByText(/page protégée/i)).not.toBeInTheDocument();
    expect(screen.getByText('403')).toBeInTheDocument();
    expect(screen.getByText('Accès refusé')).toBeInTheDocument();
  });

  test('autorise l\'accès quand le rôle correspond exactement', () => {
    renderProtected({ isAuthenticated: true, role: 'admin', requiredRole: 'admin' });
    expect(screen.getByText(/page protégée/i)).toBeInTheDocument();
  });

  test('autorise l\'accès quand le rôle de l\'utilisateur est supérieur au rôle requis', () => {
    renderProtected({ isAuthenticated: true, role: 'admin', requiredRole: 'agent' });
    expect(screen.getByText(/page protégée/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Unknown routes
// ---------------------------------------------------------------------------
describe('Routes inconnues', () => {
  test('une route inconnue affiche la page 404', () => {
    render(
      <AuthContext.Provider value={{ user: { role: 'agent' }, loading: false }}>
        <MemoryRouter initialEntries={['/this-route-does-not-exist']}>
          <Routes>
            <Route path="*" element={<ErrorPage />} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
    expect(screen.getByText('404')).toBeInTheDocument();
  });
});