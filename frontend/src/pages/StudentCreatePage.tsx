import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Center, Heading } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { StudentForm } from '../components/students/StudentForm';
import { studentService, type StudentCreateInput } from '../services/studentService';

export function StudentCreatePage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (payload: StudentCreateInput): Promise<void> => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const student = await studentService.createStudent(payload);
      navigate(`/students/${student.id}`);
    } catch {
      setErrorMessage('Unable to create student. Please check the form and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper>
      <Center py={10} px={4}>
        <GlassCard maxW="3xl" w="full">
          <Heading size="lg" mb={6}>
            Add Student
          </Heading>
          <StudentForm
            submitLabel="Create Student"
            isSubmitting={isSubmitting}
            errorMessage={errorMessage}
            onSubmit={handleSubmit}
          />
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
