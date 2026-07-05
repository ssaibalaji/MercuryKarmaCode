import { Center, Heading, Stack, Text } from '@chakra-ui/react';
import { useState, type FormEvent } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { MeshBackground } from '../components/layout/MeshBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { AnimatedInput } from '../components/ui/AnimatedInput';
import { GradientButton } from '../components/ui/GradientButton';

/**
 * Password-reset request page. There is no backend "forgot password" endpoint
 * yet (out of scope for the Auth module's current backend surface), so this
 * page collects the email and shows a generic confirmation without leaking
 * whether the account exists - the same UX contract a real endpoint would need.
 */
export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    setSubmitted(true);
  };

  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="100vh" px={4}>
        <GlassCard maxW="md" w="full">
          <Stack spacing={6}>
            <Stack spacing={1} textAlign="center">
              <Heading size="lg">Reset your password</Heading>
              <Text color="gray.600">
                Enter your email and we&apos;ll send you a reset link.
              </Text>
            </Stack>

            {submitted ? (
              <Text textAlign="center" color="gray.700">
                If an account exists for <strong>{email}</strong>, you&apos;ll receive an email
                with reset instructions shortly.
              </Text>
            ) : (
              <form onSubmit={handleSubmit}>
                <Stack spacing={4}>
                  <AnimatedInput
                    label="Email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    isRequired
                  />
                  <GradientButton type="submit" w="full">
                    Send Reset Link
                  </GradientButton>
                </Stack>
              </form>
            )}

            <Text textAlign="center" fontSize="sm" color="gray.600">
              <RouterLink to="/login" style={{ fontWeight: 600 }}>
                Back to login
              </RouterLink>
            </Text>
          </Stack>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
