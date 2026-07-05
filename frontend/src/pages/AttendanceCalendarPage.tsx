import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, AlertIcon, Box, Button, Center, Heading, HStack, SimpleGrid, Spinner, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { attendanceService } from '../services/attendanceService';
import type { CalendarDaySummary } from '../types';

const WEEKDAY_HEADERS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

function pad2(value: number): string {
  return String(value).padStart(2, '0');
}

function toIsoDate(year: number, month: number, day: number): string {
  return `${year}-${pad2(month)}-${pad2(day)}`;
}

/**
 * Monthly calendar overview of attendance activity, the primary /attendance
 * route. Each date cell shows a compact summary of that day's attendance
 * records; clicking a date navigates to the per-date marking view.
 */
export function AttendanceCalendarPage() {
  const navigate = useNavigate();
  const today = useMemo(() => new Date(), []);
  const [viewedYear, setViewedYear] = useState(today.getFullYear());
  const [viewedMonth, setViewedMonth] = useState(today.getMonth() + 1); // 1-indexed
  const [summaryByDate, setSummaryByDate] = useState<Record<string, CalendarDaySummary>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = useCallback((year: number, month: number) => {
    setIsLoading(true);
    setError(null);
    attendanceService
      .getCalendarSummary(year, month)
      .then((result) => {
        const byDate: Record<string, CalendarDaySummary> = {};
        result.days.forEach((day) => {
          byDate[day.date] = day;
        });
        setSummaryByDate(byDate);
      })
      .catch(() => {
        setError('Unable to load attendance summary for this month.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    loadSummary(viewedYear, viewedMonth);
  }, [viewedYear, viewedMonth, loadSummary]);

  const goToPreviousMonth = (): void => {
    if (viewedMonth === 1) {
      setViewedYear((y) => y - 1);
      setViewedMonth(12);
    } else {
      setViewedMonth((m) => m - 1);
    }
  };

  const goToNextMonth = (): void => {
    if (viewedMonth === 12) {
      setViewedYear((y) => y + 1);
      setViewedMonth(1);
    } else {
      setViewedMonth((m) => m + 1);
    }
  };

  const goToToday = (): void => {
    setViewedYear(today.getFullYear());
    setViewedMonth(today.getMonth() + 1);
  };

  const daysInMonth = new Date(viewedYear, viewedMonth, 0).getDate();
  const firstWeekday = new Date(viewedYear, viewedMonth - 1, 1).getDay();

  const cells: (number | null)[] = [
    ...Array<null>(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  const todayIso = toIsoDate(today.getFullYear(), today.getMonth() + 1, today.getDate());

  return (
    <PageWrapper>
      <Box maxW="5xl" mx="auto" px={6} py={10}>
        <HStack justify="space-between" align="center" mb={8} flexWrap="wrap" gap={3}>
          <Heading size="xl">Attendance</Heading>
          <HStack>
            <Button variant="outline" borderRadius="full" onClick={goToToday}>
              Today
            </Button>
          </HStack>
        </HStack>

        <GlassCard mb={6}>
          <HStack justify="space-between" align="center">
            <Button borderRadius="full" onClick={goToPreviousMonth} aria-label="Previous month">
              &larr; Prev
            </Button>
            <Heading size="md">
              {MONTH_NAMES[viewedMonth - 1]} {viewedYear}
            </Heading>
            <Button borderRadius="full" onClick={goToNextMonth} aria-label="Next month">
              Next &rarr;
            </Button>
          </HStack>
        </GlassCard>

        {error && (
          <Alert status="error" borderRadius="xl" mb={4}>
            <AlertIcon />
            {error}
          </Alert>
        )}

        <GlassCard>
          {isLoading ? (
            <Center py={10}>
              <Spinner size="xl" color="brand.500" />
            </Center>
          ) : (
            <>
              <SimpleGrid columns={7} spacing={2} mb={2}>
                {WEEKDAY_HEADERS.map((label) => (
                  <Text key={label} fontSize="sm" fontWeight="semibold" textAlign="center" color="gray.600">
                    {label}
                  </Text>
                ))}
              </SimpleGrid>
              <SimpleGrid columns={7} spacing={2}>
                {cells.map((day, index) => {
                  if (day === null) {
                    return <Box key={`empty-${index}`} minH="80px" />;
                  }
                  const iso = toIsoDate(viewedYear, viewedMonth, day);
                  const summary = summaryByDate[iso];
                  const isToday = iso === todayIso;

                  return (
                    <Box
                      key={iso}
                      as="button"
                      type="button"
                      onClick={() => navigate(`/attendance/${iso}`)}
                      minH="80px"
                      p={2}
                      borderRadius="lg"
                      border="1px solid"
                      borderColor={isToday ? 'brand.400' : 'whiteAlpha.400'}
                      bg={isToday ? 'brand.50' : 'whiteAlpha.500'}
                      textAlign="left"
                      _hover={{ bg: 'brand.50', borderColor: 'brand.300' }}
                      transition="all 0.15s"
                    >
                      <Text fontSize="sm" fontWeight="bold">
                        {day}
                      </Text>
                      {summary ? (
                        <Text fontSize="xs" color="gray.700" mt={1}>
                          {summary.present}/{summary.total} present
                          {summary.absent > 0 ? ` · ${summary.absent} absent` : ''}
                          {summary.late > 0 ? ` · ${summary.late} late` : ''}
                        </Text>
                      ) : (
                        <Text fontSize="xs" color="gray.400" mt={1}>
                          No records
                        </Text>
                      )}
                    </Box>
                  );
                })}
              </SimpleGrid>
            </>
          )}
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}
