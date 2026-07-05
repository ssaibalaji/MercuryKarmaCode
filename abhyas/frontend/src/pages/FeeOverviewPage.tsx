import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  Badge,
  Box,
  Button,
  Center,
  Flex,
  Heading,
  Spinner,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  useDisclosure,
  useToast,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { feeService } from '../services/feeService';
import type { FeeStructureWithBalance } from '../types';

/** Teacher-facing overview of overdue fees across all of their students. */
export function FeeOverviewPage() {
  const [overdueFees, setOverdueFees] = useState<FeeStructureWithBalance[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [remindingId, setRemindingId] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [markingPaidId, setMarkingPaidId] = useState<number | null>(null);
  const [feeToMarkPaid, setFeeToMarkPaid] = useState<FeeStructureWithBalance | null>(null);
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);

  const loadOverdueFees = useCallback(() => {
    setIsLoading(true);
    setError(null);
    feeService
      .getOverdueFees()
      .then(setOverdueFees)
      .catch(() => setError('Unable to load overdue fees right now.'))
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    loadOverdueFees();
  }, [loadOverdueFees]);

  const handleRemind = async (feeId: number): Promise<void> => {
    setRemindingId(feeId);
    try {
      await feeService.sendReminder(feeId);
      toast({ title: 'Reminder sent', status: 'success', duration: 3000, isClosable: true });
    } catch {
      toast({ title: 'Failed to send reminder', status: 'error', duration: 3000, isClosable: true });
    } finally {
      setRemindingId(null);
    }
  };

  const handleOpenMarkPaidConfirm = (fee: FeeStructureWithBalance): void => {
    setFeeToMarkPaid(fee);
    onOpen();
  };

  const handleConfirmMarkPaid = async (): Promise<void> => {
    if (!feeToMarkPaid) {
      return;
    }
    const feeId = feeToMarkPaid.id;
    onClose();
    setMarkingPaidId(feeId);
    try {
      const updated = await feeService.markFeePaid(feeId);
      setOverdueFees((prev) => (prev ? prev.map((fee) => (fee.id === feeId ? updated : fee)) : prev));
      toast({ title: 'Fee marked as paid', status: 'success', duration: 3000, isClosable: true });
    } catch {
      toast({ title: 'Failed to mark fee as paid', status: 'error', duration: 3000, isClosable: true });
    } finally {
      setMarkingPaidId(null);
      setFeeToMarkPaid(null);
    }
  };

  const handleGenerateFees = async (): Promise<void> => {
    setIsGenerating(true);
    try {
      const summary = await feeService.generateFeesFromAttendance();
      const studentCount = new Set(summary.created.map((entry) => entry.student_id)).size;
      toast({
        title: `Created ${summary.created.length} fee entries across ${studentCount} students.`,
        description:
          `Skipped: ${summary.skipped_already_generated} already generated, ` +
          `${summary.skipped_no_daily_fee} with no daily fee set, ` +
          `${summary.skipped_zero_days} with zero attendance days.`,
        status: 'success',
        duration: 6000,
        isClosable: true,
      });
      loadOverdueFees();
    } catch {
      toast({
        title: 'Failed to generate fees from attendance',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <PageWrapper>
      <Box maxW="6xl" mx="auto" px={6} py={10}>
        <Flex justify="space-between" align="center" mb={8} wrap="wrap" gap={4}>
          <Heading size="xl">Fees Overview</Heading>
          <GradientButton isLoading={isGenerating} onClick={handleGenerateFees}>
            Generate Fees for Past Months
          </GradientButton>
        </Flex>

        {isLoading ? (
          <Center minH="40vh">
            <Spinner size="xl" color="brand.500" />
          </Center>
        ) : error ? (
          <GlassCard>
            <Text color="red.600">{error}</Text>
          </GlassCard>
        ) : !overdueFees || overdueFees.length === 0 ? (
          <GlassCard>
            <Text color="gray.600">No overdue fees. Everyone is up to date.</Text>
          </GlassCard>
        ) : (
          <GlassCard overflowX="auto">
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Student</Th>
                  <Th>Due Date</Th>
                  <Th isNumeric>Outstanding</Th>
                  <Th>Status</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {overdueFees.map((fee) => {
                  const isPaid = fee.outstanding_balance <= 0;
                  return (
                    <Tr key={fee.id}>
                      <Td>
                        <RouterLink to={`/fees/${fee.student_id}`}>{fee.student_name}</RouterLink>
                      </Td>
                      <Td>{fee.due_date}</Td>
                      <Td isNumeric>₹{fee.outstanding_balance.toLocaleString()}</Td>
                      <Td>
                        {isPaid ? (
                          <Badge colorScheme="green" borderRadius="md" px={2} py={1}>
                            Paid
                          </Badge>
                        ) : (
                          <Badge colorScheme="red" borderRadius="md" px={2} py={1}>
                            Overdue
                          </Badge>
                        )}
                      </Td>
                      <Td>
                        <Flex gap={2} wrap="wrap">
                          <GradientButton
                            size="sm"
                            isDisabled={isPaid}
                            isLoading={remindingId === fee.id}
                            onClick={() => handleRemind(fee.id)}
                          >
                            Send Reminder
                          </GradientButton>
                          <Button
                            size="sm"
                            colorScheme="green"
                            borderRadius="full"
                            isDisabled={isPaid}
                            isLoading={markingPaidId === fee.id}
                            onClick={() => handleOpenMarkPaidConfirm(fee)}
                          >
                            Payment Complete
                          </Button>
                        </Flex>
                      </Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </GlassCard>
        )}
      </Box>

      <AlertDialog isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={onClose}>
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Mark fee as paid
            </AlertDialogHeader>
            <AlertDialogBody>Are you sure you want to mark this fee as paid?</AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onClose}>
                Cancel
              </Button>
              <Button colorScheme="green" onClick={handleConfirmMarkPaid} ml={3}>
                Yes
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </PageWrapper>
  );
}
