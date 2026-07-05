import { Center, Heading, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';

interface PlaceholderPageProps {
  title: string;
}

/**
 * Temporary placeholder used for routes that have not yet been implemented
 * by their respective module agent (Auth, Students, Attendance, Fees, Admin).
 */
export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <PageWrapper>
      <Center minH="100vh">
        <GlassCard maxW="md" textAlign="center">
          <Heading size="lg" mb={2}>
            {title}
          </Heading>
          <Text color="gray.600">This page is coming soon.</Text>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
