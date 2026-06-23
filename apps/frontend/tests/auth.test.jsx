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
  test('affiche le formulaire avec email, mot de passe et bouton de connexion', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByLabelText(/^email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/mot de passe/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /se connecter/i })).toBeInTheDocument();
  });

  test('les champs email et mot de passe sont requis', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByLabelText(/^email/i)).toBeRequired();
    expect(screen.getByLabelText(/mot de passe/i)).toBeRequired();
  });

  test('affiche une modale d\'erreur quand les identifiants sont invalides', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ message: 'Mot de passe erroné' }),
    });

    renderWithRouter(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/^email/i), { target: { value: 'wrong@cadri.fr' } });
    fireEvent.change(screen.getByLabelText(/mot de passe/i), { target: { value: 'wrongpassword' } });
    fireEvent.click(screen.getByRole('button', { name: /se connecter/i }));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/mot de passe erroné/i)).toBeInTheDocument();
    });
  });

  test('affiche un lien "Mot de passe oublié ?"', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByRole('link', { name: /mot de passe oublié/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ForgotPasswordPage
// ---------------------------------------------------------------------------
describe('ForgotPasswordPage', () => {
  test('affiche le formulaire avec un champ email et un bouton d\'envoi', () => {
    renderWithRouter(<ForgotPasswordPage />);
    expect(screen.getByLabelText(/^email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /envoyer le lien/i })).toBeInTheDocument();
  });

  test('affiche un message de confirmation après envoi réussi', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Email sent' }),
    });

    renderWithRouter(<ForgotPasswordPage />);
    fireEvent.change(screen.getByLabelText(/^email/i), { target: { value: 'agent@cadri.fr' } });
    fireEvent.click(screen.getByRole('button', { name: /envoyer le lien/i }));

    await waitFor(() => {
      expect(screen.getByText(/lien envoyé/i)).toBeInTheDocument();
      expect(screen.getByText(/agent@cadri\.fr/)).toBeInTheDocument();
    });
  });

  test('le champ email est requis', () => {
    renderWithRouter(<ForgotPasswordPage />);
    expect(screen.getByLabelText(/^email/i)).toBeRequired();
  });
});

// ---------------------------------------------------------------------------
// ResetPasswordPage
// ---------------------------------------------------------------------------
describe('ResetPasswordPage', () => {
  test('affiche les champs nouveau mot de passe et confirmation', () => {
    renderWithRouter(<ResetPasswordPage />, { route: '/reset-password?token=abc123' });
    expect(screen.getByLabelText(/nouveau mot de passe/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmer le mot de passe/i)).toBeInTheDocument();
  });

  test('affiche une erreur quand les mots de passe ne correspondent pas', async () => {
    renderWithRouter(<ResetPasswordPage />, { route: '/reset-password?token=abc123' });
    fireEvent.change(screen.getByLabelText(/nouveau mot de passe/i), { target: { value: 'Azerty123!' } });
    fireEvent.change(screen.getByLabelText(/confirmer le mot de passe/i), { target: { value: 'Different123!' } });
    fireEvent.click(screen.getByRole('button', { name: /réinitialiser le mot de passe/i }));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/ne correspondent pas/i)).toBeInTheDocument();
    });
  });

  test('appelle l\'API de réinitialisation avec le token et le mot de passe', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    renderWithRouter(<ResetPasswordPage />, { route: '/reset-password?token=abc123' });

    fireEvent.change(screen.getByLabelText(/nouveau mot de passe/i), { target: { value: 'Azerty123!' } });
    fireEvent.change(screen.getByLabelText(/confirmer le mot de passe/i), { target: { value: 'Azerty123!' } });
    fireEvent.click(screen.getByRole('button', { name: /réinitialiser le mot de passe/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
      const [, options] = global.fetch.mock.calls[0];
      const body = JSON.parse(options.body);
      expect(body.token).toBe('abc123');
      expect(body.password).toBe('Azerty123!');
    });
  });
});

// ---------------------------------------------------------------------------
// ActivateAccountPage
// ---------------------------------------------------------------------------
describe('ActivateAccountPage', () => {
  test('affiche la pop-up de bienvenue à l\'arrivée sur la page', () => {
    renderWithRouter(<ActivateAccountPage />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/bienvenue sur cadri/i)).toBeInTheDocument();
  });

  test('cliquer sur "Continuer" ferme la pop-up de bienvenue', async () => {
    renderWithRouter(<ActivateAccountPage />);
    fireEvent.click(screen.getByRole('button', { name: /continuer/i }));

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  test('affiche les champs mot de passe et confirmation', () => {
    renderWithRouter(<ActivateAccountPage />);
    expect(screen.getByLabelText(/^mot de passe/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmer le mot de passe/i)).toBeInTheDocument();
  });
});