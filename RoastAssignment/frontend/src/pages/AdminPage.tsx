import { Box, Heading, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { useAuth } from '../hooks/useAuth';

const ALLOWED_ROLES = ['examiner', 'coach'];

export function AdminPage(): JSX.Element {
  const { user } = useAuth();
  const isAllowed = !!user?.role && ALLOWED_ROLES.includes(user.role);

  if (!isAllowed) {
    return (
      <PageWrapper>
        <Box maxW="3xl" mx="auto" px={4} py={8}>
          <GlassCard>
            <Heading size="md" mb={2}>
              Access denied
            </Heading>
            <Text color="gray.500">
              You don&apos;t have permission to view this page.
            </Text>
          </GlassCard>
        </Box>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <Box maxW="3xl" mx="auto" px={4} py={8}>
        <Heading size="lg" mb={6}>
          Admin
        </Heading>
        <GlassCard>
          <Heading size="md" mb={2}>
            Coming soon: user &amp; role management
          </Heading>
          <Text color="gray.500">
            This area will let examiners and coaches manage user accounts and roles. It is not
            part of the MVP and is planned for a later release.
          </Text>
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}

export default AdminPage;
