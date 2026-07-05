import { useCallback, useEffect, useState } from 'react';
import {
  Badge,
  Box,
  Center,
  Heading,
  Spinner,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
} from '@chakra-ui/react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../context/AuthContext';
import { feeService } from '../services/feeService';
import type { FeeDetailResponse } from '../types';

/** Fee structures + payment history for a single student. */
export function FeeDetailPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const { user } = useAuth();
  const [detail, setDetail] = useState<FeeDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const numericStudentId = studentId ? Number(studentId) : null;

  const loadDetail = useCallback(() => {
    if (numericStudentId === null) return;
    setIsLoading(true);
    setError(null);
    feeService
      .getFeeDetail(numericStudentId)
      .then(setDetail)
      .catch(() => setError('Unable to load fee details for this student.'))
      .finally(() => setIsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericStudentId]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  if (numericStudentId === null) {
    return (
      <PageWrapper>
        <Center minH="100vh">
          <GlassCard>
            <Text color="red.600">Invalid student.</Text>
          </GlassCard>
        </Center>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <Box maxW="5xl" mx="auto" px={6} py={10}>
        <Heading size="xl" mb={8}>
          Fee Details
        </Heading>

        {isLoading ? (
          <Center minH="40vh">
            <Spinner size="xl" color="brand.500" />
          </Center>
        ) : error || !detail ? (
          <GlassCard>
            <Text color="red.600">{error ?? 'No fee data available.'}</Text>
          </GlassCard>
        ) : (
          <VStack align="stretch" spacing={8}>
            <GlassCard>
              <Heading size="md" mb={2}>
                Outstanding Balance: ₹{detail.total_outstanding.toLocaleString()}
              </Heading>
            </GlassCard>

            <GlassCard overflowX="auto">
              <Heading size="md" mb={4}>
                Fee Structures
              </Heading>
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Frequency</Th>
                    <Th>Due Date</Th>
                    <Th isNumeric>Amount</Th>
                    <Th isNumeric>Outstanding</Th>
                    <Th>Status</Th>
                    {user?.role === 'parent' && <Th>Actions</Th>}
                  </Tr>
                </Thead>
                <Tbody>
                  {detail.fee_structures.map((fee) => (
                    <Tr key={fee.id}>
                      <Td textTransform="capitalize">{fee.frequency.replace('_', ' ')}</Td>
                      <Td>{fee.due_date}</Td>
                      <Td isNumeric>₹{fee.amount.toLocaleString()}</Td>
                      <Td isNumeric>₹{fee.outstanding_balance.toLocaleString()}</Td>
                      <Td>
                        {fee.outstanding_balance <= 0 ? (
                          <Badge colorScheme="green" borderRadius="md" px={2} py={1}>
                            Paid
                          </Badge>
                        ) : fee.is_overdue ? (
                          <Badge colorScheme="red" borderRadius="md" px={2} py={1}>
                            Overdue
                          </Badge>
                        ) : (
                          <Badge colorScheme="yellow" borderRadius="md" px={2} py={1}>
                            Pending
                          </Badge>
                        )}
                      </Td>
                      {user?.role === 'parent' && (
                        <Td>
                          {fee.outstanding_balance > 0 && (
                            <RouterLink to={`/fees/${numericStudentId}/pay?feeId=${fee.id}`}>
                              <GradientButton size="sm">Pay Now</GradientButton>
                            </RouterLink>
                          )}
                        </Td>
                      )}
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </GlassCard>

            <GlassCard overflowX="auto">
              <Heading size="md" mb={4}>
                Payment History
              </Heading>
              {detail.payments.length === 0 ? (
                <Text color="gray.600">No payments recorded yet.</Text>
              ) : (
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Date</Th>
                      <Th isNumeric>Amount</Th>
                      <Th>Method</Th>
                      <Th>Status</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {detail.payments.map((payment) => (
                      <Tr key={payment.id}>
                        <Td>{new Date(payment.payment_date).toLocaleDateString()}</Td>
                        <Td isNumeric>₹{payment.amount_paid.toLocaleString()}</Td>
                        <Td textTransform="capitalize">{payment.method.replace('_', ' ')}</Td>
                        <Td>
                          <Badge
                            colorScheme={
                              payment.status === 'completed'
                                ? 'green'
                                : payment.status === 'failed'
                                  ? 'red'
                                  : 'yellow'
                            }
                            borderRadius="md"
                            px={2}
                            py={1}
                          >
                            {payment.status}
                          </Badge>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              )}
            </GlassCard>
          </VStack>
        )}
      </Box>
    </PageWrapper>
  );
}
