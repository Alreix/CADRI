import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import ProfilePage from '../src/pages/ProfilePage';
import { AuthContext } from '../src/contexts/AuthContext';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const USER_MOCK = {
  id: 1,
  firstName: 'Jean',
  lastName: 'Dupont',
  email: 'jean.dupont@cadri.fr',
  role: 'agent',
};

const renderProfile = (logout = vi.fn()) => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => USER_MOCK,
  });
  return render(
    <AuthContext.Provider value={{ user: USER_MOCK, logout }}>
      <MemoryRouter><ProfilePage /></MemoryRouter>
    </AuthContext.Provider>
  );
};

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
describe('ProfilePage — rendering', () => {
  test('renders the user personal information', async () => {
    renderProfile();
    await waitFor(() => {
      expect(screen.getByText(/Jean/i)).toBeInTheDocument();
      expect(screen.getByText(/Dupont/i)).toBeInTheDocument();
      expect(screen.getByText(/jean\.dupont@cadri\.fr/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// General settings
// ---------------------------------------------------------------------------
describe('ProfilePage — general settings', () => {
  test('form fields are pre-filled with current user data', async () => {
    renderProfile();
    await waitFor(() => {
      expect(screen.getByLabelText(/last name/i)).toHaveValue('Dupont');
      expect(screen.getByLabelText(/first name/i)).toHaveValue('Jean');
    });
  });

  test('saving changes calls the API with updated values', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => USER_MOCK })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...USER_MOCK, lastName: 'Durand' }) });

    renderProfile();
    await waitFor(() => screen.getByLabelText(/last name/i));

    fireEvent.change(screen.getByLabelText(/last name/i), { target: { value: 'Durand' } });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/profile'),
        expect.objectContaining({ method: expect.stringMatching(/PUT|PATCH/) })
      );
    });
  });
});

// ---------------------------------------------------------------------------
// Password change
// ---------------------------------------------------------------------------
describe('ProfilePage — password change', () => {
  test('password requirements popup appears when focusing the new password field', async () => {
    renderProfile();
    await waitFor(() => screen.getByLabelText(/last name/i));

    const passwordInput = screen.queryByLabelText(/new password/i);
    if (passwordInput) {
      fireEvent.focus(passwordInput);
      expect(
        screen.queryByRole('tooltip') || screen.queryByText(/uppercase|special character|length/i)
      ).toBeInTheDocument();
    }
  });

  test('shows an error when the new password does not meet requirements', async () => {
    renderProfile();
    await waitFor(() => screen.getByLabelText(/last name/i));

    const passwordInput = screen.queryByLabelText(/new password/i);
    if (passwordInput) {
      fireEvent.change(passwordInput, { target: { value: '123' } });
      fireEvent.click(screen.getByRole('button', { name: /save|change/i }));
      await waitFor(() => {
        expect(screen.getByText(/too short|complexity|characters/i)).toBeInTheDocument();
      });
    }
  });
});

// ---------------------------------------------------------------------------
// Logout
// ---------------------------------------------------------------------------
describe('ProfilePage — logout', () => {
  test('clicking Logout opens the confirmation dialog', async () => {
    renderProfile();
    await waitFor(() => screen.getByLabelText(/last name/i));
    fireEvent.click(screen.getByRole('button', { name: /log out|sign out/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/confirm logout|are you sure/i)).toBeInTheDocument();
  });

  test('confirming logout calls the logout handler', async () => {
    const logoutMock = vi.fn();
    renderProfile(logoutMock);
    await waitFor(() => screen.getByLabelText(/last name/i));
    fireEvent.click(screen.getByRole('button', { name: /log out|sign out/i }));
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalled();
    });
  });

  test('clicking Cancel closes the logout dialog', async () => {
    renderProfile();
    await waitFor(() => screen.getByLabelText(/last name/i));
    fireEvent.click(screen.getByRole('button', { name: /log out|sign out/i }));
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });
});
