import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';

import UserManagementPage from '../src/pages/UserManagementPage';
import UserFormPage from '../src/pages/UserFormPage';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const USERS_MOCK = [
  { id: 1, lastName: 'Dupont', firstName: 'Jean',  email: 'jean.dupont@cadri.fr',  role: 'agent',   status: 'active'   },
  { id: 2, lastName: 'Martin', firstName: 'Claire', email: 'claire.martin@cadri.fr', role: 'manager', status: 'active'   },
  { id: 3, lastName: 'Durand', firstName: 'Paul',  email: 'paul.durand@cadri.fr',  role: 'agent',   status: 'inactive' },
];

const renderManagement = (role) => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => USERS_MOCK,
  });
  return render(
    <AuthContext.Provider value={{ user: { role, id: 99 } }}>
      <MemoryRouter><UserManagementPage /></MemoryRouter>
    </AuthContext.Provider>
  );
};

const renderForm = (role, mode = 'create', userId = null) => {
  if (mode !== 'create') {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => USERS_MOCK.find(u => u.id === userId) ?? USERS_MOCK[0],
    });
  }
  const route = userId ? `/users/${userId}/${mode}` : '/users/create';
  const path  = userId ? `/users/:id/${mode}` : '/users/create';
  return render(
    <AuthContext.Provider value={{ user: { role, id: 99 } }}>
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
describe('UserManagementPage — list', () => {
  test('renders the user list', async () => {
    renderManagement('admin');
    await waitFor(() => {
      expect(screen.getByText('Jean Dupont')).toBeInTheDocument();
      expect(screen.getByText('Claire Martin')).toBeInTheDocument();
    });
  });

  test('renders an empty state when no users are returned', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    render(
      <AuthContext.Provider value={{ user: { role: 'admin' } }}>
        <MemoryRouter><UserManagementPage /></MemoryRouter>
      </AuthContext.Provider>
    );
    await waitFor(() => {
      expect(screen.getByText(/no users/i)).toBeInTheDocument();
    });
  });

  test('is only accessible to managers and admins', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => USERS_MOCK });
    render(
      <AuthContext.Provider value={{ user: { role: 'agent' } }}>
        <MemoryRouter><UserManagementPage /></MemoryRouter>
      </AuthContext.Provider>
    );
    await waitFor(() => {
      expect(screen.queryByText('Jean Dupont')).not.toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// UserManagementPage — filters
// ---------------------------------------------------------------------------
describe('UserManagementPage — filters', () => {
  test('clicking the filter button opens the filter panel', async () => {
    renderManagement('admin');
    await waitFor(() => screen.getByText('Jean Dupont'));
    fireEvent.click(screen.getByRole('button', { name: /filter/i }));
    expect(screen.getByRole('region', { name: /filter/i })).toBeInTheDocument();
  });

  test('filtering by "agent" role hides non-agents', async () => {
    renderManagement('admin');
    await waitFor(() => screen.getByText('Claire Martin'));
    fireEvent.click(screen.getByRole('button', { name: /filter/i }));
    fireEvent.click(screen.getByLabelText(/^agent$/i));

    expect(screen.getByText('Jean Dupont')).toBeInTheDocument();
    expect(screen.queryByText('Claire Martin')).not.toBeInTheDocument();
  });

  test('filtering by "inactive" status only shows inactive users', async () => {
    renderManagement('admin');
    await waitFor(() => screen.getByText('Paul Durand'));
    fireEvent.click(screen.getByRole('button', { name: /filter/i }));
    fireEvent.click(screen.getByLabelText(/inactive/i));

    expect(screen.getByText('Paul Durand')).toBeInTheDocument();
    expect(screen.queryByText('Jean Dupont')).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// UserFormPage — create
// ---------------------------------------------------------------------------
describe('UserFormPage — create (admin)', () => {
  test('renders all required fields', () => {
    renderForm('admin', 'create');
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/role/i)).toBeInTheDocument();
  });

  test('shows validation errors when required fields are empty', async () => {
    renderForm('admin', 'create');
    fireEvent.click(screen.getByRole('button', { name: /create|save/i }));
    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0);
    });
  });
});

describe('UserFormPage — create (manager)', () => {
  test('role field does not include the "admin" option', () => {
    renderForm('manager', 'create');
    const select = screen.queryByLabelText(/role/i);
    if (select) {
      const options = Array.from(select.options).map(o => o.value);
      expect(options).not.toContain('admin');
    }
  });
});

// ---------------------------------------------------------------------------
// UserFormPage — view
// ---------------------------------------------------------------------------
describe('UserFormPage — view profile', () => {
  test('renders user information in read-only mode', async () => {
    renderForm('admin', 'view', 1);
    await waitFor(() => {
      expect(screen.getByText('Jean Dupont')).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// UserFormPage — edit
// ---------------------------------------------------------------------------
describe('UserFormPage — edit', () => {
  test('fields are pre-filled with the existing user data', async () => {
    renderForm('admin', 'edit', 1);
    await waitFor(() => {
      expect(screen.getByLabelText(/last name/i)).toHaveValue('Dupont');
      expect(screen.getByLabelText(/email/i)).toHaveValue('jean.dupont@cadri.fr');
    });
  });
});

// ---------------------------------------------------------------------------
// UserFormPage — delete
// ---------------------------------------------------------------------------
describe('UserFormPage — delete', () => {
  test('clicking Delete opens the confirmation dialog', async () => {
    renderForm('admin', 'edit', 1);
    await waitFor(() => screen.getByLabelText(/last name/i));
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  test('confirming deletion calls the DELETE API endpoint', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => USERS_MOCK[0] })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    renderForm('admin', 'edit', 1);
    await waitFor(() => screen.getByLabelText(/last name/i));
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/users/1'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });
});
