import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';

import ProfilePage from '../src/pages/ProfilePage';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Mock data — raw backend shape (snake_case), as returned by GET /me and
// normalized by profileApi.js.
// ---------------------------------------------------------------------------
const PROFILE_MOCK = {
  id: '1',
  first_name: 'Jean',
  last_name: 'Dupont',
  email: 'jean.dupont@cadri.fr',
  role: { name: 'agent', label: 'Agent' },
  service: { name: 'electrique', label: 'Électrique' },
};

function mockFetchRoutes({ profile = PROFILE_MOCK } = {}) {
  global.fetch = vi.fn((url, options = {}) => {
    const path = String(url);
    const method = options.method || 'GET';

    if (path.endsWith('/change-password') && method === 'PATCH') {
      return Promise.resolve({ ok: true, json: async () => ({}) });
    }
    if (path.endsWith('/me') && method === 'PATCH') {
      return Promise.resolve({ ok: true, json: async () => ({ user: profile }) });
    }
    if (path.endsWith('/me') && method === 'GET') {
      return Promise.resolve({ ok: true, json: async () => profile });
    }
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
}

const renderProfile = (logout = vi.fn(), profile = PROFILE_MOCK) => {
  mockFetchRoutes({ profile });
  return render(
    <AuthContext.Provider value={{ user: { role: 'agent', id: '1' }, logout }}>
      <MemoryRouter><ProfilePage /></MemoryRouter>
    </AuthContext.Provider>
  );
};

const openEditMode = async () => {
  await waitFor(() => screen.getByText('Modifier le profil'));
  fireEvent.click(screen.getByText('Modifier le profil'));
};

// Renders ProfilePage behind an actual /profile -> /login route pair, so
// tests can assert on the real post-password-change redirect instead of
// just checking that `logout` was called.
const renderProfileWithRouting = ({ logout = vi.fn(), profile = PROFILE_MOCK, fetchOverride } = {}) => {
  if (fetchOverride) {
    global.fetch = fetchOverride;
  } else {
    mockFetchRoutes({ profile });
  }
  return render(
    <AuthContext.Provider value={{ user: { role: 'agent', id: '1' }, logout }}>
      <MemoryRouter initialEntries={['/profile']}>
        <Routes>
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/login" element={<div>Page de connexion</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

const fillPasswordChangeFields = () => {
  fireEvent.change(screen.getByLabelText(/mot de passe actuel/i), {
    target: { value: 'AncienPass123!' },
  });
  fireEvent.change(screen.getByLabelText(/^nouveau mot de passe/i), {
    target: { value: 'NouveauPass123!' },
  });
  fireEvent.change(screen.getByLabelText(/confirmer le nouveau mot de passe/i), {
    target: { value: 'NouveauPass123!' },
  });
};

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
describe('ProfilePage — affichage', () => {
  test('affiche les informations personnelles de l\'utilisateur', async () => {
    renderProfile();
    await waitFor(() => {
      expect(screen.getByText('Jean')).toBeInTheDocument();
      expect(screen.getByText('Dupont')).toBeInTheDocument();
      expect(screen.getByText('jean.dupont@cadri.fr')).toBeInTheDocument();
    });
  });

  test('le bouton "Déconnexion" est un bouton distinct (style outline), pas un simple lien', async () => {
    renderProfile();
    await waitFor(() => {
      expect(document.querySelector('.profile-actions .profile-btn-cancel')).toBeInTheDocument();
    });
    expect(document.querySelector('.profile-actions .profile-btn-cancel').tagName).toBe('BUTTON');
  });
});

// ---------------------------------------------------------------------------
// General settings
// ---------------------------------------------------------------------------
describe('ProfilePage — informations générales', () => {
  test('le formulaire est pré-rempli avec les données actuelles en mode édition', async () => {
    renderProfile();
    await openEditMode();
    expect(screen.getByLabelText(/^nom/i)).toHaveValue('Dupont');
    expect(screen.getByLabelText(/prénom/i)).toHaveValue('Jean');
  });

  test('enregistrer les modifications appelle l\'API PATCH /me', async () => {
    renderProfile();
    await openEditMode();

    fireEvent.change(screen.getByLabelText(/^nom/i), { target: { value: 'Durand' } });
    fireEvent.click(screen.getByRole('button', { name: /mettre à jour le profil/i }));

    await waitFor(() => {
      const patchCall = global.fetch.mock.calls.find(
        ([url, options]) => String(url).endsWith('/me') && options?.method === 'PATCH'
      );
      expect(patchCall).toBeTruthy();
    });
  });

  test('"Annuler" referme le formulaire sans enregistrer', async () => {
    renderProfile();
    await openEditMode();
    fireEvent.click(screen.getByRole('button', { name: /annuler/i }));
    await waitFor(() => {
      expect(screen.queryByLabelText(/^nom/i)).not.toBeInTheDocument();
      expect(screen.getByText('Modifier le profil')).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// Password change
// ---------------------------------------------------------------------------
describe('ProfilePage — changement de mot de passe', () => {
  test('affiche les champs mot de passe actuel, nouveau et confirmation', async () => {
    renderProfile();
    await openEditMode();
    expect(screen.getByLabelText(/mot de passe actuel/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^nouveau mot de passe/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmer le nouveau mot de passe/i)).toBeInTheDocument();
  });

  test('cliquer sur l\'icône info ouvre la pop-up des exigences du mot de passe', async () => {
    renderProfile();
    await openEditMode();
    const infoButtons = screen.getAllByLabelText(/voir les exigences du mot de passe/i);
    fireEvent.click(infoButtons[0]);
    await waitFor(() => {
      expect(screen.getByText(/exigences du mot de passe/i)).toBeInTheDocument();
    });
  });

  test("refuse l'enregistrement si les nouveaux mots de passe ne correspondent pas", async () => {
    renderProfile();
    await openEditMode();

    fireEvent.change(screen.getByLabelText(/^nouveau mot de passe/i), {
      target: { value: "Password123!" },
    });

    fireEvent.change(
      screen.getByLabelText(/confirmer le nouveau mot de passe/i),
      {
        target: { value: "AutrePassword123!" },
      }
    );

    fireEvent.click(
      screen.getByRole("button", { name: /mettre à jour le profil/i })
    );

    expect(
      await screen.findByText(/les mots de passe ne correspondent pas/i)
    ).toBeInTheDocument();
  });

  test("refuse le changement de mot de passe si le mot de passe actuel est vide", async () => {
    renderProfile();
    await openEditMode();

    fireEvent.change(screen.getByLabelText(/^nouveau mot de passe/i), {
      target: { value: "Password123!" },
    });

    fireEvent.change(
      screen.getByLabelText(/confirmer le nouveau mot de passe/i),
      {
        target: { value: "Password123!" },
      }
    );

    fireEvent.click(
      screen.getByRole("button", { name: /mettre à jour le profil/i })
    );

    expect(
      await screen.findByText(/mot de passe actuel est obligatoire/i)
    ).toBeInTheDocument();
  });

  test('changement de mot de passe réussi : PATCH /me puis PATCH /auth/change-password, session locale terminée, redirection vers /login', async () => {
    const logoutMock = vi.fn();
    renderProfileWithRouting({ logout: logoutMock });
    await openEditMode();

    fillPasswordChangeFields();
    fireEvent.click(screen.getByRole('button', { name: /mettre à jour le profil/i }));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalled();
    });

    const calls = global.fetch.mock.calls;
    const meIndex = calls.findIndex(
      ([url, options]) => String(url).endsWith('/me') && options?.method === 'PATCH'
    );
    const changePasswordIndex = calls.findIndex(
      ([url, options]) => String(url).endsWith('/change-password') && options?.method === 'PATCH'
    );

    // The profile update must happen while the session is still valid,
    // strictly before the request that revokes it.
    expect(meIndex).toBeGreaterThanOrEqual(0);
    expect(changePasswordIndex).toBeGreaterThan(meIndex);

    // No authenticated /me request may follow the successful password change.
    const meCallsAfterPasswordChange = calls.filter(
      ([url, options], index) => index > changePasswordIndex && String(url).endsWith('/me')
    );
    expect(meCallsAfterPasswordChange).toHaveLength(0);

    await waitFor(() => {
      expect(screen.getByText(/page de connexion/i)).toBeInTheDocument();
    });
  });

  test("échec du changement de mot de passe : ne déconnecte pas, ne redirige pas, affiche l'erreur", async () => {
    const logoutMock = vi.fn();
    const fetchOverride = vi.fn((url, options = {}) => {
      const path = String(url);
      const method = options.method || 'GET';

      if (path.endsWith('/change-password') && method === 'PATCH') {
        return Promise.resolve({
          ok: false,
          status: 403,
          json: async () => ({ message: 'Mot de passe actuel incorrect.' }),
        });
      }
      if (path.endsWith('/me') && method === 'PATCH') {
        return Promise.resolve({ ok: true, json: async () => ({ user: PROFILE_MOCK }) });
      }
      if (path.endsWith('/me') && method === 'GET') {
        return Promise.resolve({ ok: true, json: async () => PROFILE_MOCK });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    renderProfileWithRouting({ logout: logoutMock, fetchOverride });
    await openEditMode();

    fillPasswordChangeFields();
    fireEvent.click(screen.getByRole('button', { name: /mettre à jour le profil/i }));

    expect(await screen.findByText(/mot de passe actuel incorrect/i)).toBeInTheDocument();
    expect(logoutMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/page de connexion/i)).not.toBeInTheDocument();
    // The form is still there and usable, so the user can retry.
    expect(screen.getByLabelText(/mot de passe actuel/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Logout
// ---------------------------------------------------------------------------
describe('ProfilePage — déconnexion', () => {
  const getProfileLogoutButton = () => document.querySelector('.profile-actions .profile-btn-cancel');

  test('cliquer sur Déconnexion ouvre la pop-up de confirmation', async () => {
    renderProfile();
    await waitFor(() => expect(getProfileLogoutButton()).toBeInTheDocument());
    fireEvent.click(getProfileLogoutButton());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/êtes-vous sûr de vouloir vous déconnecter/i)).toBeInTheDocument();
  });

  test('confirmer la déconnexion appelle le handler logout', async () => {
    const logoutMock = vi.fn();
    renderProfile(logoutMock);
    await waitFor(() => expect(getProfileLogoutButton()).toBeInTheDocument());
    fireEvent.click(getProfileLogoutButton());

    const dialog = screen.getByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: /^oui$/i }));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalled();
    });
  });

  test('"Non" referme la pop-up sans déconnecter', async () => {
    const logoutMock = vi.fn();
    renderProfile(logoutMock);
    await waitFor(() => expect(getProfileLogoutButton()).toBeInTheDocument());
    fireEvent.click(getProfileLogoutButton());

    const dialog = screen.getByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: /^non$/i }));

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    expect(logoutMock).not.toHaveBeenCalled();
  });
});
