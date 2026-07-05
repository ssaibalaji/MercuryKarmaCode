import { useEffect, useState } from 'react';
import { Badge, Center, Heading, HStack, Spinner, Text, VStack } from '@chakra-ui/react';
import { GlassCard } from '../ui/GlassCard';
import { feeService } from '../../services/feeService';
import type { FeeDetailResponse } from '../../types';

interface FeeSummaryCardProps {
  studentId: number;
}

/**
 * Compact fee summary meant to slot into a student profile page: shows total
 * outstanding balance across all fee structures and the next upcoming due date.
 */
export function FeeSummaryCard({ studentId }: FeeSummaryCardProps) {
  const [detail, setDetail] = useState<FeeDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    setError(null);
    feeService
      .getFeeDetail(studentId)
      .then(setDetail)
      .catch(() => setError('Unable to load fee summary.'))
      .finally(() => setIsLoading(false));
  }, [studentId]);

  if (isLoading) {
    return (
      <GlassCard>
        <Center minH="24" py={4}>
          <Spinner color="brand.500" />
        </Center>
      </GlassCard>
    );
  }

  if (error || !detail) {
    return (
      <GlassCard>
        <Text color="red.600">{error ?? 'No fee data available.'}</Text>
      </GlassCard>
    );
  }

  const nextDue = detail.fee_structures
    .filter((fee) => fee.outstanding_balance > 0)
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];

  const hasOverdue = detail.fee_structures.some((fee) => fee.is_overdue);

  return (
    <GlassCard>
      <HStack justify="space-between" align="flex-start">
        <VStack align="flex-start" spacing={1}>
          <Text fontSize="sm" color="gray.600">
            Outstanding Balance
          </Text>
          <Heading size="lg">₹{detail.total_outstanding.toLocaleString()}</Heading>
        </VStack>
        {hasOverdue && (
          <Badge colorScheme="red" borderRadius="md" px={2} py={1}>
            Overdue
          </Badge>
        )}
      </HStack>
      <Text mt={4} fontSize="sm" color="gray.600">
        {nextDue ? `Next due: ${nextDue.due_date} (₹${nextDue.outstanding_balance.toLocaleString()})` : 'No pending dues'}
      </Text>
    </GlassCard>
  );
}
