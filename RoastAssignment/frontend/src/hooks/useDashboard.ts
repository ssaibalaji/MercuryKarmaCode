import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { DashboardStats, ScoreDistributionBucket, SubmissionsOverTimePoint } from '../types';

// `api`'s response interceptor already converts the backend's snake_case
// JSON to camelCase, so the response shape matches `DashboardStats` directly.
export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => api.get<DashboardStats>('/dashboard/stats').then((r) => r.data),
  });
}

/**
 * Histogram of overall scores. Only meaningful for examiner/coach roles —
 * callers should gate rendering on `useAuth().user?.role`.
 */
export function useScoreDistribution() {
  return useQuery({
    queryKey: ['dashboard', 'analytics', 'score-distribution'],
    queryFn: () =>
      api
        .get<ScoreDistributionBucket[]>('/dashboard/analytics/score-distribution')
        .then((r) => r.data),
  });
}

/**
 * Daily submission counts over time. Only meaningful for examiner/coach
 * roles — callers should gate rendering on `useAuth().user?.role`.
 */
export function useSubmissionsOverTime() {
  return useQuery({
    queryKey: ['dashboard', 'analytics', 'submissions-over-time'],
    queryFn: () =>
      api
        .get<SubmissionsOverTimePoint[]>('/dashboard/analytics/submissions-over-time')
        .then((r) => r.data),
  });
}
