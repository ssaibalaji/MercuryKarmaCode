import { createContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';
import { User, UserRole } from '../types';

export interface RegisterPayload {
  email: string;
  password: string;
  fullName?: string;
  role: UserRole;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: RegisterPayload) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      api
        .get('/auth/me')
        .then((r) => setUser(r.data))
        .catch(() => {})
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const form = new FormData();
    form.append('username', email);
    form.append('password', password);
    const { data } = await api.post('/auth/login', form);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    const me = await api.get('/auth/me');
    setUser(me.data);
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  const register = async (data: RegisterPayload) => {
    await api.post('/auth/register', {
      email: data.email,
      password: data.password,
      full_name: data.fullName,
      role: data.role,
    });
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
}

// Re-exported for backward compatibility — the canonical hook now lives in
// `hooks/useAuth.ts` (single source of truth), which reads from this context.
export { useAuth } from '../hooks/useAuth';
