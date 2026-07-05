import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  AlertIcon,
  Badge,
  Center,
  Heading,
  HStack,
  Input,
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
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../context/AuthContext';
import { studentService, type StudentListItem } from '../services/studentService';

export function StudentListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isTeacher = user?.role === 'teacher';

  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [classFilter, setClassFilter] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setError(null);

    studentService
      .listStudents({
        class_grade: classFilter || undefined,
        section: sectionFilter || undefined,
      })
      .then((data) => {
        if (isMounted) setStudents(data);
      })
      .catch(() => {
        if (isMounted) setError('Unable to load students right now.');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [classFilter, sectionFilter]);

  return (
    <PageWrapper>
      <Center py={10} px={4}>
        <GlassCard maxW="4xl" w="full">
          <HStack justify="space-between" mb={6} flexWrap="wrap" gap={3}>
            <Heading size="lg">{isTeacher ? 'My Students' : 'My Children'}</Heading>
            {isTeacher && (
              <GradientButton onClick={() => navigate('/students/new')}>
                Add Student
              </GradientButton>
            )}
          </HStack>

          {isTeacher && (
            <HStack mb={6} spacing={4}>
              <Input
                placeholder="Filter by class/grade"
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                maxW="200px"
              />
              <Input
                placeholder="Filter by section"
                value={sectionFilter}
                onChange={(e) => setSectionFilter(e.target.value)}
                maxW="200px"
              />
            </HStack>
          )}

          {isLoading && (
            <Center py={10}>
              <Spinner color="brand.500" size="lg" />
            </Center>
          )}

          {!isLoading && error && (
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              {error}
            </Alert>
          )}

          {!isLoading && !error && students.length === 0 && (
            <Text color="gray.600">No students found.</Text>
          )}

          {!isLoading && !error && students.length > 0 && (
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Name</Th>
                  <Th>Class</Th>
                  <Th>Section</Th>
                  <Th>Roll #</Th>
                  <Th>Status</Th>
                </Tr>
              </Thead>
              <Tbody>
                {students.map((student) => (
                  <Tr
                    key={student.id}
                    onClick={() => navigate(`/students/${student.id}`)}
                    cursor="pointer"
                    _hover={{ bg: 'whiteAlpha.500' }}
                  >
                    <Td>{student.full_name}</Td>
                    <Td>{student.class_grade}</Td>
                    <Td>{student.section ?? '-'}</Td>
                    <Td>{student.roll_number ?? '-'}</Td>
                    <Td>
                      <Badge colorScheme={student.is_active ? 'green' : 'gray'}>
                        {student.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
