import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Select, Stack, Text } from '@chakra-ui/react';
import { AnimatedInput } from '../ui/AnimatedInput';
import { GradientButton } from '../ui/GradientButton';
import { authService } from '../../services/authService';
import { UserRole } from '../../types';

interface FormErrors {
  email?: string;
  password?: string;
  confirmPassword?: string;
  fullName?: string;
}

function validate(
  email: string,
  password: string,
  confirmPassword: string
): FormErrors {
  const errors: FormErrors = {};
  if (!email.trim()) {
    errors.email = 'Email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = 'Enter a valid email address';
  }
  if (!password) {
    errors.password = 'Password is required';
  } else if (password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
  }
  if (confirmPassword !== password) {
    errors.confirmPassword = 'Passwords do not match';
  }
  return errors;
}

export function RegisterForm(): JSX.Element {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<UserRole>('student');
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setSubmitError(null);

    const validationErrors = validate(email, password, confirmPassword);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await authService.register({ email, password, fullName: fullName || undefined, role });
      navigate('/login', { replace: true });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setSubmitError(message ?? 'Could not create your account. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Stack as="form" spacing={4} onSubmit={handleSubmit} noValidate>
      <AnimatedInput
        type="text"
        label="Full name"
        placeholder="Jane Doe"
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
        error={errors.fullName}
        autoComplete="name"
      />
      <AnimatedInput
        type="email"
        label="Email"
        placeholder="you@example.com"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={errors.email}
        autoComplete="email"
      />
      <AnimatedInput
        type="password"
        label="Password"
        placeholder="••••••••"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        error={errors.password}
        autoComplete="new-password"
      />
      <AnimatedInput
        type="password"
        label="Confirm password"
        placeholder="••••••••"
        value={confirmPassword}
        onChange={(event) => setConfirmPassword(event.target.value)}
        error={errors.confirmPassword}
        autoComplete="new-password"
      />
      <Stack spacing={1}>
        <Text fontSize="sm" fontWeight="medium">
          Role
        </Text>
        <Select
          value={role}
          onChange={(event) => setRole(event.target.value as UserRole)}
          rounded="xl"
          borderWidth="2px"
        >
          <option value="student">Student</option>
          <option value="examiner">Examiner</option>
          <option value="coach">Coach</option>
        </Select>
      </Stack>
      {submitError && (
        <Text color="red.500" fontSize="sm">
          {submitError}
        </Text>
      )}
      <GradientButton type="submit" disabled={isSubmitting} w="full">
        {isSubmitting ? 'Creating account…' : 'Create Account'}
      </GradientButton>
    </Stack>
  );
}

export default RegisterForm;
