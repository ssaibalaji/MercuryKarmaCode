import api from './api';
import type { User } from '../types';

export interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
}

export interface UpdateMeInput {
  full_name?: string;
}

export const authService = {
  async register(payload: RegisterInput): Promise<User> {
    const response = await api.post<User>('/auth/register', payload);
    return response.data;
  },

  async login(email: string, password: string): Promise<void> {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);

    // The backend sets the access/refresh tokens as httpOnly cookies on this
    // response - there is nothing in the JSON body to store client-side.
    await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },

  async logout(): Promise<void> {
    // Reads the refresh token from its cookie server-side; no body needed.
    await api.post('/auth/logout');
  },

  async getMe(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  async updateMe(payload: UpdateMeInput): Promise<User> {
    const response = await api.put<User>('/auth/me', payload);
    return response.data;
  },

  googleLoginUrl(): string {
    return `${import.meta.env.VITE_API_URL}/api/v1/auth/google`;
  },
};
