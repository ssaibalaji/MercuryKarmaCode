import { Badge, Box, Flex, Heading, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { AnimatedList } from '../ui/AnimatedList';
import { GlassCard } from '../ui/GlassCard';
import { Submission, SubmissionSyncStatus } from '../../types';

interface SubmissionTableProps {
  submissions: Submission[];
}

const SYNC_STATUS_COLOR: Record<SubmissionSyncStatus, string> = {
  synced: 'green',
  pending: 'yellow',
  error: 'red',
};

export function SubmissionTable({ submissions }: SubmissionTableProps) {
  if (submissions.length === 0) {
    return (
      <GlassCard>
        <Text>No submissions found.</Text>
      </GlassCard>
    );
  }

  return (
    <AnimatedList>
      {submissions.map((submission) => (
        <GlassCard key={submission.id} mb={4}>
          <Flex justify="space-between" align="center" gap={4} wrap="wrap">
            <Box>
              <Heading size="sm">{submission.studentName}</Heading>
              <Text fontSize="sm" color="gray.500">
                {submission.assignmentName}
              </Text>
              <Text fontSize="xs" color="gray.400">
                Submitted {new Date(submission.submittedAt).toLocaleString()}
              </Text>
            </Box>
            <Flex align="center" gap={4}>
              <Badge colorScheme={SYNC_STATUS_COLOR[submission.syncStatus]} rounded="full" px={3} py={1}>
                {submission.syncStatus}
              </Badge>
              <Text
                as={RouterLink}
                to={`/submissions/${submission.id}`}
                fontWeight="semibold"
                color="purple.500"
                _hover={{ textDecoration: 'underline' }}
              >
                View details
              </Text>
            </Flex>
          </Flex>
        </GlassCard>
      ))}
    </AnimatedList>
  );
}
