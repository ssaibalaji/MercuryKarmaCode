import api from './api';
import { User, UserRole } from '../types';

export interface RegisterData {
  email: string;
  password: string;
  fullName?: string;
  role: UserRole;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Thin wrapper around the `/auth/*` backend endpoints. Components/hooks
 * should prefer `useAuth()` for state that needs to live in React context
 * (login/logout/current user); use this service directly for one-off calls
 * (e.g. registration, password reset) that don't need context state.
 */
export const authService = {
  async register(data: RegisterData): Promise<User> {
    const { data: user } = await api.post<User>('/auth/register', {
      email: data.email,
      password: data.password,
      full_name: data.fullName,
      role: data.role,
    });
    return user;
  },

  async login(email: string, password: string): Promise<TokenPair> {
    const form = new FormData();
    form.append('username', email);
    form.append('password', password);
    const { data } = await api.post<TokenPair>('/auth/login', form);
    return data;
  },

  logout(): void {
    localStorage.clear();
  },

  async getMe(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  googleLoginUrl(): string {
    return `${import.meta.env.VITE_API_URL}/api/v1/auth/google`;
  },
};

export default authService;
