import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  AlertIcon,
  Box,
  Button,
  Center,
  Heading,
  HStack,
  Input,
  Radio,
  RadioGroup,
  Spinner,
  Stack,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import api from '../services/api';
import { attendanceService, type AttendanceEntry } from '../services/attendanceService';
import type { AttendanceStatus, StudentListItem } from '../types';

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Per-date attendance marking view, routed at /attendance/:date. Lists all of
 * the teacher's active students (optionally filtered by class/grade) with
 * present/absent/late controls and bulk-submit for that single date.
 */
export function AttendanceMarkingPage() {
  const { date: routeDate } = useParams<{ date: string }>();
  const navigate = useNavigate();
  const date = routeDate ?? todayIsoDate();
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [classGrade, setClassGrade] = useState('');
  const [marks, setMarks] = useState<Record<number, AttendanceStatus>>({});
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setError(null);

    api
      .get<StudentListItem[]>('/students', {
        params: classGrade ? { class_grade: classGrade } : undefined,
      })
      .then((response) => {
        if (!isMounted) {
          return;
        }
        setStudents(response.data);
        setMarks((prev) => {
          const next: Record<number, AttendanceStatus> = {};
          response.data.forEach((s) => {
            next[s.id] = prev[s.id] ?? 'present';
          });
          return next;
        });
      })
      .catch(() => {
        if (isMounted) {
          setError('Unable to load students right now.');
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
  }, [classGrade]);

  const activeStudents = useMemo(() => students.filter((s) => s.is_active), [students]);

  const setMark = (studentId: number, status: AttendanceStatus): void => {
    setMarks((prev) => ({ ...prev, [studentId]: status }));
  };

  const setNote = (studentId: number, value: string): void => {
    setNotes((prev) => ({ ...prev, [studentId]: value }));
  };

  const handleSubmit = async (): Promise<void> => {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    const entries: AttendanceEntry[] = activeStudents.map((s) => ({
      student_id: s.id,
      date,
      status: marks[s.id] ?? 'present',
      notes: notes[s.id]?.trim() ? notes[s.id].trim() : null,
    }));

    try {
      await attendanceService.bulkMarkAttendance(entries);
      setSuccessMessage(`Attendance for ${date} saved for ${entries.length} student(s).`);
    } catch {
      setError('Unable to save attendance right now. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper>
      <Box maxW="5xl" mx="auto" px={6} py={10}>
        <HStack justify="space-between" align="center" mb={8} flexWrap="wrap" gap={3}>
          <Heading size="xl">Mark Attendance - {date}</Heading>
          <Button variant="outline" borderRadius="full" onClick={() => navigate('/attendance')}>
            Back to Calendar
          </Button>
        </HStack>

        <GlassCard mb={6}>
          <HStack spacing={6} flexWrap="wrap">
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={1}>
                Class / Grade
              </Text>
              <Input
                placeholder="e.g. 5"
                value={classGrade}
                onChange={(e) => setClassGrade(e.target.value)}
                borderRadius="xl"
                maxW="200px"
              />
            </Box>
          </HStack>
        </GlassCard>

        {error && (
          <Alert status="error" borderRadius="xl" mb={4}>
            <AlertIcon />
            {error}
          </Alert>
        )}
        {successMessage && (
          <Alert status="success" borderRadius="xl" mb={4}>
            <AlertIcon />
            {successMessage}
          </Alert>
        )}

        <GlassCard>
          {isLoading ? (
            <Center py={10}>
              <Spinner size="xl" color="brand.500" />
            </Center>
          ) : activeStudents.length === 0 ? (
            <Text color="gray.600">No students found for this class.</Text>
          ) : (
            <Stack spacing={6}>
              <Box overflowX="auto">
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Student</Th>
                      <Th>Roll No.</Th>
                      <Th>Status</Th>
                      <Th>Notes</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {activeStudents.map((s) => (
                      <Tr key={s.id}>
                        <Td>{s.full_name}</Td>
                        <Td>{s.roll_number ?? '-'}</Td>
                        <Td>
                          <RadioGroup
                            value={marks[s.id] ?? 'present'}
                            onChange={(value) => setMark(s.id, value as AttendanceStatus)}
                          >
                            <HStack spacing={4}>
                              <Radio value="present" colorScheme="green">
                                Present
                              </Radio>
                              <Radio value="absent" colorScheme="red">
                                Absent
                              </Radio>
                              <Radio value="late" colorScheme="yellow">
                                Late
                              </Radio>
                            </HStack>
                          </RadioGroup>
                        </Td>
                        <Td>
                          <Input
                            size="sm"
                            borderRadius="lg"
                            placeholder="Optional note"
                            value={notes[s.id] ?? ''}
                            onChange={(e) => setNote(s.id, e.target.value)}
                          />
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>

              <HStack justify="flex-end">
                <GradientButton onClick={handleSubmit} isLoading={isSubmitting}>
                  Save Attendance
                </GradientButton>
              </HStack>
            </Stack>
          )}
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}
