import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { Center, Spinner, Text, VStack } from '@chakra-ui/react';
import { useAuth } from '../../hooks/useAuth';
import { AppHeader } from '../layout/AppHeader';
import { UserRole } from '../../types';

interface ProtectedRouteProps {
  children: ReactNode;
  allowedRoles?: UserRole[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps): JSX.Element {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Center minH="100vh">
        <VStack spacing={3}>
          <Spinner size="xl" color="purple.500" thickness="3px" />
          <Text color="gray.500">Loading…</Text>
        </VStack>
      </Center>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <>
      <AppHeader />
      {children}
    </>
  );
}

export default ProtectedRoute;
