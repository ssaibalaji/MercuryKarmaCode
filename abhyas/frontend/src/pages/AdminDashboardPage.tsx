import { useEffect, useState } from 'react';
import { Box, Center, Heading, SimpleGrid, Spinner, Text } from '@chakra-ui/react';
import { GlassCard } from '../components/ui/GlassCard';
import { adminService } from '../services/adminService';
import type { AdminStats } from '../types';

interface StatTileProps {
  label: string;
  value: string;
}

function StatTile({ label, value }: StatTileProps) {
  return (
    <GlassCard>
      <Text fontSize="sm" color="gray.600">
        {label}
      </Text>
      <Heading size="lg" mt={2}>
        {value}
      </Heading>
    </GlassCard>
  );
}

export function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    adminService
      .getStats()
      .then(setStats)
      .catch(() => setError('Unable to load platform stats right now.'))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <Box maxW="6xl" mx="auto" px={6} py={10}>
      <Heading size="xl" mb={8}>
        Admin Dashboard
      </Heading>
      {isLoading ? (
        <Center minH="40vh">
          <Spinner size="xl" color="brand.500" />
        </Center>
      ) : error || !stats ? (
        <GlassCard>
          <Text color="red.600">{error ?? 'No stats available.'}</Text>
        </GlassCard>
      ) : (
        <SimpleGrid columns={{ base: 1, sm: 2, lg: 5 }} spacing={6}>
          <StatTile label="Total Users" value={String(stats.total_users)} />
          <StatTile label="Teachers" value={String(stats.total_teachers)} />
          <StatTile label="Parents" value={String(stats.total_parents)} />
          <StatTile label="Students" value={String(stats.total_students)} />
          <StatTile
            label="Payments This Month"
            value={`₹${stats.total_payments_this_month.toLocaleString()}`}
          />
        </SimpleGrid>
      )}
    </Box>
  );
}
