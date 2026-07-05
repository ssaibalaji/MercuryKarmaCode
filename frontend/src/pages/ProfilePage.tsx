import { Badge, Center, Heading, Stack, Text } from '@chakra-ui/react';
import { useState, type FormEvent } from 'react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { AnimatedInput } from '../components/ui/AnimatedInput';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services/authService';
import type { ApiError } from '../types';

function extractErrorMessage(error: unknown): string {
  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    typeof (error as { response?: { data?: ApiError } }).response?.data?.detail === 'string'
  ) {
    return (error as { response: { data: ApiError } }).response.data.detail;
  }
  return 'Something went wrong. Please try again.';
}

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSuccess(false);
    setIsSubmitting(true);
    try {
      await authService.updateMe({ full_name: fullName });
      await refreshUser();
      setSuccess(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper>
      <Center minH="100vh" px={4}>
        <GlassCard maxW="md" w="full">
          <Stack spacing={6}>
            <Stack spacing={1}>
              <Heading size="lg">Your Profile</Heading>
              {user && (
                <Stack direction="row" align="center" spacing={2}>
                  <Text color="gray.600">{user.email}</Text>
                  <Badge colorScheme="purple" borderRadius="full" px={2}>
                    {user.role}
                  </Badge>
                </Stack>
              )}
            </Stack>

            <form onSubmit={handleSubmit}>
              <Stack spacing={4}>
                <AnimatedInput
                  label="Full Name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  isRequired
                />
                {error && (
                  <Text color="red.500" fontSize="sm">
                    {error}
                  </Text>
                )}
                {success && (
                  <Text color="green.500" fontSize="sm">
                    Profile updated.
                  </Text>
                )}
                <GradientButton type="submit" isLoading={isSubmitting} w="full">
                  Save Changes
                </GradientButton>
              </Stack>
            </form>
          </Stack>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
