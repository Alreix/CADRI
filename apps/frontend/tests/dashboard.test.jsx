import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import DashboardPage from '../src/pages/DashboardPage';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Mock data — shape returned by GET /missions once mapped by missionsApi.js
// ---------------------------------------------------------------------------
const MISSIONS_MOCK = [
  {
    id: 1,
    title: 'Réparation éclairage public',
    status: 'in_progress',
    statusLabel: 'En cours',
    priority: 'high',
    priorityLabel: 'Urgente',
    startDate: '2026-06-01',
    endDate: '2026-06-10',
    interventionType: 'Réparation',
    service: 'Électrique',
    assignedUsers: [],
  },
  {
    id: 2,
    title: 'Entretien parc municipal',
    status: 'completed',
    statusLabel: 'Terminée',
    priority: 'medium',
    priorityLabel: 'Moyenne',
    startDate: '2026-05-15',
    endDate: '2026-05-20',
    interventionType: 'Entretien',
    service: 'Parcs & Jardins',
    assignedUsers: [],
  },
  {
    id: 3,
    title: 'Fuite voirie Avenue des Champs',
    status: 'in_progress',
    statusLabel: 'En cours',
    priority: 'low',
    priorityLabel: 'Basse',
    startDate: '2026-06-05',
    endDate: '2026-06-12',
    interventionType: 'Réparation',
    service: 'Travaux Publics',
    assignedUsers: [],
  },
];

const renderAs = (role, missions = MISSIONS_MOCK) => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => missions,
  });
  return render(
    <AuthContext.Provider value={{ user: { role } }}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
describe('DashboardPage — affichage', () => {
  test('affiche la liste des missions une fois chargée', async () => {
    renderAs('agent');
    await waitFor(() => {
      expect(screen.getByText('Réparation éclairage public')).toBeInTheDocument();
      expect(screen.getByText('Entretien parc municipal')).toBeInTheDocument();
    });
  });

  test('affiche un message quand aucune mission ne correspond', async () => {
    renderAs('agent', []);
    await waitFor(() => {
      expect(screen.getByText(/aucune mission ne correspond/i)).toBeInTheDocument();
    });
  });

  test('affiche le nombre de missions en cours et urgentes dans les cartes statistiques', async () => {
    renderAs('agent');
    await waitFor(() => {
      expect(screen.getByText('Missions en cours')).toBeInTheDocument();
      expect(screen.getByText('Missions urgentes')).toBeInTheDocument();
    });
    // 2 missions "in_progress" sur les 3 du mock, 1 "high" priority
    const values = screen.getAllByText(/^[0-9]+$/);
    expect(values.map((node) => node.textContent)).toEqual(expect.arrayContaining(['2', '1']));
  });

  test('affiche à la fois le badge de priorité et le badge de statut sur une mission urgente', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Réparation éclairage public'));
    expect(screen.getByText('Urgente')).toBeInTheDocument();
    expect(screen.getAllByText('En cours').length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Filters
// ---------------------------------------------------------------------------
describe('DashboardPage — filtres', () => {
  test('cliquer sur le bouton Filtres ouvre le panneau de filtres', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Réparation éclairage public'));
    fireEvent.click(screen.getByRole('button', { name: /filtres/i }));
    expect(screen.getByText('Filtrer les missions')).toBeInTheDocument();
  });

  test('la recherche filtre les missions par titre', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Réparation éclairage public'));
    fireEvent.change(screen.getByPlaceholderText(/rechercher des missions/i), {
      target: { value: 'parc' },
    });
    expect(screen.getByText('Entretien parc municipal')).toBeInTheDocument();
    expect(screen.queryByText('Réparation éclairage public')).not.toBeInTheDocument();
  });

  test('le filtre de statut "Terminée" n\'affiche que les missions terminées', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Réparation éclairage public'));
    fireEvent.click(screen.getByRole('button', { name: /filtres/i }));
    fireEvent.click(screen.getByLabelText(/terminée/i));

    expect(screen.getByText('Entretien parc municipal')).toBeInTheDocument();
    expect(screen.queryByText('Réparation éclairage public')).not.toBeInTheDocument();
    expect(screen.queryByText('Fuite voirie Avenue des Champs')).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
describe('DashboardPage — navigation', () => {
  test('chaque mission propose un lien "Voir la mission" vers sa page de détail', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Réparation éclairage public'));
    const links = screen.getAllByRole('link', { name: /voir la mission/i });
    expect(links[0]).toHaveAttribute('href', '/missions/1');
  });
});

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------
describe('DashboardPage — pagination', () => {
  test('le bouton "Précédent" est désactivé sur la première page', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Réparation éclairage public'));
    expect(screen.getByText(/précédent/i).closest('button')).toBeDisabled();
  });
});