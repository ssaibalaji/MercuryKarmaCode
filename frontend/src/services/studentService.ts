import api from './api';
import type { MonthlyFeePreview, Student } from '../types';

export interface StudentListItem {
  id: number;
  full_name: string;
  class_grade: string;
  section: string | null;
  roll_number: string | null;
  photo_url: string | null;
  is_active: boolean;
  parent_user_id: number | null;
}

export interface StudentCreateInput {
  full_name: string;
  date_of_birth: string;
  class_grade: string;
  section?: string | null;
  roll_number?: string | null;
  photo_url?: string | null;
  parent_name?: string | null;
  parent_email?: string | null;
  parent_phone?: string | null;
  enrollment_date: string;
  daily_fee?: number | null;
  scheduled_days?: string[];
  monthly_fee?: number | null;
}

export type StudentUpdateInput = Partial<StudentCreateInput> & { is_active?: boolean };

export interface ParentInviteInput {
  parent_email: string;
  parent_name?: string | null;
}

export interface ParentInviteResult {
  student_id: number;
  parent_email: string;
  invited: boolean;
  parent_user_id: number | null;
  message: string;
}

export interface StudentListFilters {
  class_grade?: string;
  section?: string;
}

export const studentService = {
  async listStudents(filters: StudentListFilters = {}): Promise<StudentListItem[]> {
    const response = await api.get<StudentListItem[]>('/students', { params: filters });
    return response.data;
  },

  async getStudent(id: number): Promise<Student> {
    const response = await api.get<Student>(`/students/${id}`);
    return response.data;
  },

  async createStudent(payload: StudentCreateInput): Promise<Student> {
    const response = await api.post<Student>('/students', payload);
    return response.data;
  },

  async updateStudent(id: number, payload: StudentUpdateInput): Promise<Student> {
    const response = await api.put<Student>(`/students/${id}`, payload);
    return response.data;
  },

  async deleteStudent(id: number): Promise<Student> {
    const response = await api.delete<Student>(`/students/${id}`);
    return response.data;
  },

  async inviteParent(id: number, payload: ParentInviteInput): Promise<ParentInviteResult> {
    const response = await api.post<ParentInviteResult>(`/students/${id}/invite-parent`, payload);
    return response.data;
  },

  async getMonthlyFeePreview(
    studentId: number,
    year: number,
    month: number,
  ): Promise<MonthlyFeePreview> {
    const response = await api.get<MonthlyFeePreview>(`/students/${studentId}/monthly-fee`, {
      params: { year, month },
    });
    return response.data;
  },
};
