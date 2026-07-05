import { Stack, Text } from '@chakra-ui/react';
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AnimatedInput } from '../ui/AnimatedInput';
import { GradientButton } from '../ui/GradientButton';
import { useAuth } from '../../hooks/useAuth';
import type { ApiError } from '../../types';

function extractErrorMessage(error: unknown): string {
  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    typeof (error as { response?: { data?: ApiError } }).response?.data?.detail === 'string'
  ) {
    return (error as { response: { data: ApiError } }).response.data.detail;
  }
  return 'Something went wrong. Please try again.';
}

export function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
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
        <AnimatedInput
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          isRequired
        />
        {error && (
          <Text color="red.500" fontSize="sm">
            {error}
          </Text>
        )}
        <GradientButton type="submit" isLoading={isSubmitting} w="full">
          Log In
        </GradientButton>
      </Stack>
    </form>
  );
}
