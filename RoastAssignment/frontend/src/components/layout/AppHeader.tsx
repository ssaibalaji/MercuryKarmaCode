import { Flex, Heading, Spacer, Text } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { GradientButton } from '../ui/GradientButton';

/** Shared header rendered on every authenticated page via `ProtectedRoute`. */
export function AppHeader(): JSX.Element {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <Flex
      as="header"
      align="center"
      px={6}
      py={4}
      bg="whiteAlpha.600"
      backdropFilter="blur(12px)"
      borderBottom="1px solid"
      borderColor="purple.100"
    >
      <Heading size="md" color="purple.600">
        Assignment Evaluator
      </Heading>
      <Spacer />
      {user && (
        <Text fontSize="sm" color="gray.600" mr={4}>
          {user.fullName || user.email} · {user.role}
        </Text>
      )}
      <GradientButton onClick={handleLogout} px={4} py={2} fontSize="sm">
        Logout
      </GradientButton>
    </Flex>
  );
}
