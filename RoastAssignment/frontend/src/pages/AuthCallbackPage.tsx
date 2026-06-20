import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Center, Spinner, Text, VStack } from '@chakra-ui/react';
import api from '../services/api';

export function AuthCallbackPage(): JSX.Element {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    if (!accessToken || !refreshToken) {
      navigate('/login', { replace: true });
      return;
    }

    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);

    // Full reload so AuthContext re-mounts and picks up the new tokens.
    api
      .get('/auth/me')
      .then(() => { window.location.href = '/dashboard'; })
      .catch(() => navigate('/login', { replace: true }));
  }, [navigate]);

  return (
    <Center minH="100vh">
      <VStack spacing={3}>
        <Spinner size="xl" color="purple.500" thickness="3px" />
        <Text color="gray.500">Signing you in…</Text>
      </VStack>
    </Center>
  );
}

export default AuthCallbackPage;
