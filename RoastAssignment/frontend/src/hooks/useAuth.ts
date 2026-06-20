import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

/**
 * Access the current authentication state and actions (`user`, `isLoading`,
 * `login`, `logout`, `register`).
 *
 * This is the single canonical import path for the hook — `AuthContext.tsx`
 * re-exports it for backward compatibility with existing imports.
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
