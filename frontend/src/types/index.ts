/**
 * Shared TypeScript interfaces used across the Abhyas frontend.
 * These mirror the backend SQLAlchemy models defined in PRPs/abhyas-prp.md.
 */

export type UserRole = 'teacher' | 'parent' | 'admin';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  oauth_provider: string | null;
  created_at: string;
}

export type AttendanceStatus = 'present' | 'absent' | 'late';

export type FeeFrequency = 'monthly' | 'term' | 'one_time';

export type PaymentMethod = 'razorpay' | 'cash' | 'bank_transfer';

export type PaymentStatus = 'pending' | 'completed' | 'failed';

export type ReminderChannel = 'email';

export type ReminderStatus = 'sent' | 'failed';

export type ScheduledDay = 'sun' | 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat';

export interface Student {
  id: number;
  teacher_id: number;
  full_name: string;
  date_of_birth: string;
  class_grade: string;
  section: string | null;
  roll_number: string | null;
  photo_url: string | null;
  parent_name: string | null;
  parent_email: string | null;
  parent_phone: string | null;
  parent_user_id: number | null;
  enrollment_date: string;
  is_active: boolean;
  daily_fee: number | null;
  scheduled_days: string[];
  monthly_fee: number | null;
  created_at: string;
  updated_at: string;
}

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

export interface CalendarDaySummary {
  date: string;
  present: number;
  absent: number;
  late: number;
  total: number;
}

export interface MonthlyFeePreview {
  year: number;
  month: number;
  calculated_monthly_fee: string;
}

export interface AttendanceRecord {
  id: number;
  student_id: number;
  teacher_id: number;
  date: string;
  status: AttendanceStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttendanceSummary {
  student_id: number;
  total_days: number;
  present_days: number;
  absent_days: number;
  late_days: number;
  attendance_percentage: number;
}

export interface FeeStructure {
  id: number;
  student_id: number;
  amount: number;
  frequency: FeeFrequency;
  due_date: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeeStructureCreate {
  student_id: number;
  amount: number;
  frequency: FeeFrequency;
  due_date: string;
  description?: string | null;
}

export interface FeeStructureUpdate {
  amount?: number;
  frequency?: FeeFrequency;
  due_date?: string;
  description?: string | null;
}

export interface FeeStructureWithBalance extends FeeStructure {
  student_name: string;
  outstanding_balance: number;
  is_overdue: boolean;
}

export interface FeeDetailResponse {
  student_id: number;
  fee_structures: FeeStructureWithBalance[];
  payments: Payment[];
  total_outstanding: number;
}

export interface RazorpayOrderResponse {
  payment_id: number;
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
}

export interface Payment {
  id: number;
  fee_structure_id: number;
  student_id: number;
  amount_paid: number;
  payment_date: string;
  method: PaymentMethod;
  razorpay_payment_id: string | null;
  razorpay_order_id: string | null;
  status: PaymentStatus;
  created_at: string;
}

export interface GeneratedFeeEntry {
  student_id: number;
  student_name: string;
  year: number;
  month: number;
  amount: string;
}

export interface FeeGenerationSummary {
  created: GeneratedFeeEntry[];
  skipped_already_generated: number;
  skipped_no_daily_fee: number;
  skipped_zero_days: number;
}

export interface FeeReminder {
  id: number;
  student_id: number;
  fee_structure_id: number;
  sent_at: string;
  channel: ReminderChannel;
  status: ReminderStatus;
}

export interface ApiError {
  detail: string;
}

export interface RecentActivityEntry {
  type: string;
  description: string;
  timestamp: string;
}

export interface DashboardStats {
  total_students: number;
  attendance_percentage_recent: number;
  attendance_reference_date: string;
  overdue_fees_count: number;
  total_fees_collected_this_month: number;
  recent_activity: RecentActivityEntry[];
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AdminUserUpdate {
  is_active?: boolean;
  role?: UserRole;
}

export interface AdminStats {
  total_users: number;
  total_teachers: number;
  total_parents: number;
  total_students: number;
  total_payments_this_month: number;
}
