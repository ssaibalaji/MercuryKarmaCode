import clsx, { type ClassValue } from 'clsx';

/**
 * Merge class names conditionally. Thin wrapper around clsx so the rest of
 * the codebase has a single, stable import (`cn`) regardless of which
 * underlying class-merging library is used.
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(...inputs);
}
