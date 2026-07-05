import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Center,
  Heading,
  HStack,
  Input,
  Select,
  Spinner,
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
import api from '../services/api';
import { attendanceService } from '../services/attendanceService';
import type { AttendanceRecord, AttendanceStatus, StudentListItem } from '../types';

const STATUS_COLOR: Record<AttendanceStatus, string> = {
  present: 'green',
  absent: 'red',
  late: 'yellow',
};

export function AttendanceHistoryPage() {
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [studentId, setStudentId] = useState<string>('');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<StudentListItem[]>('/students')
      .then((response) => setStudents(response.data))
      .catch(() => {
        /* Student roster is optional context for filtering; ignore failures. */
      });
  }, []);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setError(null);

    attendanceService
      .queryAttendance({
        student_id: studentId ? Number(studentId) : undefined,
      })
      .then((data) => {
        if (isMounted) {
          setRecords(data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setError('Unable to load attendance history right now.');
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

  const studentNameById = useMemo(() => {
    const map = new Map<number, string>();
    students.forEach((s) => map.set(s.id, s.full_name));
    return map;
  }, [students]);

  const filteredRecords = useMemo(() => {
    return records.filter((record) => {
      if (fromDate && record.date < fromDate) {
        return false;
      }
      if (toDate && record.date > toDate) {
        return false;
      }
      return true;
    });
  }, [records, fromDate, toDate]);

  return (
    <PageWrapper>
      <Box maxW="5xl" mx="auto" px={6} py={10}>
        <Heading size="xl" mb={8}>
          Attendance History
        </Heading>

        <GlassCard mb={6}>
          <HStack spacing={6} flexWrap="wrap">
            {students.length > 0 && (
              <Box>
                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  Student
                </Text>
                <Select
                  placeholder="All students"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  borderRadius="xl"
                  maxW="220px"
                >
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.full_name}
                    </option>
                  ))}
                </Select>
              </Box>
            )}
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={1}>
                From
              </Text>
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                borderRadius="xl"
                maxW="200px"
              />
            </Box>
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={1}>
                To
              </Text>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
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

        <GlassCard>
          {isLoading ? (
            <Center py={10}>
              <Spinner size="xl" color="brand.500" />
            </Center>
          ) : filteredRecords.length === 0 ? (
            <Text color="gray.600">No attendance records found for the selected filters.</Text>
          ) : (
            <Box overflowX="auto">
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Date</Th>
                    <Th>Student</Th>
                    <Th>Status</Th>
                    <Th>Notes</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {filteredRecords.map((record) => (
                    <Tr key={record.id}>
                      <Td>{record.date}</Td>
                      <Td>{studentNameById.get(record.student_id) ?? `#${record.student_id}`}</Td>
                      <Td>
                        <Badge colorScheme={STATUS_COLOR[record.status]} borderRadius="full" px={2}>
                          {record.status}
                        </Badge>
                      </Td>
                      <Td>{record.notes ?? '-'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}
