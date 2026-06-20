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
import { MarkdownLite } from '../ui/MarkdownLite';
import { parseRoastSections, RoastSectionKey } from '../../utils/parseRoast';

interface EvaluationPanelProps {
  submissionId: number;
}

const ROAST_SECTION_STYLE: Record<
  RoastSectionKey,
  { emoji: string; defaultTitle: string; bg: string; accentColor: string; titleColor: string; textColor: string }
> = {
  good: {
    emoji: '🎉',
    defaultTitle: 'The Good Stuff',
    bg: 'green.50',
    accentColor: 'green.400',
    titleColor: 'green.700',
    textColor: 'gray.700',
  },
  roast: {
    emoji: '🔥',
    defaultTitle: 'The Roast',
    bg: 'orange.50',
    accentColor: 'orange.400',
    titleColor: 'orange.700',
    textColor: 'gray.700',
  },
  overall: {
    emoji: '📊',
    defaultTitle: 'Overall Verdict',
    bg: 'purple.50',
    accentColor: 'purple.400',
    titleColor: 'purple.700',
    textColor: 'gray.700',
  },
  other: {
    emoji: '📝',
    defaultTitle: 'Notes',
    bg: 'gray.50',
    accentColor: 'gray.400',
    titleColor: 'gray.700',
    textColor: 'gray.700',
  },
};

function toPercent(score: number): number {
  return Math.round(score * 100);
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

  const roastSections = parseRoastSections(evaluation.aiRoastText);

  return (
    <Box>
      <Heading size="sm" mb={3}>
        AI Roast
      </Heading>
      {roastSections.length === 0 ? (
        <GlassCard mb={4} bg="gray.50">
          <Text color="gray.700">{evaluation.aiRoastText}</Text>
        </GlassCard>
      ) : (
        roastSections.map((section, i) => {
          const style = ROAST_SECTION_STYLE[section.key];
          return (
            <GlassCard
              key={i}
              mb={4}
              bg={style.bg}
              borderColor="transparent"
              borderLeftWidth="4px"
              borderLeftColor={style.accentColor}
              boxShadow="md"
            >
              <Heading size="md" mb={3} color={style.titleColor}>
                {style.emoji} {section.title || style.defaultTitle}
              </Heading>
              <MarkdownLite text={section.content} color={style.textColor} />
            </GlassCard>
          );
        })
      )}

      <GlassCard mb={4}>
        <Flex gap={8} wrap="wrap">
          <Stat>
            <StatLabel>AI Score</StatLabel>
            <StatNumber>{toPercent(evaluation.aiScore)}%</StatNumber>
            <Progress value={toPercent(evaluation.aiScore)} colorScheme="purple" rounded="full" mt={2} />
          </Stat>
          <Stat>
            <StatLabel>Static Analysis Score</StatLabel>
            <StatNumber>{toPercent(evaluation.staticAnalysisScore)}%</StatNumber>
            <Progress
              value={toPercent(evaluation.staticAnalysisScore)}
              colorScheme="pink"
              rounded="full"
              mt={2}
            />
          </Stat>
          <Stat>
            <StatLabel>Overall Score</StatLabel>
            <StatNumber>{toPercent(evaluation.overallScore)}%</StatNumber>
            <Progress value={toPercent(evaluation.overallScore)} colorScheme="green" rounded="full" mt={2} />
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
