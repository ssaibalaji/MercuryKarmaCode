import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ChakraProvider } from '@chakra-ui/react';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { useAuth } from '../hooks/useAuth';
import { User } from '../types';

vi.mock('../hooks/useAuth');

const mockedUseAuth = vi.mocked(useAuth);

function renderProtectedRoute(allowedRoles?: ('student' | 'examiner' | 'coach')[]) {
  return render(
    <ChakraProvider>
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute allowedRoles={allowedRoles}>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </ChakraProvider>
  );
}

const baseUser: User = {
  id: 1,
  email: 'student@example.com',
  fullName: 'Stu Dent',
  role: 'student',
  isActive: true,
  isVerified: true,
  createdAt: new Date().toISOString(),
};

describe('ProtectedRoute', () => {
  it('shows a loading state while auth is resolving', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
    });

    renderProtectedRoute();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('redirects to /login when there is no authenticated user', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
    });

    renderProtectedRoute();
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('renders children when the user is authenticated and no role restriction applies', () => {
    mockedUseAuth.mockReturnValue({
      user: baseUser,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
    });

    renderProtectedRoute();
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects to /dashboard when the user role is not in allowedRoles', () => {
    mockedUseAuth.mockReturnValue({
      user: baseUser,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
    });

    renderProtectedRoute(['examiner', 'coach']);
    expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
  });

  it('renders children when the user role is in allowedRoles', () => {
    mockedUseAuth.mockReturnValue({
      user: { ...baseUser, role: 'examiner' },
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
    });

    renderProtectedRoute(['examiner', 'coach']);
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });
});
