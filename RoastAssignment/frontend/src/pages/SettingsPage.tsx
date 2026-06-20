import { useState } from 'react';
import { Box, FormControl, FormLabel, Heading, Stack, Switch, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';

export function SettingsPage(): JSX.Element {
  // TODO: replace local state with a real `GET/PUT /users/me/preferences`
  // backend call once that endpoint exists; persist to the server instead
  // of only in component state.
  const [notificationEmailsEnabled, setNotificationEmailsEnabled] = useState(true);

  return (
    <PageWrapper>
      <Box maxW="3xl" mx="auto" px={4} py={8}>
        <Heading size="lg" mb={6}>
          Settings
        </Heading>

        <GlassCard>
          <Heading size="sm" mb={4}>
            Notifications
          </Heading>
          <Stack spacing={4}>
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel htmlFor="notification-emails" mb={0}>
                  Email notifications
                </FormLabel>
                <Text fontSize="sm" color="gray.500">
                  Receive an email when your evaluation results are ready.
                </Text>
              </Box>
              <Switch
                id="notification-emails"
                isChecked={notificationEmailsEnabled}
                onChange={(event) => setNotificationEmailsEnabled(event.target.checked)}
                colorScheme="purple"
              />
            </FormControl>
          </Stack>
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}

export default SettingsPage;
