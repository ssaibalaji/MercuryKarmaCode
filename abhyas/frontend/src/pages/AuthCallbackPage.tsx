import { Center, Spinner, Text, VStack } from '@chakra-ui/react';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { useAuth } from '../hooks/useAuth';

/**
 * Landing page for the Google OAuth redirect. The backend's
 * GET /auth/google/callback sets the access/refresh tokens as httpOnly
 * cookies directly on its redirect response, so no tokens ever appear in
 * this page's URL. We just confirm the session by loading the current user,
 * then route into the app.
 */
export function AuthCallbackPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  useEffect(() => {
    refreshUser()
      .then(() => navigate('/dashboard', { replace: true }))
      .catch(() => navigate('/login', { replace: true }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <PageWrapper>
      <Center minH="100vh">
        <VStack spacing={4}>
          <Spinner size="xl" color="brand.500" />
          <Text color="gray.600">Signing you in...</Text>
        </VStack>
      </Center>
    </PageWrapper>
  );
}
