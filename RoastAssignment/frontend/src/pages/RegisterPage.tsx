import { Link as RouterLink } from 'react-router-dom';
import { Center, Heading, Link, Stack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { MeshBackground } from '../components/layout/MeshBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { RegisterForm } from '../components/auth/RegisterForm';

export function RegisterPage(): JSX.Element {
  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="100vh" px={4}>
        <GlassCard maxW="md" w="full">
          <Stack spacing={6}>
            <Stack spacing={1} textAlign="center">
              <Heading size="lg">Create your account</Heading>
              <Text color="gray.500">Join Assignment Evaluator as a student, examiner, or coach</Text>
            </Stack>

            <RegisterForm />

            <Text textAlign="center" fontSize="sm" color="gray.500">
              Already have an account?{' '}
              <Link as={RouterLink} to="/login" color="purple.500" fontWeight="semibold">
                Log in
              </Link>
            </Text>
          </Stack>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}

export default RegisterPage;
