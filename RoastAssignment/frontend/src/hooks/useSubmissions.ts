import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { Submission } from '../types';

const PAGE_SIZE = 20;

// `GET /submissions` returns a bare JSON array (no `{items, total}` wrapper).
//
// Query keys are namespaced ('list' vs 'detail') so `useSubmissions(1)` (page 1
// of the list) and `useSubmission(1)` (the submission with id 1) never share a
// cache entry — they used to both be `['submissions', 1]`, so React Query would
// serve one's cached array/object as the other's, crashing `.slice()` calls
// whenever a submission with the same id as a page number was viewed.
export function useSubmissions(page = 1) {
  const skip = (page - 1) * PAGE_SIZE;
  return useQuery({
    queryKey: ['submissions', 'list', page],
    queryFn: () =>
      api.get<Submission[]>(`/submissions?skip=${skip}&limit=${PAGE_SIZE}`).then((r) => r.data),
  });
}

export function useSubmission(id: number) {
  return useQuery({
    queryKey: ['submissions', 'detail', id],
    queryFn: () => api.get<Submission>(`/submissions/${id}`).then((r) => r.data),
    enabled: Number.isFinite(id),
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

export interface SubmissionCreatePayload {
  assignmentName: string;
  githubRepoUrl: string;
}

export function useCreateSubmission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SubmissionCreatePayload) =>
      api
        .post<Submission>('/submissions', {
          assignment_name: data.assignmentName,
          github_repo_url: data.githubRepoUrl,
        })
        .then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
