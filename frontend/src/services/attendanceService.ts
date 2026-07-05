import api from './api';
import type {
  AttendanceRecord,
  AttendanceStatus,
  AttendanceSummary,
  CalendarDaySummary,
} from '../types';

export interface AttendanceEntry {
  student_id: number;
  date: string;
  status: AttendanceStatus;
  notes?: string | null;
}

export interface AttendanceQueryParams {
  date?: string;
  class_grade?: string;
  student_id?: number;
}

export interface AttendanceUpdatePayload {
  status?: AttendanceStatus;
  notes?: string | null;
}

export const attendanceService = {
  async queryAttendance(params: AttendanceQueryParams = {}): Promise<AttendanceRecord[]> {
    const response = await api.get<AttendanceRecord[]>('/attendance', { params });
    return response.data;
  },

  async markAttendance(entry: AttendanceEntry): Promise<AttendanceRecord> {
    const response = await api.post<AttendanceRecord[]>('/attendance', { entries: [entry] });
    return response.data[0];
  },

  async bulkMarkAttendance(entries: AttendanceEntry[]): Promise<AttendanceRecord[]> {
    const response = await api.post<AttendanceRecord[]>('/attendance', { entries });
    return response.data;
  },

  async updateAttendance(
    recordId: number,
    payload: AttendanceUpdatePayload,
  ): Promise<AttendanceRecord> {
    const response = await api.put<AttendanceRecord>(`/attendance/${recordId}`, payload);
    return response.data;
  },

  async getStudentSummary(studentId: number): Promise<AttendanceSummary> {
    const response = await api.get<AttendanceSummary>(`/attendance/student/${studentId}/summary`);
    return response.data;
  },

  async getCalendarSummary(
    year: number,
    month: number,
  ): Promise<{ days: CalendarDaySummary[] }> {
    const response = await api.get<{ days: CalendarDaySummary[] }>(
      '/attendance/calendar-summary',
      { params: { year, month } },
    );
    return response.data;
  },
};
