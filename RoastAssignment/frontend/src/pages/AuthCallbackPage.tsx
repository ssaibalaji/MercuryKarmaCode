import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Center, Spinner, Text, VStack } from '@chakra-ui/react';
import api from '../services/api';

export function AuthCallbackPage(): JSX.Element {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (!code || !state) {
      navigate('/login', { replace: true });
      return;
    }

    // Google's registered redirect URI is this page (an SPA can't host a
    // server-side redirect target), so we forward the code/state to the
    // backend ourselves. `withCredentials` ensures the httpOnly
    // `oauth_state` CSRF cookie set by /auth/google is sent.
    api
      .post('/auth/google/callback', { code, state }, { withCredentials: true })
      .then(({ data }) => {
        localStorage.setItem('access_token', data.accessToken);
        localStorage.setItem('refresh_token', data.refreshToken);
        // Full reload so AuthContext re-mounts and picks up the new tokens.
        window.location.href = '/dashboard';
      })
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
