import { FormEvent, useState } from 'react';
import { Badge, Center, Heading, Stack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { AnimatedInput } from '../components/ui/AnimatedInput';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

export function ProfilePage(): JSX.Element {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.fullName ?? '');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    setIsSubmitting(true);
    try {
      await api.put('/auth/me', { full_name: fullName });
      setSuccessMessage('Profile updated successfully.');
    } catch {
      setError('Could not update your profile. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) {
    return (
      <PageWrapper>
        <Center minH="100vh">
          <Text color="gray.500">No user signed in.</Text>
        </Center>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <Center minH="100vh" px={4}>
        <GlassCard maxW="md" w="full">
          <Stack spacing={6}>
            <Stack spacing={1} textAlign="center">
              <Heading size="lg">Your profile</Heading>
              <Text color="gray.500">{user.email}</Text>
              <Center>
                <Badge colorScheme="purple" rounded="full" px={3} py={1} textTransform="capitalize">
                  {user.role}
                </Badge>
              </Center>
            </Stack>

            <Stack as="form" spacing={4} onSubmit={handleSubmit} noValidate>
              <AnimatedInput
                type="text"
                label="Full name"
                placeholder="Jane Doe"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                error={error ?? undefined}
              />
              {successMessage && (
                <Text color="green.500" fontSize="sm">
                  {successMessage}
                </Text>
              )}
              <GradientButton type="submit" disabled={isSubmitting} w="full">
                {isSubmitting ? 'Saving…' : 'Save Changes'}
              </GradientButton>
            </Stack>
          </Stack>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}

export default ProfilePage;
