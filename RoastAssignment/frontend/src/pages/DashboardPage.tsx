import {
  Box,
  Flex,
  Heading,
  SimpleGrid,
  Skeleton,
  Stat,
  StatLabel,
  StatNumber,
  Text,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { AnimatedList } from '../components/ui/AnimatedList';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../hooks/useAuth';
import { useDashboardStats } from '../hooks/useDashboard';
import { useSubmissions } from '../hooks/useSubmissions';

const RECENT_SUBMISSIONS_LIMIT = 5;

export function DashboardPage(): JSX.Element {
  const { user } = useAuth();
  const { data: stats, isLoading: isStatsLoading } = useDashboardStats();
  const { data: submissionsPage, isLoading: isSubmissionsLoading } = useSubmissions(1);

  const recentSubmissions = (submissionsPage ?? []).slice(0, RECENT_SUBMISSIONS_LIMIT);

  return (
    <PageWrapper>
      <Box maxW="6xl" mx="auto" px={4} py={8}>
        <Flex justify="space-between" align="flex-start" mb={6} wrap="wrap" gap={4}>
          <Box>
            <Heading size="lg" mb={2}>
              Dashboard
            </Heading>
            <Text color="gray.500">
              Welcome back{user?.fullName ? `, ${user.fullName}` : ''}.
            </Text>
          </Box>
          {user?.role === 'student' && (
            <GradientButton as={RouterLink} to="/submissions/new">
              Submit Assignment
            </GradientButton>
          )}
        </Flex>

        <SimpleGrid columns={{ base: 1, sm: 2, md: 5 }} spacing={4} mb={10}>
          <GlassCard>
            <Stat>
              <StatLabel>Total Submissions</StatLabel>
              {isStatsLoading ? (
                <Skeleton height="32px" mt={1} />
              ) : (
                <StatNumber>{stats?.totalSubmissions ?? 0}</StatNumber>
              )}
            </Stat>
          </GlassCard>
          <GlassCard>
            <Stat>
              <StatLabel>Pending</StatLabel>
              {isStatsLoading ? (
                <Skeleton height="32px" mt={1} />
              ) : (
                <StatNumber>{stats?.pendingEvaluations ?? 0}</StatNumber>
              )}
            </Stat>
          </GlassCard>
          <GlassCard>
            <Stat>
              <StatLabel>Completed</StatLabel>
              {isStatsLoading ? (
                <Skeleton height="32px" mt={1} />
              ) : (
                <StatNumber>{stats?.completedEvaluations ?? 0}</StatNumber>
              )}
            </Stat>
          </GlassCard>
          <GlassCard>
            <Stat>
              <StatLabel>Failed</StatLabel>
              {isStatsLoading ? (
                <Skeleton height="32px" mt={1} />
              ) : (
                <StatNumber>{stats?.failedEvaluations ?? 0}</StatNumber>
              )}
            </Stat>
          </GlassCard>
          <GlassCard>
            <Stat>
              <StatLabel>Average Score</StatLabel>
              {isStatsLoading ? (
                <Skeleton height="32px" mt={1} />
              ) : (
                <StatNumber>
                  {stats?.averageOverallScore != null ? stats.averageOverallScore.toFixed(2) : '—'}
                </StatNumber>
              )}
            </Stat>
          </GlassCard>
        </SimpleGrid>

        <Flex justify="space-between" align="baseline" mb={4}>
          <Heading size="md">Recent Submissions</Heading>
          <Text
            as={RouterLink}
            to="/submissions"
            fontWeight="semibold"
            color="purple.500"
            fontSize="sm"
            _hover={{ textDecoration: 'underline' }}
          >
            View all
          </Text>
        </Flex>

        {isSubmissionsLoading ? (
          <Skeleton height="80px" rounded="2xl" />
        ) : recentSubmissions.length === 0 ? (
          <GlassCard>
            <Text>No submissions yet.</Text>
          </GlassCard>
        ) : (
          <AnimatedList>
            {recentSubmissions.map((submission) => (
              <GlassCard key={submission.id} mb={3}>
                <Flex justify="space-between" align="center" gap={4} wrap="wrap">
                  <Box>
                    <Text fontWeight="semibold">{submission.studentName}</Text>
                    <Text fontSize="sm" color="gray.500">
                      {submission.assignmentName}
                    </Text>
                  </Box>
                  <Text
                    as={RouterLink}
                    to={`/submissions/${submission.id}`}
                    fontSize="sm"
                    fontWeight="semibold"
                    color="purple.500"
                    _hover={{ textDecoration: 'underline' }}
                  >
                    View details
                  </Text>
                </Flex>
              </GlassCard>
            ))}
          </AnimatedList>
        )}
      </Box>
    </PageWrapper>
  );
}

export default DashboardPage;
