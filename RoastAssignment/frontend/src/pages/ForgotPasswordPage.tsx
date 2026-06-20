import { FormEvent, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Center, Heading, Link, Stack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { MeshBackground } from '../components/layout/MeshBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { AnimatedInput } from '../components/ui/AnimatedInput';
import { GradientButton } from '../components/ui/GradientButton';
import api from '../services/api';

export function ForgotPasswordPage(): JSX.Element {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);

    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Enter a valid email address');
      return;
    }

    setIsSubmitting(true);
    try {
      // TODO: backend does not implement POST /auth/forgot-password yet.
      // Wired up ahead of time so the UI is ready once it's built.
      await api.post('/auth/forgot-password', { email });
      setIsSubmitted(true);
    } catch {
      // Even if the endpoint doesn't exist yet (404) or the request fails,
      // avoid leaking whether an email is registered — show a generic
      // confirmation state once the backend is implemented.
      setIsSubmitted(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="100vh" px={4}>
        <GlassCard maxW="md" w="full">
          <Stack spacing={6}>
            <Stack spacing={1} textAlign="center">
              <Heading size="lg">Reset your password</Heading>
              <Text color="gray.500">
                Enter your account email and we&apos;ll send you a reset link.
              </Text>
            </Stack>

            {isSubmitted ? (
              <Text textAlign="center" color="green.500" fontWeight="medium">
                If an account exists for that email, a reset link is on its way.
              </Text>
            ) : (
              <Stack as="form" spacing={4} onSubmit={handleSubmit} noValidate>
                <AnimatedInput
                  type="email"
                  label="Email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  error={error ?? undefined}
                  autoComplete="email"
                />
                <GradientButton type="submit" disabled={isSubmitting} w="full">
                  {isSubmitting ? 'Sending…' : 'Send Reset Link'}
                </GradientButton>
              </Stack>
            )}

            <Text textAlign="center" fontSize="sm" color="gray.500">
              <Link as={RouterLink} to="/login" color="purple.500" fontWeight="semibold">
                Back to log in
              </Link>
            </Text>
          </Stack>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}

export default ForgotPasswordPage;
