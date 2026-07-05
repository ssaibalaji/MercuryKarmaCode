import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { AttendanceSummaryCard } from '../../../components/attendance/AttendanceSummaryCard';
import { attendanceService } from '../../../services/attendanceService';
import { renderWithProviders } from '../../../test/test-utils';
import type { AttendanceSummary } from '../../../types';

vi.mock('../../../services/attendanceService', () => ({
  attendanceService: {
    getStudentSummary: vi.fn(),
    queryAttendance: vi.fn(),
    markAttendance: vi.fn(),
    bulkMarkAttendance: vi.fn(),
    updateAttendance: vi.fn(),
  },
}));

const mockedAttendanceService = vi.mocked(attendanceService);

const summary: AttendanceSummary = {
  student_id: 42,
  total_days: 100,
  present_days: 80,
  absent_days: 15,
  late_days: 5,
  attendance_percentage: 80,
};

describe('AttendanceSummaryCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the attendance percentage and present/absent/late breakdown', async () => {
    mockedAttendanceService.getStudentSummary.mockResolvedValue(summary);

    renderWithProviders(<AttendanceSummaryCard studentId={42} />);

    expect(await screen.findByText(/80% present over 100 days/)).toBeInTheDocument();
    expect(screen.getByText('80')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(mockedAttendanceService.getStudentSummary).toHaveBeenCalledWith(42);
  });

  it('renders an error message when the summary request fails', async () => {
    mockedAttendanceService.getStudentSummary.mockRejectedValue(new Error('boom'));

    renderWithProviders(<AttendanceSummaryCard studentId={42} />);

    expect(
      await screen.findByText('Unable to load attendance summary right now.'),
    ).toBeInTheDocument();
  });
});
