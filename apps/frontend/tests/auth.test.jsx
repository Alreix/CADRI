import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import LoginPage from '../src/pages/LoginPage';
import ForgotPasswordPage from '../src/pages/ForgotPasswordPage';
import ResetPasswordPage from '../src/pages/ResetPasswordPage';
import ActivateAccountPage from '../src/pages/ActivateAccountPage';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const renderWithRouter = (ui, { route = '/' } = {}) =>
  render(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>);

// ---------------------------------------------------------------------------
// LoginPage
// ---------------------------------------------------------------------------
describe('LoginPage', () => {
  test('renders the form with email, password fields and a submit button', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log in|sign in|connect/i })).toBeInTheDocument();
  });

  test('submit button is disabled when fields are empty', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByRole('button', { name: /log in|sign in|connect/i })).toBeDisabled();
  });

  test('submit button is enabled when both fields are filled', () => {
    renderWithRouter(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'agent@cadri.fr' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Azerty123!' } });
    expect(screen.getByRole('button', { name: /log in|sign in|connect/i })).not.toBeDisabled();
  });

  test('shows an error alert when credentials are invalid', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ message: 'Invalid credentials' }),
    });

    renderWithRouter(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'wrong@cadri.fr' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } });
    fireEvent.click(screen.getByRole('button', { name: /log in|sign in|connect/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid credentials/i);
    });
  });

  test('renders a "Forgot password?" link', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByRole('link', { name: /forgot password/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ForgotPasswordPage
// ---------------------------------------------------------------------------
describe('ForgotPasswordPage', () => {
  test('renders the form with an email field and a submit button', () => {
    renderWithRouter(<ForgotPasswordPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send|reset/i })).toBeInTheDocument();
  });

  test('shows a confirmation message after successful submission', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Email sent' }),
    });

    renderWithRouter(<ForgotPasswordPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'agent@cadri.fr' } });
    fireEvent.click(screen.getByRole('button', { name: /send|reset/i }));

    await waitFor(() => {
      expect(screen.getByText(/email sent|check your inbox/i)).toBeInTheDocument();
    });
  });

  test('submit button is disabled when the email field is empty', () => {
    renderWithRouter(<ForgotPasswordPage />);
    expect(screen.getByRole('button', { name: /send|reset/i })).toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// ResetPasswordPage
// ---------------------------------------------------------------------------
describe('ResetPasswordPage', () => {
  test('renders new password and confirmation fields', () => {
    renderWithRouter(<ResetPasswordPage />, { route: '/reset-password?token=abc123' });
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm/i)).toBeInTheDocument();
  });

  test('shows an error when passwords do not match', async () => {
    renderWithRouter(<ResetPasswordPage />, { route: '/reset-password?token=abc123' });
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'Azerty123!' } });
    fireEvent.change(screen.getByLabelText(/confirm/i), { target: { value: 'Different123!' } });
    fireEvent.click(screen.getByRole('button', { name: /save|confirm|submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/do not match|passwords must match/i)).toBeInTheDocument();
    });
  });

  test('shows an error when password does not meet complexity requirements', async () => {
    renderWithRouter(<ResetPasswordPage />, { route: '/reset-password?token=abc123' });
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: '123' } });
    fireEvent.click(screen.getByRole('button', { name: /save|confirm|submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/too short|complexity|characters/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// ActivateAccountPage
// ---------------------------------------------------------------------------
describe('ActivateAccountPage', () => {
  test('shows the welcome popup on account activation', () => {
    renderWithRouter(<ActivateAccountPage />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/welcome/i)).toBeInTheDocument();
  });

  test('clicking "Get started" closes the welcome popup', async () => {
    renderWithRouter(<ActivateAccountPage />);
    fireEvent.click(screen.getByRole('button', { name: /get started/i }));

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });
});
