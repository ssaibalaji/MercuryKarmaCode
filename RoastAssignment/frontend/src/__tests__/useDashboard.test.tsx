import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ReactNode } from 'react';
import {
  useDashboardStats,
  useScoreDistribution,
  useSubmissionsOverTime,
} from '../hooks/useDashboard';
import api from '../services/api';

// Manual factory mock: `services/api.ts`'s default export is a configured
// axios instance (interceptors, transformResponse, etc.), which vitest's
// automock can't safely reconstruct. We only need `.get` for these hooks.
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api, true);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useDashboardStats', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('resolves to the expected DashboardStats shape', async () => {
    const statsPayload = {
      totalSubmissions: 12,
      pendingEvaluations: 3,
      completedEvaluations: 8,
      failedEvaluations: 1,
      averageOverallScore: 0.72,
    };
    mockedApi.get.mockResolvedValueOnce({ data: statsPayload });

    const { result } = renderHook(() => useDashboardStats(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith('/dashboard/stats');
    expect(result.current.data).toEqual(statsPayload);
  });

  it('surfaces an error state when the request fails', async () => {
    mockedApi.get.mockRejectedValueOnce(new Error('network error'));

    const { result } = renderHook(() => useDashboardStats(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useScoreDistribution', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('resolves to a list of score buckets', async () => {
    const buckets = [
      { range: '0.0-0.2', count: 1 },
      { range: '0.8-1.0', count: 5 },
    ];
    mockedApi.get.mockResolvedValueOnce({ data: buckets });

    const { result } = renderHook(() => useScoreDistribution(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/dashboard/analytics/score-distribution');
    expect(result.current.data).toEqual(buckets);
  });
});

describe('useSubmissionsOverTime', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('resolves to a list of submissions-over-time points', async () => {
    const points = [{ date: '2026-06-01', count: 4 }];
    mockedApi.get.mockResolvedValueOnce({ data: points });

    const { result } = renderHook(() => useSubmissionsOverTime(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/dashboard/analytics/submissions-over-time');
    expect(result.current.data).toEqual(points);
  });
});
