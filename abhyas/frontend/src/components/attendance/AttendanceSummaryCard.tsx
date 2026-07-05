import { useEffect, useState } from 'react';
import { Center, Heading, Progress, SimpleGrid, Spinner, Stack, Text } from '@chakra-ui/react';
import { GlassCard } from '../ui/GlassCard';
import { attendanceService } from '../../services/attendanceService';
import type { AttendanceSummary } from '../../types';

interface AttendanceSummaryCardProps {
  studentId: number;
}

interface BreakdownTileProps {
  label: string;
  value: number;
  colorScheme: string;
}

function BreakdownTile({ label, value, colorScheme }: BreakdownTileProps) {
  return (
    <Stack spacing={0} align="center">
      <Heading size="md" color={`${colorScheme}.600`}>
        {value}
      </Heading>
      <Text fontSize="xs" color="gray.600">
        {label}
      </Text>
    </Stack>
  );
}

/**
 * Reusable card showing a student's attendance percentage and
 * present/absent/late breakdown. Designed to be dropped into
 * StudentDetailPage (and anywhere else a quick attendance snapshot
 * for a single student is useful).
 */
export function AttendanceSummaryCard({ studentId }: AttendanceSummaryCardProps) {
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setError(null);

    attendanceService
      .getStudentSummary(studentId)
      .then((data) => {
        if (isMounted) {
          setSummary(data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setError('Unable to load attendance summary right now.');
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [studentId]);

  if (isLoading) {
    return (
      <GlassCard>
        <Center py={6}>
          <Spinner color="brand.500" />
        </Center>
      </GlassCard>
    );
  }

  if (error || !summary) {
    return (
      <GlassCard>
        <Text color="red.600">{error ?? 'No attendance data available.'}</Text>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <Heading size="md" mb={4}>
        Attendance
      </Heading>

      <Progress
        value={summary.attendance_percentage}
        colorScheme="purple"
        borderRadius="full"
        size="lg"
        mb={2}
      />
      <Text fontSize="sm" color="gray.600" mb={4}>
        {summary.attendance_percentage}% present over {summary.total_days} day
        {summary.total_days === 1 ? '' : 's'}
      </Text>

      <SimpleGrid columns={3} spacing={4}>
        <BreakdownTile label="Present" value={summary.present_days} colorScheme="green" />
        <BreakdownTile label="Absent" value={summary.absent_days} colorScheme="red" />
        <BreakdownTile label="Late" value={summary.late_days} colorScheme="yellow" />
      </SimpleGrid>
    </GlassCard>
  );
}
