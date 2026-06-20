import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Heading, Stack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { AnimatedInput } from '../components/ui/AnimatedInput';
import { GradientButton } from '../components/ui/GradientButton';
import { useCreateSubmission } from '../hooks/useSubmissions';

interface FormErrors {
  assignmentName?: string;
  githubRepoUrl?: string;
}

const GITHUB_REPO_URL_RE = /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/;

function validate(assignmentName: string, githubRepoUrl: string): FormErrors {
  const errors: FormErrors = {};
  if (!assignmentName.trim()) {
    errors.assignmentName = 'Assignment name is required';
  }
  if (!githubRepoUrl.trim()) {
    errors.githubRepoUrl = 'GitHub repo URL is required';
  } else if (!GITHUB_REPO_URL_RE.test(githubRepoUrl.trim())) {
    errors.githubRepoUrl = 'Enter a valid GitHub repo URL, e.g. https://github.com/owner/repo';
  }
  return errors;
}

export function SubmitAssignmentPage(): JSX.Element {
  const navigate = useNavigate();
  const createSubmission = useCreateSubmission();
  const [assignmentName, setAssignmentName] = useState('');
  const [githubRepoUrl, setGithubRepoUrl] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setSubmitError(null);

    const validationErrors = validate(assignmentName, githubRepoUrl);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    try {
      const submission = await createSubmission.mutateAsync({
        assignmentName: assignmentName.trim(),
        githubRepoUrl: githubRepoUrl.trim(),
      });
      navigate(`/submissions/${submission.id}`, { replace: true });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setSubmitError(message ?? 'Could not submit your assignment. Please try again.');
    }
  };

  return (
    <PageWrapper>
      <Box maxW="lg" mx="auto" px={4} py={8}>
        <Heading size="lg" mb={2}>
          Submit Assignment
        </Heading>
        <Text color="gray.500" mb={6}>
          Share your GitHub repo link to kick off the AI roast + evaluation.
        </Text>

        <GlassCard>
          <Stack as="form" spacing={4} onSubmit={handleSubmit} noValidate>
            <AnimatedInput
              type="text"
              label="Assignment name"
              placeholder="e.g. Week 3 - REST API"
              value={assignmentName}
              onChange={(event) => setAssignmentName(event.target.value)}
              error={errors.assignmentName}
            />
            <AnimatedInput
              type="url"
              label="GitHub repo URL"
              placeholder="https://github.com/owner/repo"
              value={githubRepoUrl}
              onChange={(event) => setGithubRepoUrl(event.target.value)}
              error={errors.githubRepoUrl}
            />
            {submitError && (
              <Text color="red.500" fontSize="sm">
                {submitError}
              </Text>
            )}
            <GradientButton type="submit" disabled={createSubmission.isPending} w="full">
              {createSubmission.isPending ? 'Submitting…' : 'Submit'}
            </GradientButton>
          </Stack>
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}

export default SubmitAssignmentPage;
