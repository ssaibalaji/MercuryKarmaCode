import { Box, Flex, Heading, Link as ChakraLink, Spinner, Text } from '@chakra-ui/react';
import { useNavigate, useParams } from 'react-router-dom';
import { EvaluationPanel } from '../components/submissions/EvaluationPanel';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { PageWrapper } from '../components/layout/PageWrapper';
import { useSubmission } from '../hooks/useSubmissions';

export function SubmissionDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const submissionId = id ? Number(id) : undefined;
  const { data: submission, isLoading, isError } = useSubmission(submissionId as number);

  return (
    <PageWrapper>
      <Box px={6} pt={6} pb={6}>
        <Flex justify="flex-end" mb={4}>
          <GradientButton onClick={() => navigate('/dashboard')}>
            ← Back to Dashboard
          </GradientButton>
        </Flex>
        <Heading size="lg" mb={6}>
          Submission Details
        </Heading>

        {isLoading && (
          <Box mb={6}>
            <Spinner />
          </Box>
        )}
        {isError && <Text color="red.400">Failed to load submission.</Text>}

        {submission && (
          <GlassCard mb={6}>
            <Heading size="sm" mb={2}>
              {submission.studentName}
            </Heading>
            <Text color="gray.500" mb={1}>
              {submission.studentEmail}
            </Text>
            <Text mb={1}>
              <Text as="span" fontWeight="semibold">
                Assignment:
              </Text>{' '}
              {submission.assignmentName}
            </Text>
            <Text mb={1}>
              <ChakraLink href={submission.githubRepoUrl} color="purple.400" isExternal>
                {submission.githubRepoUrl}
              </ChakraLink>
            </Text>
            <Text fontSize="sm" color="gray.400">
              Submitted {new Date(submission.submittedAt).toLocaleString()}
            </Text>
          </GlassCard>
        )}

        {submissionId !== undefined && <EvaluationPanel submissionId={submissionId} />}
      </Box>
    </PageWrapper>
  );
}
