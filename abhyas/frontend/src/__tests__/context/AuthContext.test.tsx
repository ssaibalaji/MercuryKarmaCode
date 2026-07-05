import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AuthProvider, useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import type { User } from '../../types';

vi.mock('../../services/authService', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getMe: vi.fn(),
    updateMe: vi.fn(),
    googleLoginUrl: vi.fn(),
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

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls getMe on mount to detect an existing (cookie-based) session', async () => {
    mockedAuthService.getMe.mockRejectedValue(new Error('no session'));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).toBeNull();
    expect(mockedAuthService.getMe).toHaveBeenCalled();
  });

  it('logs in successfully: calls login (cookies set by the backend), then loads the user', async () => {
    mockedAuthService.getMe.mockRejectedValueOnce(new Error('no session'));
    mockedAuthService.login.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    mockedAuthService.getMe.mockResolvedValue(testUser);

    await act(async () => {
      await result.current.login('user@example.com', 'password123');
    });

    expect(mockedAuthService.login).toHaveBeenCalledWith('user@example.com', 'password123');
    expect(mockedAuthService.getMe).toHaveBeenCalled();
    expect(result.current.user).toEqual(testUser);
  });

  it('clears user on logout even when authService.logout throws', async () => {
    mockedAuthService.getMe.mockResolvedValue(testUser);
    mockedAuthService.logout.mockRejectedValue(new Error('network error'));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await waitFor(() => expect(result.current.user).toEqual(testUser));

    await act(async () => {
      await expect(result.current.logout()).rejects.toThrow('network error');
    });

    expect(result.current.user).toBeNull();
  });
});
