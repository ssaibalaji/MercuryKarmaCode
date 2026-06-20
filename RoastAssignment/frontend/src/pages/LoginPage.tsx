import { Link as RouterLink } from 'react-router-dom';
import { Center, Divider, Heading, Link, Stack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { MeshBackground } from '../components/layout/MeshBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { LoginForm } from '../components/auth/LoginForm';
import { GoogleLoginButton } from '../components/auth/GoogleLoginButton';

export function LoginPage(): JSX.Element {
  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="100vh" px={4}>
        <GlassCard maxW="md" w="full">
          <Stack spacing={6}>
            <Stack spacing={1} textAlign="center">
              <Heading size="lg">Welcome back</Heading>
              <Text color="gray.500">Log in to continue to Assignment Evaluator</Text>
            </Stack>

            <LoginForm />

            <Divider />

            <GoogleLoginButton />

            <Text textAlign="center" fontSize="sm" color="gray.500">
              Don&apos;t have an account?{' '}
              <Link as={RouterLink} to="/register" color="purple.500" fontWeight="semibold">
                Sign up
              </Link>
            </Text>
            <Text textAlign="center" fontSize="sm">
              <Link as={RouterLink} to="/forgot-password" color="purple.500">
                Forgot your password?
              </Link>
            </Text>
          </Stack>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}

export default LoginPage;
