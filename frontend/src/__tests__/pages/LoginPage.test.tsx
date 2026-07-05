import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChakraProvider } from '@chakra-ui/react';
import { MemoryRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { LoginPage } from '../../pages/LoginPage';
import { AuthProvider } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import theme from '../../lib/theme';
import type { User } from '../../types';

vi.mock('../../services/authService', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getMe: vi.fn(),
    updateMe: vi.fn(),
    googleLoginUrl: vi.fn(() => 'https://example.com/auth/google'),
  },
}));

const mockedAuthService = vi.mocked(authService);

const testUser: User = {
  id: 1,
  email: 'user@example.com',
  full_name: 'Test User',
  role: 'teacher',
  is_active: true,
  is_verified: true,
  oauth_provider: null,
  created_at: '2024-01-01T00:00:00Z',
};

function renderLoginPage() {
  return render(
    <ChakraProvider theme={theme}>
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    </ChakraProvider>,
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders the email/password inputs and the submit button', () => {
    renderLoginPage();

    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
  });

  it('submits valid credentials and calls authService.login', async () => {
    mockedAuthService.login.mockResolvedValue(undefined);
    mockedAuthService.getMe.mockResolvedValue(testUser);

    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: /log in/i }));

    await vi.waitFor(() => {
      expect(mockedAuthService.login).toHaveBeenCalledWith('user@example.com', 'password123');
    });
    expect(mockedAuthService.getMe).toHaveBeenCalled();
  });
});
