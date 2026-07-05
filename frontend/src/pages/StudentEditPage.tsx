import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Alert, AlertIcon, Center, Heading, Spinner } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { StudentForm, type StudentFormValues } from '../components/students/StudentForm';
import { studentService, type StudentCreateInput } from '../services/studentService';
import type { Student } from '../types';

function toFormValues(student: Student): Partial<StudentFormValues> {
  return {
    full_name: student.full_name,
    date_of_birth: student.date_of_birth,
    class_grade: student.class_grade,
    section: student.section ?? '',
    roll_number: student.roll_number ?? '',
    photo_url: student.photo_url ?? '',
    parent_name: student.parent_name ?? '',
    parent_email: student.parent_email ?? '',
    parent_phone: student.parent_phone ?? '',
    enrollment_date: student.enrollment_date,
    daily_fee: student.daily_fee !== null ? String(student.daily_fee) : '',
    scheduled_days: student.scheduled_days,
    monthly_fee: student.monthly_fee !== null ? String(student.monthly_fee) : '',
  };
}

export function StudentEditPage() {
  const { id } = useParams<{ id: string }>();
  const studentId = Number(id);
  const navigate = useNavigate();

  const [student, setStudent] = useState<Student | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    studentService
      .getStudent(studentId)
      .then((data) => {
        if (isMounted) setStudent(data);
      })
      .catch(() => {
        if (isMounted) setLoadError('Unable to load this student.');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [studentId]);

  const handleSubmit = async (payload: StudentCreateInput): Promise<void> => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await studentService.updateStudent(studentId, payload);
      navigate(`/students/${studentId}`);
    } catch {
      setErrorMessage('Unable to update student. Please check the form and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper>
      <Center py={10} px={4}>
        <GlassCard maxW="3xl" w="full">
          <Heading size="lg" mb={6}>
            Edit Student
          </Heading>

          {isLoading && (
            <Center py={10}>
              <Spinner color="brand.500" size="lg" />
            </Center>
          )}

          {!isLoading && loadError && (
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              {loadError}
            </Alert>
          )}

          {!isLoading && !loadError && student && (
            <StudentForm
              studentId={studentId}
              initialValues={toFormValues(student)}
              submitLabel="Save Changes"
              isSubmitting={isSubmitting}
              errorMessage={errorMessage}
              onSubmit={handleSubmit}
            />
          )}
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
