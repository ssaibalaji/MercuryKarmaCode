import { useCallback, useEffect, useState } from 'react';
import { Box, Center, Heading, Spinner, Text, VStack, useToast } from '@chakra-ui/react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../context/AuthContext';
import { feeService } from '../services/feeService';
import { openRazorpayCheckout, type RazorpayCheckoutResponse } from '../lib/razorpay';
import type { FeeStructureWithBalance } from '../types';

/** Parent-facing Razorpay checkout for a single outstanding fee structure. */
export function PaymentPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  const numericStudentId = studentId ? Number(studentId) : null;
  const feeIdParam = searchParams.get('feeId');
  const numericFeeId = feeIdParam ? Number(feeIdParam) : null;

  const [fee, setFee] = useState<FeeStructureWithBalance | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPaying, setIsPaying] = useState(false);

  const loadFee = useCallback(async () => {
    if (numericStudentId === null || numericFeeId === null) {
      setError('No fee selected to pay.');
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const detail = await feeService.getFeeDetail(numericStudentId);
      const match = detail.fee_structures.find((f) => f.id === numericFeeId);
      if (!match) {
        setError('Fee not found.');
      } else {
        setFee(match);
      }
    } catch {
      setError('Unable to load fee details.');
    } finally {
      setIsLoading(false);
    }
  }, [numericStudentId, numericFeeId]);

  useEffect(() => {
    loadFee();
  }, [loadFee]);

  const handlePay = async (): Promise<void> => {
    if (!fee) return;
    setIsPaying(true);
    try {
      const order = await feeService.createRazorpayOrder(fee.id);
      await openRazorpayCheckout({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: 'Abhyas Fees',
        description: `Fee payment for fee structure #${fee.id}`,
        order_id: order.order_id,
        prefill: {
          name: user?.full_name ?? undefined,
          email: user?.email ?? undefined,
        },
        theme: { color: '#aa3bff' },
        handler: (_response: RazorpayCheckoutResponse) => {
          toast({
            title: 'Payment submitted',
            description: 'We will confirm your payment once Razorpay notifies us.',
            status: 'success',
            duration: 5000,
            isClosable: true,
          });
          navigate(`/fees/${numericStudentId}`);
        },
        modal: {
          ondismiss: () => setIsPaying(false),
        },
      });
    } catch {
      toast({ title: 'Unable to start payment', status: 'error', duration: 4000, isClosable: true });
      setIsPaying(false);
    }
  };

  return (
    <PageWrapper>
      <Center minH="100vh" px={6}>
        <GlassCard maxW="md" w="full">
          {isLoading ? (
            <Center py={8}>
              <Spinner size="xl" color="brand.500" />
            </Center>
          ) : error || !fee ? (
            <Text color="red.600">{error ?? 'No fee to pay.'}</Text>
          ) : (
            <VStack align="stretch" spacing={4}>
              <Heading size="md">Pay Fee</Heading>
              <Box>
                <Text color="gray.600" fontSize="sm">
                  Due Date
                </Text>
                <Text fontWeight="semibold">{fee.due_date}</Text>
              </Box>
              <Box>
                <Text color="gray.600" fontSize="sm">
                  Amount Due
                </Text>
                <Heading size="lg">₹{fee.outstanding_balance.toLocaleString()}</Heading>
              </Box>
              <GradientButton isLoading={isPaying} onClick={handlePay} w="full">
                Pay with Razorpay
              </GradientButton>
            </VStack>
          )}
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
