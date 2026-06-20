import {
  Box,
  Flex,
  Heading,
  Progress,
  Spinner,
  Stat,
  StatLabel,
  StatNumber,
  Text,
} from '@chakra-ui/react';
import { useAuth } from '../../hooks/useAuth';
import { useEvaluation, useRetryEvaluation } from '../../hooks/useEvaluation';
import { GlassCard } from '../ui/GlassCard';
import { GradientButton } from '../ui/GradientButton';

interface EvaluationPanelProps {
  submissionId: number;
}

function ReportList({ report }: { report: Record<string, unknown> }) {
  const entries = Object.entries(report);
  if (entries.length === 0) {
    return <Text color="gray.500">No static analysis details available.</Text>;
  }
  return (
    <Box>
      {entries.map(([key, value]) => (
        <Flex key={key} justify="space-between" py={1} borderBottom="1px solid" borderColor="whiteAlpha.200">
          <Text fontWeight="semibold">{key}</Text>
          <Text color="gray.500">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</Text>
        </Flex>
      ))}
    </Box>
  );
}

export function EvaluationPanel({ submissionId }: EvaluationPanelProps) {
  const { user } = useAuth();
  const { data: evaluation, isLoading, isError } = useEvaluation(submissionId);
  const retryEvaluation = useRetryEvaluation();

  const canRetry = user?.role !== 'student';

  if (isLoading) {
    return (
      <GlassCard>
        <Flex align="center" gap={3}>
          <Spinner />
          <Text>Loading evaluation...</Text>
        </Flex>
      </GlassCard>
    );
  }

  if (isError || !evaluation) {
    return (
      <GlassCard>
        <Text color="red.400">Unable to load evaluation for this submission.</Text>
      </GlassCard>
    );
  }

  if (evaluation.status === 'pending' || evaluation.status === 'running') {
    return (
      <GlassCard>
        <Flex align="center" gap={3}>
          <Spinner />
          <Text>Evaluation is {evaluation.status}...</Text>
        </Flex>
      </GlassCard>
    );
  }

  if (evaluation.status === 'failed') {
    return (
      <GlassCard>
        <Heading size="sm" color="red.400" mb={2}>
          Evaluation failed
        </Heading>
        <Text color="gray.500" mb={4}>
          Something went wrong while evaluating this submission.
        </Text>
        {canRetry && (
          <GradientButton
            onClick={() => retryEvaluation.mutate(submissionId)}
            isLoading={retryEvaluation.isPending}
          >
            Retry
          </GradientButton>
        )}
      </GlassCard>
    );
  }

  return (
    <Box>
      <GlassCard mb={4}>
        <Heading size="sm" mb={2}>
          AI Roast
        </Heading>
        <Text fontFamily="mono" whiteSpace="pre-wrap" color="pink.300">
          {evaluation.aiRoastText}
        </Text>
      </GlassCard>

      <GlassCard mb={4}>
        <Flex gap={8} wrap="wrap">
          <Stat>
            <StatLabel>AI Score</StatLabel>
            <StatNumber>{evaluation.aiScore}</StatNumber>
            <Progress value={evaluation.aiScore} colorScheme="purple" rounded="full" mt={2} />
          </Stat>
          <Stat>
            <StatLabel>Static Analysis Score</StatLabel>
            <StatNumber>{evaluation.staticAnalysisScore}</StatNumber>
            <Progress value={evaluation.staticAnalysisScore} colorScheme="pink" rounded="full" mt={2} />
          </Stat>
          <Stat>
            <StatLabel>Overall Score</StatLabel>
            <StatNumber>{evaluation.overallScore}</StatNumber>
            <Progress value={evaluation.overallScore} colorScheme="green" rounded="full" mt={2} />
          </Stat>
        </Flex>
      </GlassCard>

      <GlassCard>
        <Heading size="sm" mb={3}>
          Static Analysis Report
        </Heading>
        <ReportList report={evaluation.staticAnalysisReport} />
      </GlassCard>
    </Box>
  );
}
