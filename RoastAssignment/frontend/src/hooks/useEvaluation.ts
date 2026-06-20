import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { Evaluation } from '../types';

export function useEvaluation(submissionId: number | undefined) {
  return useQuery({
    queryKey: ['evaluations', submissionId],
    queryFn: () =>
      api.get<Evaluation>(`/evaluations/${submissionId}`).then((r) => r.data),
    enabled: submissionId !== undefined,
  });
}

export function useRetryEvaluation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (submissionId: number) =>
      api.post<Evaluation>(`/evaluations/${submissionId}/retry`),
    onSuccess: (_data, submissionId) => {
      queryClient.invalidateQueries({ queryKey: ['evaluations', submissionId] });
      // Also refresh the submission list so status badges update immediately.
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
    },
  });
}
