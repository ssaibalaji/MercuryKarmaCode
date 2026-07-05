import { Center, Divider, Heading, HStack, Stack, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { MeshBackground } from '../components/layout/MeshBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { LoginForm } from '../components/auth/LoginForm';
import { GoogleLoginButton } from '../components/auth/GoogleLoginButton';

export function LoginPage() {
  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="100vh" px={4}>
        <GlassCard maxW="md" w="full">
          <Stack spacing={6}>
            <Stack spacing={1} textAlign="center">
              <Heading size="lg">Welcome back</Heading>
              <Text color="gray.600">Log in to manage your students</Text>
            </Stack>

            <LoginForm />

            <HStack>
              <Divider />
              <Text fontSize="sm" color="gray.500" whiteSpace="nowrap">
                OR
              </Text>
              <Divider />
            </HStack>

            <GoogleLoginButton />

            <Text textAlign="center" fontSize="sm" color="gray.600">
              Don&apos;t have an account?{' '}
              <RouterLink to="/register" style={{ fontWeight: 600 }}>
                Sign up
              </RouterLink>
            </Text>
            <Text textAlign="center" fontSize="sm">
              <RouterLink to="/forgot-password" style={{ fontWeight: 600 }}>
                Forgot password?
              </RouterLink>
            </Text>
          </Stack>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
