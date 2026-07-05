import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Center,
  Heading,
  HStack,
  Progress,
  SimpleGrid,
  Spinner,
  Stack,
  Text,
} from '@chakra-ui/react';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../context/AuthContext';
import { dashboardService } from '../services/dashboardService';
import type { DashboardStats } from '../types';

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

function TeacherDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    dashboardService
      .getStats()
      .then(setStats)
      .catch(() => setError('Unable to load dashboard stats right now.'))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <Center minH="40vh">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (error || !stats) {
    return (
      <GlassCard>
        <Text color="red.600">{error ?? 'No dashboard data available.'}</Text>
      </GlassCard>
    );
  }

  return (
    <Stack spacing={8}>
      <HStack justify="flex-end">
        <GradientButton onClick={() => navigate('/students/new')}>
          Add Student
        </GradientButton>
      </HStack>

      <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={6}>
        <StatTile label="Total Students" value={String(stats.total_students)} />
        <StatTile
          label={`Attendance (${stats.attendance_reference_date})`}
          value={`${stats.attendance_percentage_recent}%`}
        />
        <StatTile label="Overdue Fees" value={String(stats.overdue_fees_count)} />
        <StatTile
          label="Fees Collected This Month"
          value={`₹${stats.total_fees_collected_this_month.toLocaleString()}`}
        />
      </SimpleGrid>

      <GlassCard>
        <Heading size="md" mb={2}>
          Attendance Snapshot
        </Heading>
        <Progress
          value={stats.attendance_percentage_recent}
          colorScheme="purple"
          borderRadius="full"
          size="lg"
        />
        <Text mt={2} fontSize="sm" color="gray.600">
          {stats.attendance_percentage_recent}% present on {stats.attendance_reference_date}
        </Text>
      </GlassCard>

      <GlassCard>
        <Heading size="md" mb={4}>
          Recent Activity
        </Heading>
        {stats.recent_activity.length === 0 ? (
          <Text color="gray.600">No recent activity yet.</Text>
        ) : (
          <Stack spacing={3}>
            {stats.recent_activity.map((entry, index) => (
              <Box key={index} borderBottomWidth={index === stats.recent_activity.length - 1 ? 0 : '1px'} pb={2}>
                <Text fontWeight="medium">{entry.description}</Text>
                <Text fontSize="xs" color="gray.500">
                  {new Date(entry.timestamp).toLocaleString()}
                </Text>
              </Box>
            ))}
          </Stack>
        )}
      </GlassCard>
    </Stack>
  );
}

function ParentDashboard() {
  return (
    <GlassCard>
      <Heading size="md" mb={2}>
        Welcome
      </Heading>
      <Text color="gray.600">
        A parent-focused dashboard with your child&apos;s attendance and fee summary is coming soon.
        For now, please check the Students and Fees sections for details.
      </Text>
    </GlassCard>
  );
}

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <Box maxW="6xl" mx="auto" px={6} py={10}>
      <Heading size="xl" mb={8}>
        Dashboard
      </Heading>
      {user?.role === 'teacher' ? <TeacherDashboard /> : <ParentDashboard />}
    </Box>
  );
}
