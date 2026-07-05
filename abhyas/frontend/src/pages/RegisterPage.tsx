import { Center, Heading, Stack, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { MeshBackground } from '../components/layout/MeshBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { RegisterForm } from '../components/auth/RegisterForm';

export function RegisterPage() {
  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="100vh" px={4}>
        <GlassCard maxW="md" w="full">
          <Stack spacing={6}>
            <Stack spacing={1} textAlign="center">
              <Heading size="lg">Create your account</Heading>
              <Text color="gray.600">For teachers and institutes</Text>
            </Stack>

            <RegisterForm />

            <Text textAlign="center" fontSize="sm" color="gray.600">
              Already have an account?{' '}
              <RouterLink to="/login" style={{ fontWeight: 600 }}>
                Log in
              </RouterLink>
            </Text>
          </Stack>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
