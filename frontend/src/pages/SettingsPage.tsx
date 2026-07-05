import { useState, type FormEvent } from 'react';
import { Box, FormControl, FormLabel, Heading, Input, Stack, Text } from '@chakra-ui/react';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import type { User } from '../types';

export function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setIsSaving(true);
    setStatus('idle');
    try {
      await api.put<User>('/auth/me', { full_name: fullName });
      await refreshUser();
      setStatus('success');
    } catch {
      setStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Box maxW="2xl" mx="auto" px={6} py={10}>
      <Heading size="xl" mb={8}>
        Settings
      </Heading>
      <GlassCard>
        <form onSubmit={handleSubmit}>
          <Stack spacing={5}>
            <FormControl>
              <FormLabel>Email</FormLabel>
              <Input value={user?.email ?? ''} isReadOnly isDisabled />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Full Name</FormLabel>
              <Input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                minLength={1}
                maxLength={150}
              />
            </FormControl>
            {status === 'success' && <Text color="green.600">Profile updated successfully.</Text>}
            {status === 'error' && <Text color="red.600">Failed to update profile. Please try again.</Text>}
            <GradientButton type="submit" isLoading={isSaving} alignSelf="flex-start">
              Save Changes
            </GradientButton>
          </Stack>
        </form>
      </GlassCard>
    </Box>
  );
}
