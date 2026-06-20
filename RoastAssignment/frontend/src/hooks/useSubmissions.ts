import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { Submission } from '../types';

const PAGE_SIZE = 20;

// `GET /submissions` returns a bare JSON array (no `{items, total}` wrapper).
export function useSubmissions(page = 1) {
  const skip = (page - 1) * PAGE_SIZE;
  return useQuery({
    queryKey: ['submissions', page],
    queryFn: () =>
      api.get<Submission[]>(`/submissions?skip=${skip}&limit=${PAGE_SIZE}`).then((r) => r.data),
  });
}

export function useSubmission(id: number) {
  return useQuery({
    queryKey: ['submissions', id],
    queryFn: () => api.get<Submission>(`/submissions/${id}`).then((r) => r.data),
    enabled: id !== undefined,
  });
}

export function useSyncSubmissions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post('/submissions/sync'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
    },
  });
}
