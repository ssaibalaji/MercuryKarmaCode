import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ChakraProvider } from '@chakra-ui/react';
import { LoginForm } from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth';

// `AnimatedInput` (frontend/src/components/ui/AnimatedInput.tsx) renders its
// label as a plain `Text as="label"` with no `htmlFor`/`id` pairing to the
// input, so `getByLabelText` cannot associate them (a real a11y bug worth
// fixing upstream). We query by placeholder text instead as a workaround.
vi.mock('../hooks/useAuth');

const mockedUseAuth = vi.mocked(useAuth);

function renderLoginForm() {
  return render(
    <ChakraProvider>
      <LoginForm />
    </ChakraProvider>
  );
}

describe('LoginForm', () => {
  const loginMock = vi.fn();

  beforeEach(() => {
    loginMock.mockReset();
    mockedUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      login: loginMock,
      logout: vi.fn(),
      register: vi.fn(),
    });
  });

  it('renders email and password fields', () => {
    renderLoginForm();
    expect(screen.getByPlaceholderText(/you@example.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
  });

  it('shows validation errors and does not call login when fields are empty', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    await user.click(screen.getByRole('button', { name: /log in/i }));

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('shows a validation error for a malformed email', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'not-an-email');
    await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
    await user.click(screen.getByRole('button', { name: /log in/i }));

    expect(await screen.findByText(/enter a valid email address/i)).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('calls useAuth().login with the entered credentials on submit', async () => {
    loginMock.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'test@example.com');
    await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
    await user.click(screen.getByRole('button', { name: /log in/i }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  it('shows a submit error message when login rejects', async () => {
    loginMock.mockRejectedValueOnce(new Error('invalid credentials'));
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'test@example.com');
    await user.type(screen.getByPlaceholderText('••••••••'), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /log in/i }));

    expect(
      await screen.findByText(/invalid email or password\. please try again\./i)
    ).toBeInTheDocument();
  });
});
