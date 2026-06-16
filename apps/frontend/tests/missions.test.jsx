import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';

import MissionDetailPage from '../src/pages/MissionDetailPage';
import MissionFormPage from '../src/pages/MissionFormPage';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const MISSION_MOCK = {
  id: 1,
  title: 'Mission Alpha',
  description: 'Test mission description.',
  status: 'ongoing',
  startDate: '2026-06-01',
  endDate: '2026-06-30',
  type: 'field',
};

const renderDetail = (role) => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => MISSION_MOCK,
  });
  return render(
    <AuthContext.Provider value={{ user: { role } }}>
      <MemoryRouter initialEntries={['/missions/1']}>
        <Routes>
          <Route path="/missions/:id" element={<MissionDetailPage />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

const renderForm = (role, mode = 'create') => {
  if (mode === 'edit') {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => MISSION_MOCK,
    });
  }
  const route = mode === 'edit' ? '/missions/1/edit' : '/missions/create';
  const path  = mode === 'edit' ? '/missions/:id/edit' : '/missions/create';
  return render(
    <AuthContext.Provider value={{ user: { role } }}>
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
  test('renders full mission details (title, status, description)', async () => {
    renderDetail('agent');
    await waitFor(() => {
      expect(screen.getByText('Mission Alpha')).toBeInTheDocument();
      expect(screen.getByText(/test mission description/i)).toBeInTheDocument();
      expect(screen.getByText(/ongoing/i)).toBeInTheDocument();
    });
  });

  test('does not render Edit or Delete buttons for an agent', async () => {
    renderDetail('agent');
    await waitFor(() => screen.getByText('Mission Alpha'));
    expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// MissionDetailPage — manager / admin
// ---------------------------------------------------------------------------
describe('MissionDetailPage — manager / admin', () => {
  test('renders Edit and Delete buttons', async () => {
    renderDetail('manager');
    await waitFor(() => screen.getByText('Mission Alpha'));
    expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
  });

  test('clicking Delete opens the confirmation dialog', async () => {
    renderDetail('manager');
    await waitFor(() => screen.getByText('Mission Alpha'));
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/confirm deletion/i)).toBeInTheDocument();
  });

  test('clicking Cancel closes the confirmation dialog', async () => {
    renderDetail('manager');
    await waitFor(() => screen.getByText('Mission Alpha'));
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  test('confirming deletion calls the API and redirects', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => MISSION_MOCK })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    renderDetail('manager');
    await waitFor(() => screen.getByText('Mission Alpha'));
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });
});

// ---------------------------------------------------------------------------
// MissionFormPage — create
// ---------------------------------------------------------------------------
describe('MissionFormPage — create', () => {
  test('renders all required fields', () => {
    renderForm('manager', 'create');
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
  });

  test('shows validation errors when required fields are empty', async () => {
    renderForm('manager', 'create');
    fireEvent.click(screen.getByRole('button', { name: /create|save|submit/i }));
    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0);
    });
  });

  test('submits the form and calls the API when all fields are filled', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: 99 }) });
    renderForm('manager', 'create');

    fireEvent.change(screen.getByLabelText(/title/i),       { target: { value: 'New mission' } });
    fireEvent.change(screen.getByLabelText(/description/i), { target: { value: 'Test description' } });
    fireEvent.change(screen.getByLabelText(/start date/i),  { target: { value: '2026-07-01' } });
    fireEvent.change(screen.getByLabelText(/end date/i),    { target: { value: '2026-07-31' } });
    fireEvent.click(screen.getByRole('button', { name: /create|save|submit/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/missions'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});

// ---------------------------------------------------------------------------
// MissionFormPage — edit (role-based)
// ---------------------------------------------------------------------------
describe('MissionFormPage — edit', () => {
  test('agent cannot edit the status field', async () => {
    renderForm('agent', 'edit');
    await waitFor(() => screen.getByLabelText(/title/i));
    expect(screen.queryByLabelText(/status/i)).not.toBeInTheDocument();
  });

  test('manager can edit all fields including status', async () => {
    renderForm('manager', 'edit');
    await waitFor(() => screen.getByLabelText(/title/i));
    expect(screen.getByLabelText(/status/i)).toBeInTheDocument();
  });

  test('fields are pre-filled with existing mission data', async () => {
    renderForm('manager', 'edit');
    await waitFor(() => {
      expect(screen.getByLabelText(/title/i)).toHaveValue('Mission Alpha');
    });
  });
});
