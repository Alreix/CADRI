// Regression tests for the apiClient <-> AuthContext session-expiration sync:
// when a protected request's automatic refresh-on-401 definitively fails,
// React state (AuthContext.user) must actually clear, not just the
// in-memory access token and the localStorage cache.
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';

import AuthProvider from '../src/contexts/AuthContext';
import ProtectedRoute from '../src/components/common/ProtectedRoute';
import { getAccessToken, clearAccessToken } from '../src/api/apiClient';

const DummyPage = () => <div>Page protégée</div>;

const CACHED_USER = {
  id: '1',
  firstName: 'Jean',
  lastName: 'Dupont',
  email: 'jean.dupont@cadri.fr',
  role: 'agent',
  service: 'Électrique',
};

const PROFILE_RESPONSE = {
  id: '1',
  first_name: 'Jean',
  last_name: 'Dupont',
  email: 'jean.dupont@cadri.fr',
  role: { name: 'agent', label: 'Agent' },
  service: { name: 'electrique', label: 'Électrique' },
};

const renderApp = () =>
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <DummyPage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Page de connexion</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );

beforeEach(() => {
  localStorage.clear();
  clearAccessToken();
});

describe('Synchronisation de session entre apiClient et AuthContext', () => {
  test('un refresh échoué après un 401 déconnecte réellement React (AuthContext.user devient null)', async () => {
    localStorage.setItem('cadri_user', JSON.stringify(CACHED_USER));

    global.fetch = vi.fn((url, options = {}) => {
      const path = String(url);
      const method = options.method || 'GET';

      if (path.endsWith('/me') && method === 'GET') {
        return Promise.resolve({
          ok: false,
          status: 401,
          json: async () => ({ msg: 'Token has expired' }),
        });
      }
      if (path.endsWith('/auth/refresh') && method === 'POST') {
        return Promise.resolve({
          ok: false,
          status: 401,
          json: async () => ({ msg: 'Refresh token is expired or invalid.' }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    renderApp();

    // Once /me -> refresh both definitively fail, React state itself (not
    // just localStorage/the in-memory token) must reflect the dead session.
    // (The transient optimistic render using the cached user, before /me
    // settles, resolves too fast under mocked fetch to reliably assert on.)
    await waitFor(() => {
      expect(screen.getByText(/page de connexion/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/page protégée/i)).not.toBeInTheDocument();
    expect(localStorage.getItem('cadri_user')).toBeNull();
    expect(getAccessToken()).toBeNull();
  });

  test('un refresh réussi ne déconnecte pas : la session et le rendu protégé sont conservés', async () => {
    localStorage.setItem('cadri_user', JSON.stringify(CACHED_USER));

    global.fetch = vi.fn((url, options = {}) => {
      const path = String(url);
      const method = options.method || 'GET';

      if (path.endsWith('/me') && method === 'GET') {
        const authHeader = options.headers?.Authorization;
        if (authHeader === 'Bearer new-access-token') {
          return Promise.resolve({ ok: true, json: async () => PROFILE_RESPONSE });
        }
        return Promise.resolve({
          ok: false,
          status: 401,
          json: async () => ({ msg: 'Token has expired' }),
        });
      }
      if (path.endsWith('/auth/refresh') && method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ access_token: 'new-access-token' }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    renderApp();

    await waitFor(() => {
      expect(screen.getByText(/page protégée/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/page de connexion/i)).not.toBeInTheDocument();
    expect(localStorage.getItem('cadri_user')).not.toBeNull();
    expect(getAccessToken()).toBe('new-access-token');
  });

  test("ne fait pas confiance à l'utilisateur en cache avant confirmation serveur : rien ne s'affiche tant que /me n'a pas répondu", async () => {
    localStorage.setItem('cadri_user', JSON.stringify(CACHED_USER));

    // Deliberately never-resolving until the test resolves it by hand, so we
    // can assert on the state while the very first /me call is still pending.
    let resolveMe;
    const mePromise = new Promise((resolve) => {
      resolveMe = resolve;
    });

    global.fetch = vi.fn((url, options = {}) => {
      const path = String(url);
      const method = options.method || 'GET';

      if (path.endsWith('/me') && method === 'GET') {
        return mePromise;
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    renderApp();

    // A cached user alone (no credential backing it anymore, since the
    // access token lives only in memory) must not unlock the protected UI.
    expect(screen.queryByText(/page protégée/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/page de connexion/i)).not.toBeInTheDocument();

    resolveMe({ ok: true, json: async () => PROFILE_RESPONSE });

    await waitFor(() => {
      expect(screen.getByText(/page protégée/i)).toBeInTheDocument();
    });
  });
});
