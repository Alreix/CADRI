import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';

import UserManagementPage from '../src/pages/UserManagementPage';
import UserFormPage from '../src/pages/UserFormPage';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Mock data — raw backend shapes (snake_case), as returned by the API and
// then normalized by usersApi.js.
// ---------------------------------------------------------------------------
const USERS_MOCK = [
  {
    id: '1',
    first_name: 'Jean',
    last_name: 'Dupont',
    email: 'jean.dupont@cadri.fr',
    role: { name: 'agent', label: 'Agent' },
    service: { id: 'svc1', name: 'electrique', label: 'Électrique' },
  },
  {
    id: '2',
    first_name: 'Claire',
    last_name: 'Martin',
    email: 'claire.martin@cadri.fr',
    role: { name: 'responsable', label: 'Responsable' },
    service: { id: 'svc2', name: 'travaux_publics', label: 'Travaux Publics' },
  },
  {
    id: '3',
    first_name: 'Paul',
    last_name: 'Durand',
    email: 'paul.durand@cadri.fr',
    role: { name: 'admin', label: 'Admin' },
    service: { id: 'svc1', name: 'electrique', label: 'Électrique' },
  },
];

const ROLES_MOCK = [
  { id: 'r1', name: 'agent', label: 'Agent' },
  { id: 'r2', name: 'responsable', label: 'Responsable' },
  { id: 'r3', name: 'admin', label: 'Admin' },
];

const SERVICES_MOCK = [
  { id: 'svc1', name: 'electrique', label: 'Électrique' },
  { id: 'svc2', name: 'travaux_publics', label: 'Travaux Publics' },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function mockFetchRoutes({ users = USERS_MOCK, user = USERS_MOCK[0], roles = ROLES_MOCK, services = SERVICES_MOCK } = {}) {
  global.fetch = vi.fn((url, options = {}) => {
    const path = String(url);
    const method = options.method || 'GET';

    if (path.includes('/metadata/roles')) {
      return Promise.resolve({ ok: true, json: async () => roles });
    }
    if (path.includes('/metadata/services')) {
      return Promise.resolve({ ok: true, json: async () => services });
    }
    if (path.match(/\/users\/[^/]+$/) && method === 'DELETE') {
      return Promise.resolve({ ok: true, json: async () => ({}) });
    }
    if (path.match(/\/users\/[^/]+$/) && method === 'PATCH') {
      return Promise.resolve({ ok: true, json: async () => ({ user }) });
    }
    if (path.match(/\/users\/[^/]+$/) && method === 'GET') {
      return Promise.resolve({ ok: true, json: async () => user });
    }
    if (path.endsWith('/users') && method === 'POST') {
      return Promise.resolve({ ok: true, json: async () => ({ user: { ...user, id: '99' } }) });
    }
    if (path.endsWith('/users') && method === 'GET') {
      return Promise.resolve({ ok: true, json: async () => users });
    }
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
}

const renderManagement = (role) => {
  mockFetchRoutes();
  return render(
    <AuthContext.Provider value={{ user: { role, id: '99' } }}>
      <MemoryRouter><UserManagementPage /></MemoryRouter>
    </AuthContext.Provider>
  );
};

const renderForm = (role, mode = 'create', userId = null, { user } = {}) => {
  mockFetchRoutes(user ? { user } : {});
  const route = userId ? `/users/${userId}/${mode}` : '/users/create';
  const path = userId ? `/users/:id/${mode}` : '/users/create';
  return render(
    <AuthContext.Provider value={{ user: { role, id: '99' } }}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path={path} element={<UserFormPage mode={mode} />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

// ---------------------------------------------------------------------------
// UserManagementPage — list
// ---------------------------------------------------------------------------
describe('UserManagementPage — liste', () => {
  test('affiche la liste des utilisateurs', async () => {
    renderManagement('admin');
    await waitFor(() => {
      expect(screen.getByText('Jean')).toBeInTheDocument();
      expect(screen.getByText('Dupont')).toBeInTheDocument();
      expect(screen.getByText('Claire')).toBeInTheDocument();
      expect(screen.getByText('Martin')).toBeInTheDocument();
    });
  });

  test('affiche le rôle de chaque utilisateur, capitalisé', async () => {
    renderManagement('admin');
    await waitFor(() => {
      expect(screen.getByText('Agent')).toBeInTheDocument();
      expect(screen.getByText('Responsable')).toBeInTheDocument();
    });
  });

  test('affiche un message quand aucun utilisateur ne correspond', async () => {
    mockFetchRoutes({ users: [] });
    render(
      <AuthContext.Provider value={{ user: { role: 'admin', id: '99' } }}>
        <MemoryRouter><UserManagementPage /></MemoryRouter>
      </AuthContext.Provider>
    );
    await waitFor(() => {
      expect(screen.getByText(/aucun utilisateur ne correspond/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// UserManagementPage — filters
// ---------------------------------------------------------------------------
describe('UserManagementPage — filtres', () => {
  test('cliquer sur le bouton Filtres ouvre le panneau de filtres', async () => {
    renderManagement('admin');
    await waitFor(() => screen.getByText('Jean'));
    fireEvent.click(screen.getByRole('button', { name: /filtres/i }));
    expect(screen.getByText('Filtrer les utilisateurs')).toBeInTheDocument();
  });

  test('filtrer par rôle "Agent" masque les autres rôles', async () => {
    renderManagement('admin');
    await waitFor(() => screen.getByText('Claire'));
    fireEvent.click(screen.getByRole('button', { name: /filtres/i }));
    fireEvent.change(screen.getByLabelText(/^rôle/i), { target: { value: 'agent' } });

    expect(screen.getByText('Jean')).toBeInTheDocument();
    expect(screen.queryByText('Claire')).not.toBeInTheDocument();
  });

  test('la recherche filtre par prénom ou nom', async () => {
    renderManagement('admin');
    await waitFor(() => screen.getByText('Jean'));
    fireEvent.change(screen.getByPlaceholderText(/rechercher des utilisateurs/i), {
      target: { value: 'martin' },
    });
    expect(screen.getByText('Claire')).toBeInTheDocument();
    expect(screen.queryByText('Jean')).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// UserFormPage — create
// ---------------------------------------------------------------------------
describe('UserFormPage — création (admin)', () => {
  test('affiche tous les champs requis', async () => {
    renderForm('admin', 'create');
    await waitFor(() => {
      expect(screen.getByLabelText(/^nom/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/prénom/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^rôle/i)).toBeInTheDocument();
    });
  });

  test('le rôle "Admin" est disponible dans la liste', async () => {
    renderForm('admin', 'create');
    await waitFor(() => screen.getByLabelText(/^rôle/i));
    const select = screen.getByLabelText(/^rôle/i);
    const options = Array.from(select.options).map((option) => option.value);
    expect(options).toContain('admin');
  });
});

describe('UserFormPage — création (responsable)', () => {
  test('le champ rôle ne propose pas "admin" et le titre devient "Créer un nouvel agent"', async () => {
    renderForm('responsable', 'create');
    await waitFor(() => {
      expect(screen.getByText('Créer un nouvel agent')).toBeInTheDocument();
    });
    // For a manager, the role field is locked to "agent" (read-only input),
    // not a <select>, so there is no list of options to assert against here.
    expect(screen.getByLabelText(/^rôle/i)).toHaveValue('Agent');
  });
});

// ---------------------------------------------------------------------------
// UserFormPage — view
// ---------------------------------------------------------------------------
describe('UserFormPage — profil utilisateur (lecture seule)', () => {
  test('affiche les informations utilisateur en lecture seule', async () => {
    renderForm('admin', 'view', '1', { user: USERS_MOCK[1] });
    await waitFor(() => {
      expect(screen.getByText('Profil utilisateur')).toBeInTheDocument();
      expect(screen.getByLabelText(/prénom/i)).toHaveValue('Claire');
    });
    expect(screen.queryByRole('button', { name: /valider|mettre à jour|créer/i })).not.toBeInTheDocument();
  });

  test('le rôle est affiché avec son libellé capitalisé, pas la valeur technique brute', async () => {
    renderForm('admin', 'view', '2', { user: USERS_MOCK[1] });
    await waitFor(() => {
      expect(screen.getByLabelText(/^rôle/i)).toHaveValue('Responsable');
    });
  });
});

// ---------------------------------------------------------------------------
// UserFormPage — edit
// ---------------------------------------------------------------------------
describe('UserFormPage — édition', () => {
  test('les champs sont pré-remplis avec les données existantes de l\'utilisateur', async () => {
    renderForm('admin', 'edit', '1', { user: USERS_MOCK[0] });
    await waitFor(() => {
      expect(screen.getByLabelText(/^nom/i)).toHaveValue('Dupont');
      expect(screen.getByLabelText(/^email/i)).toHaveValue('jean.dupont@cadri.fr');
    });
  });

  test('le bouton "Supprimer l\'utilisateur" est visible', async () => {
    renderForm('admin', 'edit', '1', { user: USERS_MOCK[0] });
    await waitFor(() => screen.getByLabelText(/^nom/i));
    expect(screen.getByRole('button', { name: /supprimer l'utilisateur/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// UserFormPage — delete
// ---------------------------------------------------------------------------
describe('UserFormPage — suppression', () => {
  test('cliquer sur Supprimer ouvre la pop-up de confirmation', async () => {
    renderForm('admin', 'edit', '1', { user: USERS_MOCK[0] });
    await waitFor(() => screen.getByLabelText(/^nom/i));
    fireEvent.click(screen.getByRole('button', { name: /supprimer l'utilisateur/i }));
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByText("Supprimer l'utilisateur")).toBeInTheDocument();
  });

  test('confirmer la suppression appelle l\'API DELETE', async () => {
    renderForm('admin', 'edit', '1', { user: USERS_MOCK[0] });
    await waitFor(() => screen.getByLabelText(/^nom/i));
    fireEvent.click(screen.getByRole('button', { name: /supprimer l'utilisateur/i }));

    const dialog = screen.getByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: /oui, supprimer/i }));

    await waitFor(() => {
      const deleteCall = global.fetch.mock.calls.find(([, options]) => options?.method === 'DELETE');
      expect(deleteCall).toBeTruthy();
    });
  });
});