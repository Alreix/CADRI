import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';

import MissionDetailPage from '../src/pages/MissionDetailPage';
import MissionFormPage from '../src/pages/MissionFormPage';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Mock data — raw backend shapes (snake_case), as returned by the API and
// then normalized by missionsApi.js / metadataApi.js / usersApi.js.
// ---------------------------------------------------------------------------
const MISSION_TO_DO = {
  id: '1',
  title: 'Mission Alpha',
  description: 'Test mission description.',
  status: 'to_do',
  priority: 'high',
  intervention_type: 'Réparation',
  location: 'Avenue des Champs',
  start_date: '2026-06-01',
  end_date: '2026-06-30',
  estimated_duration: 16,
  required_equipment: 'Camion nacelle',
  signage_required: true,
  services: [{ id: 's1', name: 'electrique', label: 'Électrique' }],
  assignments: [{ id: '42' }],
};

const MISSION_IN_PROGRESS = {
  ...MISSION_TO_DO,
  status: 'in_progress',
};

const SERVICES_MOCK = [
  { id: 's1', name: 'electrique', label: 'Électrique' },
  { id: 's2', name: 'travaux_publics', label: 'Travaux Publics' },
];

const ASSIGNABLE_USERS_MOCK = [
  { id: '42', first_name: 'Jean', last_name: 'Dupont', service: { label: 'Électrique' } },
  { id: '43', first_name: 'Marie', last_name: 'Martin', service: { label: 'Travaux Publics' } },
];

// ---------------------------------------------------------------------------
// Helpers — route a single global fetch mock to different fake endpoints
// ---------------------------------------------------------------------------
function mockFetchRoutes({ mission = MISSION_TO_DO, services = SERVICES_MOCK, assignableUsers = ASSIGNABLE_USERS_MOCK } = {}) {
  global.fetch = vi.fn((url, options = {}) => {
    const path = String(url);
    const method = options.method || 'GET';

    if (path.includes('/metadata/services')) {
      return Promise.resolve({ ok: true, json: async () => services });
    }
    if (path.includes('/users/assignable')) {
      return Promise.resolve({ ok: true, json: async () => assignableUsers });
    }
    if (path.match(/\/missions\/[^/]+\/status/) && method === 'PATCH') {
      return Promise.resolve({ ok: true, json: async () => ({ mission: { ...mission, status: 'in_progress' } }) });
    }
    if (path.match(/\/missions\/[^/]+\/actual-duration/) && method === 'PATCH') {
      return Promise.resolve({ ok: true, json: async () => ({ mission }) });
    }
    if (path.match(/\/missions\/[^/]+\/remark/) && method === 'POST') {
      return Promise.resolve({ ok: true, json: async () => ({ mission }) });
    }
    if (path.match(/\/missions\/[^/]+$/) && method === 'DELETE') {
      return Promise.resolve({ ok: true, json: async () => ({}) });
    }
    if (path.match(/\/missions\/[^/]+$/) && method === 'PATCH') {
      return Promise.resolve({ ok: true, json: async () => ({ mission }) });
    }
    if (path.match(/\/missions\/[^/]+$/) && method === 'GET') {
      return Promise.resolve({ ok: true, json: async () => mission });
    }
    if (path.endsWith('/missions') && method === 'POST') {
      return Promise.resolve({ ok: true, json: async () => ({ mission: { ...mission, id: '99' } }) });
    }
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
}

const renderDetail = (role, { mission = MISSION_IN_PROGRESS, userId = '99' } = {}) => {
  mockFetchRoutes({ mission });
  return render(
    <AuthContext.Provider value={{ user: { role, id: userId } }}>
      <MemoryRouter initialEntries={['/missions/1']}>
        <Routes>
          <Route path="/missions/:id" element={<MissionDetailPage />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

const renderForm = (role, mode = 'create', { mission = MISSION_TO_DO, userId = '99' } = {}) => {
  mockFetchRoutes({ mission });
  const route = mode === 'edit' ? '/missions/1/edit' : '/missions/create';
  const path = mode === 'edit' ? '/missions/:id/edit' : '/missions/create';
  return render(
    <AuthContext.Provider value={{ user: { role, id: userId } }}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path={path} element={<MissionFormPage mode={mode} />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

// ---------------------------------------------------------------------------
// MissionDetailPage — agent
// ---------------------------------------------------------------------------
describe('MissionDetailPage — agent', () => {
  test('affiche les détails complets de la mission (titre, statut, description)', async () => {
    renderDetail('agent', { userId: '42' });
    await waitFor(() => {
      expect(screen.getByText('Mission Alpha')).toBeInTheDocument();
      expect(screen.getByText(/test mission description/i)).toBeInTheDocument();
      expect(screen.getByText('En cours')).toBeInTheDocument();
    });
  });

  test('un agent non assigné ne voit ni "Modifier" ni "Démarrer la mission"', async () => {
    renderDetail('agent', { userId: '999' });
    await waitFor(() => screen.getByText('Mission Alpha'));
    expect(screen.queryByRole('button', { name: /modifier/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /démarrer la mission/i })).not.toBeInTheDocument();
  });

  test('un agent assigné peut démarrer une mission "à faire"', async () => {
    renderDetail('agent', { mission: MISSION_TO_DO, userId: '42' });
    await waitFor(() => screen.getByText('Mission Alpha'));
    expect(screen.getByRole('button', { name: /démarrer la mission/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// MissionDetailPage — manager / admin
// ---------------------------------------------------------------------------
describe('MissionDetailPage — responsable / admin', () => {
  test('affiche les boutons Modifier et Supprimer', async () => {
    renderDetail('responsable');
    await waitFor(() => screen.getByText('Mission Alpha'));
    expect(screen.getByRole('button', { name: /modifier/i })).toBeInTheDocument();
  });

  test('un clic sur Modifier navigue vers la page d\'édition', async () => {
    mockFetchRoutes({ mission: MISSION_IN_PROGRESS });
    render(
      <AuthContext.Provider value={{ user: { role: 'responsable', id: '99' } }}>
        <MemoryRouter initialEntries={['/missions/1']}>
          <Routes>
            <Route path="/missions/:id" element={<MissionDetailPage />} />
            <Route path="/missions/:id/edit" element={<div>Page de modification</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
    await waitFor(() => screen.getByText('Mission Alpha'));
    fireEvent.click(screen.getByRole('button', { name: /modifier/i }));
    await waitFor(() => {
      expect(screen.getByText('Page de modification')).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// MissionFormPage — create
// ---------------------------------------------------------------------------
describe('MissionFormPage — création', () => {
  test('affiche tous les champs principaux du formulaire', async () => {
    renderForm('responsable', 'create');
    await waitFor(() => screen.getByLabelText(/^titre/i));
    expect(screen.getByLabelText(/^titre/i)).toBeInTheDocument();
    expect(screen.getByText(/^service/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/date de début/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/date de fin/i)).toBeInTheDocument();
  });

  test('le titre du formulaire est "Créer une mission"', async () => {
    renderForm('responsable', 'create');
    await waitFor(() => {
      expect(screen.getByText('Créer une mission')).toBeInTheDocument();
    });
  });

  test('le bouton de soumission appelle l\'API de création', async () => {
    renderForm('responsable', 'create');
    await waitFor(() => screen.getByLabelText(/^titre/i));

    fireEvent.change(screen.getByLabelText(/^titre/i), { target: { value: 'New mission' } });
    fireEvent.change(screen.getByLabelText(/^description/i), { target: { value: 'Test description' } });
    fireEvent.change(screen.getByLabelText(/date de début/i), { target: { value: '2026-07-01' } });
    fireEvent.change(screen.getByLabelText(/date de fin/i), { target: { value: '2026-07-31' } });
    fireEvent.click(screen.getByRole('button', { name: /créer la mission/i }));

    await waitFor(() => {
      const postCall = global.fetch.mock.calls.find(
        ([url, options]) => options?.method === 'POST' && String(url).includes('/missions')
      );
      expect(postCall).toBeTruthy();
    });
  });
});

// ---------------------------------------------------------------------------
// MissionFormPage — edit (role-based)
// ---------------------------------------------------------------------------
describe('MissionFormPage — édition', () => {
  test('le statut est affiché et modifiable pour un responsable', async () => {
    renderForm('responsable', 'edit');
    await waitFor(() => screen.getByLabelText(/^titre/i));
    expect(screen.getByLabelText(/^statut/i)).toBeInTheDocument();
  });

  test('le champ "Durée réelle" est éditable pour un responsable, quelle que soit l\'assignation', async () => {
    renderForm('responsable', 'edit', { mission: MISSION_IN_PROGRESS });
    await waitFor(() => screen.getByLabelText(/^titre/i));
    expect(screen.getByLabelText(/durée réelle/i)).not.toBeDisabled();
  });

  test('un agent assigné et sur une mission "en cours" peut renseigner la durée réelle et la remarque', async () => {
    renderForm('agent', 'edit', { mission: MISSION_IN_PROGRESS, userId: '42' });
    await waitFor(() => screen.getByLabelText(/^titre/i));
    expect(screen.getByLabelText(/durée réelle/i)).not.toBeDisabled();
    expect(screen.getByLabelText(/^remarque/i)).not.toBeDisabled();
  });

  test('un agent non assigné voit tous les champs de suivi désactivés', async () => {
    renderForm('agent', 'edit', { mission: MISSION_IN_PROGRESS, userId: '999' });
    await waitFor(() => screen.getByLabelText(/^titre/i));
    expect(screen.getByLabelText(/durée réelle/i)).toBeDisabled();
  });

  test('le champ "Remarque" est visible mais en lecture seule pour un responsable', async () => {
    renderForm('responsable', 'edit', { mission: MISSION_IN_PROGRESS });
    await waitFor(() => screen.getByLabelText(/^titre/i));
    expect(screen.getByLabelText(/^remarque/i)).toBeDisabled();
  });

  test('les champs sont pré-remplis avec les données existantes de la mission', async () => {
    renderForm('responsable', 'edit');
    await waitFor(() => {
      expect(screen.getByLabelText(/^titre/i)).toHaveValue('Mission Alpha');
    });
  });

  test('le bouton "Supprimer la mission" est visible pour un responsable', async () => {
    renderForm('responsable', 'edit');
    await waitFor(() => screen.getByLabelText(/^titre/i));
    expect(screen.getByRole('button', { name: /supprimer la mission/i })).toBeInTheDocument();
  });

  test('confirmer la suppression appelle l\'API DELETE', async () => {
    renderForm('responsable', 'edit');
    await waitFor(() => screen.getByLabelText(/^titre/i));
    fireEvent.click(screen.getByRole('button', { name: /supprimer la mission/i }));

    const dialog = screen.getByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: /oui, supprimer/i }));

    await waitFor(() => {
      const deleteCall = global.fetch.mock.calls.find(([, options]) => options?.method === 'DELETE');
      expect(deleteCall).toBeTruthy();
    });
  });
});