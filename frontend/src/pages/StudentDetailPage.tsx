import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  AlertIcon,
  Badge,
  Center,
  Heading,
  HStack,
  SimpleGrid,
  Spinner,
  Stack,
  Text,
} from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { AttendanceSummaryCard } from '../components/attendance/AttendanceSummaryCard';
import { FeeSummaryCard } from '../components/fees/FeeSummaryCard';
import { useAuth } from '../context/AuthContext';
import { studentService } from '../services/studentService';
import type { Student } from '../types';

const DAY_LABELS: Record<string, string> = {
  sun: 'Sunday',
  mon: 'Monday',
  tue: 'Tuesday',
  wed: 'Wednesday',
  thu: 'Thursday',
  fri: 'Friday',
  sat: 'Saturday',
};

export function StudentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const studentId = Number(id);
  const navigate = useNavigate();
  const { user } = useAuth();
  const isTeacher = user?.role === 'teacher';

  const [student, setStudent] = useState<Student | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setError(null);
    studentService
      .getStudent(studentId)
      .then((data) => {
        if (isMounted) setStudent(data);
      })
      .catch(() => {
        if (isMounted) setError('Unable to load this student.');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [studentId]);

  const handleDeactivate = async (): Promise<void> => {
    await studentService.deleteStudent(studentId);
    navigate('/students');
  };

  if (isLoading) {
    return (
      <PageWrapper>
        <Center minH="100vh">
          <Spinner size="xl" color="brand.500" />
        </Center>
      </PageWrapper>
    );
  }

  if (error || !student) {
    return (
      <PageWrapper>
        <Center minH="100vh" px={4}>
          <Alert status="error" borderRadius="md" maxW="md">
            <AlertIcon />
            {error ?? 'Student not found.'}
          </Alert>
        </Center>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <Center py={10} px={4}>
        <Stack spacing={6} maxW="4xl" w="full">
          <GlassCard>
            <HStack justify="space-between" align="flex-start" flexWrap="wrap" gap={3}>
              <Stack spacing={1}>
                <Heading size="lg">{student.full_name}</Heading>
                <Text color="gray.600">
                  Class {student.class_grade}
                  {student.section ? ` - ${student.section}` : ''}
                  {student.roll_number ? ` - Roll #${student.roll_number}` : ''}
                </Text>
                <Badge
                  alignSelf="flex-start"
                  colorScheme={student.is_active ? 'green' : 'gray'}
                >
                  {student.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </Stack>

              {isTeacher && (
                <HStack>
                  <GradientButton onClick={() => navigate(`/students/${studentId}/edit`)}>
                    Edit
                  </GradientButton>
                  {student.is_active && (
                    <GradientButton
                      bgGradient="linear(to-r, red.500, orange.500)"
                      onClick={() => void handleDeactivate()}
                    >
                      Deactivate
                    </GradientButton>
                  )}
                </HStack>
              )}
            </HStack>

            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mt={6}>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Date of birth
                </Text>
                <Text>{student.date_of_birth}</Text>
              </Stack>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Enrollment date
                </Text>
                <Text>{student.enrollment_date}</Text>
              </Stack>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Parent name
                </Text>
                <Text>{student.parent_name ?? 'Not provided'}</Text>
              </Stack>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Parent email
                </Text>
                <Text>{student.parent_email ?? 'Not provided'}</Text>
              </Stack>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Parent phone
                </Text>
                <Text>{student.parent_phone ?? 'Not provided'}</Text>
              </Stack>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Parent account linked
                </Text>
                <Text>{student.parent_user_id ? 'Yes' : 'Not yet linked'}</Text>
              </Stack>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Daily fee
                </Text>
                <Text>
                  {student.daily_fee !== null ? `₹${student.daily_fee.toLocaleString()}` : 'Not set'}
                </Text>
              </Stack>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Classes per week
                </Text>
                <Text>
                  {student.scheduled_days.length > 0
                    ? student.scheduled_days.map((day) => DAY_LABELS[day] ?? day).join(', ')
                    : 'Not set'}
                </Text>
              </Stack>
              <Stack spacing={0}>
                <Text fontSize="sm" color="gray.600">
                  Monthly fee
                </Text>
                <Text>
                  {student.monthly_fee !== null
                    ? `₹${student.monthly_fee.toLocaleString()}`
                    : 'Not set'}
                </Text>
              </Stack>
            </SimpleGrid>
          </GlassCard>

          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
            <AttendanceSummaryCard studentId={studentId} />
            <FeeSummaryCard studentId={studentId} />
          </SimpleGrid>
        </Stack>
      </Center>
    </PageWrapper>
  );
}
