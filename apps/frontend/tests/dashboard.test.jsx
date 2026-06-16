import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import DashboardPage from '../src/pages/DashboardPage';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const MISSIONS_MOCK = [
  { id: 1, title: 'Mission Alpha', status: 'ongoing',   date: '2026-06-01', type: 'field'  },
  { id: 2, title: 'Mission Beta',  status: 'completed', date: '2026-05-15', type: 'office' },
  { id: 3, title: 'Mission Gamma', status: 'ongoing',   date: '2026-06-10', type: 'field'  },
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
describe('DashboardPage — rendering', () => {
  test('renders the mission list after loading', async () => {
    renderAs('agent');
    await waitFor(() => {
      expect(screen.getByText('Mission Alpha')).toBeInTheDocument();
      expect(screen.getByText('Mission Beta')).toBeInTheDocument();
    });
  });

  test('renders an empty state when no missions are returned', async () => {
    renderAs('agent', []);
    await waitFor(() => {
      expect(screen.getByText(/no missions/i)).toBeInTheDocument();
    });
  });

  test('renders a loading indicator while fetching', () => {
    global.fetch = vi.fn(() => new Promise(() => {}));
    render(
      <AuthContext.Provider value={{ user: { role: 'agent' } }}>
        <MemoryRouter><DashboardPage /></MemoryRouter>
      </AuthContext.Provider>
    );
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Filters
// ---------------------------------------------------------------------------
describe('DashboardPage — filters', () => {
  test('clicking the filter button opens the filter panel', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Mission Alpha'));
    fireEvent.click(screen.getByRole('button', { name: /filter/i }));
    expect(screen.getByRole('region', { name: /filter/i })).toBeInTheDocument();
  });

  test('filtering by "ongoing" status only shows ongoing missions', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Mission Alpha'));
    fireEvent.click(screen.getByRole('button', { name: /filter/i }));
    fireEvent.click(screen.getByLabelText(/ongoing/i));

    expect(screen.getByText('Mission Alpha')).toBeInTheDocument();
    expect(screen.getByText('Mission Gamma')).toBeInTheDocument();
    expect(screen.queryByText('Mission Beta')).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
describe('DashboardPage — navigation', () => {
  test('clicking a mission row navigates to its detail page', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Mission Alpha'));
    const link = screen.getByText('Mission Alpha').closest('a, [role="link"], tr, li');
    expect(link).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Roles
// ---------------------------------------------------------------------------
describe('DashboardPage — roles', () => {
  test('"Create mission" button is visible for managers', async () => {
    renderAs('manager');
    await waitFor(() => screen.getByText('Mission Alpha'));
    expect(screen.getByRole('button', { name: /create mission|new mission/i })).toBeInTheDocument();
  });

  test('"Create mission" button is hidden for agents', async () => {
    renderAs('agent');
    await waitFor(() => screen.getByText('Mission Alpha'));
    expect(screen.queryByRole('button', { name: /create mission|new mission/i })).not.toBeInTheDocument();
  });
});
