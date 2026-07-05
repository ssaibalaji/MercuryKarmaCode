import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react';
import {
  Alert,
  AlertIcon,
  Button,
  ButtonGroup,
  FormControl,
  FormLabel,
  HStack,
  Input,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  SimpleGrid,
  Stack,
  Text,
} from '@chakra-ui/react';
import { GradientButton } from '../ui/GradientButton';
import { studentService, type StudentCreateInput } from '../../services/studentService';
import type { ScheduledDay } from '../../types';

export interface StudentFormValues {
  full_name: string;
  date_of_birth: string;
  class_grade: string;
  section: string;
  roll_number: string;
  photo_url: string;
  parent_name: string;
  parent_email: string;
  parent_phone: string;
  enrollment_date: string;
  daily_fee: string;
  scheduled_days: string[];
  monthly_fee: string;
}

const EMPTY_VALUES: StudentFormValues = {
  full_name: '',
  date_of_birth: '',
  class_grade: '',
  section: '',
  roll_number: '',
  photo_url: '',
  parent_name: '',
  parent_email: '',
  parent_phone: '',
  enrollment_date: '',
  daily_fee: '',
  scheduled_days: [],
  monthly_fee: '',
};

const DAY_OPTIONS: { code: ScheduledDay; label: string }[] = [
  { code: 'sun', label: 'Sun' },
  { code: 'mon', label: 'Mon' },
  { code: 'tue', label: 'Tue' },
  { code: 'wed', label: 'Wed' },
  { code: 'thu', label: 'Thu' },
  { code: 'fri', label: 'Fri' },
  { code: 'sat', label: 'Sat' },
];

const DAY_TO_JS_INDEX: Record<string, number> = {
  sun: 0,
  mon: 1,
  tue: 2,
  wed: 3,
  thu: 4,
  fri: 5,
  sat: 6,
};

/**
 * Client-side estimate of the monthly fee for the CURRENT calendar month,
 * used only on the create form (before a student id exists, so the real
 * backend preview endpoint can't be called yet). Counts how many times each
 * scheduled weekday occurs this month and multiplies by the daily fee.
 */
export function estimateMonthlyFeeForCurrentMonth(
  dailyFee: number,
  scheduledDays: string[],
): number {
  if (dailyFee <= 0 || scheduledDays.length === 0) {
    return 0;
  }
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth(); // 0-indexed
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const scheduledIndexes = new Set(scheduledDays.map((d) => DAY_TO_JS_INDEX[d]));

  let matchingDays = 0;
  for (let day = 1; day <= daysInMonth; day += 1) {
    const weekday = new Date(year, month, day).getDay();
    if (scheduledIndexes.has(weekday)) {
      matchingDays += 1;
    }
  }
  return matchingDays * dailyFee;
}

interface StudentFormProps {
  studentId?: number;
  initialValues?: Partial<StudentFormValues>;
  submitLabel: string;
  isSubmitting: boolean;
  errorMessage: string | null;
  onSubmit: (payload: StudentCreateInput) => void | Promise<void>;
}

function toPayload(values: StudentFormValues): StudentCreateInput {
  return {
    full_name: values.full_name,
    date_of_birth: values.date_of_birth,
    class_grade: values.class_grade,
    section: values.section || null,
    roll_number: values.roll_number || null,
    photo_url: values.photo_url || null,
    parent_name: values.parent_name || null,
    parent_email: values.parent_email || null,
    parent_phone: values.parent_phone || null,
    enrollment_date: values.enrollment_date,
    daily_fee: values.daily_fee === '' ? null : Number(values.daily_fee),
    scheduled_days: values.scheduled_days,
    monthly_fee: values.monthly_fee === '' ? null : Number(values.monthly_fee),
  };
}

/**
 * Shared form used by both StudentCreatePage and StudentEditPage.
 */
export function StudentForm({
  studentId,
  initialValues,
  submitLabel,
  isSubmitting,
  errorMessage,
  onSubmit,
}: StudentFormProps) {
  const [values, setValues] = useState<StudentFormValues>({
    ...EMPTY_VALUES,
    ...initialValues,
  });
  const [hasManuallyEditedMonthlyFee, setHasManuallyEditedMonthlyFee] = useState(false);

  const handleChange =
    (field: keyof StudentFormValues) =>
    (event: ChangeEvent<HTMLInputElement>): void => {
      setValues((prev) => ({ ...prev, [field]: event.target.value }));
    };

  const toggleDay = (day: string): void => {
    setValues((prev) => {
      const isSelected = prev.scheduled_days.includes(day);
      const scheduled_days = isSelected
        ? prev.scheduled_days.filter((d) => d !== day)
        : [...prev.scheduled_days, day];
      return { ...prev, scheduled_days };
    });
  };

  const handleDailyFeeChange = (valueAsString: string): void => {
    setValues((prev) => ({ ...prev, daily_fee: valueAsString }));
  };

  const handleMonthlyFeeChange = (valueAsString: string): void => {
    setHasManuallyEditedMonthlyFee(true);
    setValues((prev) => ({ ...prev, monthly_fee: valueAsString }));
  };

  // Auto-recalculate the Monthly Fee preview whenever Daily Fee or the
  // scheduled days change, unless the user has manually edited it already.
  useEffect(() => {
    if (hasManuallyEditedMonthlyFee) {
      return;
    }
    const dailyFeeNumber = Number(values.daily_fee);
    if (!values.daily_fee || Number.isNaN(dailyFeeNumber) || values.scheduled_days.length === 0) {
      setValues((prev) => (prev.monthly_fee === '' ? prev : { ...prev, monthly_fee: '' }));
      return;
    }

    let isCancelled = false;

    if (studentId) {
      // Editing an existing student: use the real backend preview for the
      // current calendar month.
      const now = new Date();
      studentService
        .getMonthlyFeePreview(studentId, now.getFullYear(), now.getMonth() + 1)
        .then((preview) => {
          if (!isCancelled) {
            setValues((prev) => ({
              ...prev,
              monthly_fee: preview.calculated_monthly_fee,
            }));
          }
        })
        .catch(() => {
          // Ignore preview failures - the user can still enter a value manually.
        });
    } else {
      // Creating a new student: no id yet, so estimate locally.
      const estimate = estimateMonthlyFeeForCurrentMonth(dailyFeeNumber, values.scheduled_days);
      setValues((prev) => ({ ...prev, monthly_fee: estimate === 0 ? '' : String(estimate) }));
    }

    return () => {
      isCancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values.daily_fee, values.scheduled_days, hasManuallyEditedMonthlyFee, studentId]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    void onSubmit(toPayload(values));
  };

  return (
    <form onSubmit={handleSubmit}>
      <Stack spacing={5}>
        {errorMessage && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {errorMessage}
          </Alert>
        )}

        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
          <FormControl isRequired>
            <FormLabel>Full name</FormLabel>
            <Input value={values.full_name} onChange={handleChange('full_name')} />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Date of birth</FormLabel>
            <Input
              type="date"
              value={values.date_of_birth}
              onChange={handleChange('date_of_birth')}
            />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Class / grade</FormLabel>
            <Input value={values.class_grade} onChange={handleChange('class_grade')} />
          </FormControl>

          <FormControl>
            <FormLabel>Section</FormLabel>
            <Input value={values.section} onChange={handleChange('section')} />
          </FormControl>

          <FormControl>
            <FormLabel>Roll number</FormLabel>
            <Input value={values.roll_number} onChange={handleChange('roll_number')} />
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Enrollment date</FormLabel>
            <Input
              type="date"
              value={values.enrollment_date}
              onChange={handleChange('enrollment_date')}
            />
          </FormControl>

          <FormControl>
            <FormLabel>Photo URL</FormLabel>
            <Input value={values.photo_url} onChange={handleChange('photo_url')} />
          </FormControl>

          <FormControl>
            <FormLabel>Parent name</FormLabel>
            <Input value={values.parent_name} onChange={handleChange('parent_name')} />
          </FormControl>

          <FormControl>
            <FormLabel>Parent email</FormLabel>
            <Input
              type="email"
              value={values.parent_email}
              onChange={handleChange('parent_email')}
            />
          </FormControl>

          <FormControl>
            <FormLabel>Parent phone</FormLabel>
            <Input value={values.parent_phone} onChange={handleChange('parent_phone')} />
          </FormControl>

          <FormControl>
            <FormLabel>Daily fee (₹)</FormLabel>
            <NumberInput
              min={0}
              value={values.daily_fee}
              onChange={handleDailyFeeChange}
              borderRadius="xl"
            >
              <NumberInputField placeholder="e.g. 100" />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Monthly fee (₹)</FormLabel>
            <NumberInput
              min={0}
              value={values.monthly_fee}
              onChange={handleMonthlyFeeChange}
              borderRadius="xl"
            >
              <NumberInputField placeholder="Auto-calculated" />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>
        </SimpleGrid>

        <FormControl>
          <FormLabel>Classes per week</FormLabel>
          <ButtonGroup isAttached variant="outline" flexWrap="wrap">
            {DAY_OPTIONS.map(({ code, label }) => {
              const isSelected = values.scheduled_days.includes(code);
              return (
                <Button
                  key={code}
                  onClick={() => toggleDay(code)}
                  colorScheme={isSelected ? 'brand' : 'gray'}
                  variant={isSelected ? 'solid' : 'outline'}
                  borderRadius="lg"
                  size="sm"
                >
                  {label}
                </Button>
              );
            })}
          </ButtonGroup>
          <Text fontSize="xs" color="gray.600" mt={2}>
            Select the days this student attends class each week.
          </Text>
        </FormControl>

        <HStack justify="flex-end">
          <GradientButton type="submit" isLoading={isSubmitting}>
            {submitLabel}
          </GradientButton>
        </HStack>
      </Stack>
    </form>
  );
}
