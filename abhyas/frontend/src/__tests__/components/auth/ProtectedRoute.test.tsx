import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';
import { render } from '@testing-library/react';
import { ProtectedRoute } from '../../../components/auth/ProtectedRoute';
import { useAuth } from '../../../context/AuthContext';
import type { User } from '../../../types';
import theme from '../../../lib/theme';

vi.mock('../../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);

const baseUser: User = {
  id: 1,
  email: 'teacher@example.com',
  full_name: 'Teacher One',
  role: 'teacher',
  is_active: true,
  is_verified: true,
  oauth_provider: null,
  created_at: '2024-01-01T00:00:00Z',
};

function renderProtectedRoute(children: ReactNode, allowedRoles?: User['role'][]) {
  return render(
    <ChakraProvider theme={theme}>
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/protected"
            element={<ProtectedRoute allowedRoles={allowedRoles}>{children}</ProtectedRoute>}
          />
          <Route path="/login" element={<div>Login Page Marker</div>} />
          <Route path="/dashboard" element={<div>Dashboard Page Marker</div>} />
        </Routes>
      </MemoryRouter>
    </ChakraProvider>,
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  it('renders a loading state and not children while isLoading is true', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    });

    renderProtectedRoute(<div>Secret Content</div>);

    expect(screen.queryByText('Secret Content')).not.toBeInTheDocument();
    expect(document.querySelector('.chakra-spinner')).toBeInTheDocument();
  });

  it('redirects to /login when there is no authenticated user', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    });

    renderProtectedRoute(<div>Secret Content</div>);

    expect(screen.getByText('Login Page Marker')).toBeInTheDocument();
    expect(screen.queryByText('Secret Content')).not.toBeInTheDocument();
  });

  it('redirects to /dashboard when the user role is not allowed', () => {
    mockedUseAuth.mockReturnValue({
      user: { ...baseUser, role: 'teacher' },
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    });

    renderProtectedRoute(<div>Secret Content</div>, ['admin']);

    expect(screen.getByText('Dashboard Page Marker')).toBeInTheDocument();
    expect(screen.queryByText('Secret Content')).not.toBeInTheDocument();
  });

  it('renders children when the user is authenticated and role is allowed', () => {
    mockedUseAuth.mockReturnValue({
      user: { ...baseUser, role: 'admin' },
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    });

    renderProtectedRoute(<div>Secret Content</div>, ['admin']);

    expect(screen.getByText('Secret Content')).toBeInTheDocument();
  });

  it('renders children when there are no allowedRoles restrictions', () => {
    mockedUseAuth.mockReturnValue({
      user: baseUser,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    });

    renderProtectedRoute(<div>Secret Content</div>);

    expect(screen.getByText('Secret Content')).toBeInTheDocument();
  });
});
