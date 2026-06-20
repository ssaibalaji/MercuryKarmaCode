import { Flex, Heading, Spinner, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { SubmissionTable } from '../components/submissions/SubmissionTable';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../hooks/useAuth';
import { useSubmissions, useSyncSubmissions } from '../hooks/useSubmissions';

export function SubmissionsListPage() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useSubmissions();
  const syncSubmissions = useSyncSubmissions();

  const canSync = user?.role === 'examiner' || user?.role === 'coach';

  return (
    <PageWrapper>
      <Flex justify="space-between" align="center" mb={6} px={6} pt={6}>
        <Heading size="lg">Submissions</Heading>
        {canSync && (
          <GradientButton
            onClick={() => syncSubmissions.mutate()}
            isLoading={syncSubmissions.isPending}
          >
            Sync now
          </GradientButton>
        )}
        {user?.role === 'student' && (
          <GradientButton as={RouterLink} to="/submissions/new">
            Submit Assignment
          </GradientButton>
        )}
      </Flex>

      <Flex direction="column" px={6} pb={6}>
        {isLoading && (
          <Flex align="center" gap={3}>
            <Spinner />
            <Text>Loading submissions...</Text>
          </Flex>
        )}
        {isError && <Text color="red.400">Failed to load submissions.</Text>}
        {data && <SubmissionTable submissions={data} />}
      </Flex>
    </PageWrapper>
  );
}
