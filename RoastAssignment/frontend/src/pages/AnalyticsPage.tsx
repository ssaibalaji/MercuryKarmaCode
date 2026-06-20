import { Box, Heading, SimpleGrid, Skeleton, Text } from '@chakra-ui/react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { useAuth } from '../hooks/useAuth';
import { useScoreDistribution, useSubmissionsOverTime } from '../hooks/useDashboard';

const ALLOWED_ROLES = ['examiner', 'coach'];

export function AnalyticsPage(): JSX.Element {
  const { user } = useAuth();
  const isAllowed = !!user?.role && ALLOWED_ROLES.includes(user.role);

  const { data: scoreDistribution, isLoading: isScoreLoading } = useScoreDistribution();
  const { data: submissionsOverTime, isLoading: isOverTimeLoading } = useSubmissionsOverTime();

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
      <Box maxW="6xl" mx="auto" px={4} py={8}>
        <Heading size="lg" mb={6}>
          Analytics
        </Heading>

        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
          <GlassCard>
            <Heading size="sm" mb={4}>
              Score Distribution
            </Heading>
            {isScoreLoading ? (
              <Skeleton height="300px" rounded="xl" />
            ) : !scoreDistribution || scoreDistribution.length === 0 ? (
              <Text color="gray.500">No evaluation data yet.</Text>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={scoreDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#9F7AEA" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </GlassCard>

          <GlassCard>
            <Heading size="sm" mb={4}>
              Submissions Over Time
            </Heading>
            {isOverTimeLoading ? (
              <Skeleton height="300px" rounded="xl" />
            ) : !submissionsOverTime || submissionsOverTime.length === 0 ? (
              <Text color="gray.500">No submission data yet.</Text>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={submissionsOverTime}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#D53F8C" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </GlassCard>
        </SimpleGrid>
      </Box>
    </PageWrapper>
  );
}

export default AnalyticsPage;
