import api from './api';
import type {
  FeeDetailResponse,
  FeeGenerationSummary,
  FeeStructure,
  FeeStructureCreate,
  FeeStructureUpdate,
  FeeStructureWithBalance,
  Payment,
  RazorpayOrderResponse,
} from '../types';

export const feeService = {
  async getFeeDetail(studentId: number): Promise<FeeDetailResponse> {
    const response = await api.get<FeeDetailResponse>(`/fees/students/${studentId}`);
    return response.data;
  },

  async createFeeStructure(payload: FeeStructureCreate): Promise<FeeStructure> {
    const response = await api.post<FeeStructure>('/fees', payload);
    return response.data;
  },

  async updateFeeStructure(feeId: number, payload: FeeStructureUpdate): Promise<FeeStructure> {
    const response = await api.put<FeeStructure>(`/fees/${feeId}`, payload);
    return response.data;
  },

  async createRazorpayOrder(feeStructureId: number): Promise<RazorpayOrderResponse> {
    const response = await api.post<RazorpayOrderResponse>('/payments/razorpay/order', {
      fee_structure_id: feeStructureId,
    });
    return response.data;
  },

  async getPaymentHistory(studentId: number): Promise<Payment[]> {
    const response = await api.get<Payment[]>(`/payments/student/${studentId}`);
    return response.data;
  },

  async sendReminder(feeId: number): Promise<void> {
    await api.post(`/fees/${feeId}/remind`);
  },

  async markFeePaid(feeId: number): Promise<FeeStructureWithBalance> {
    const response = await api.post<FeeStructureWithBalance>(`/fees/${feeId}/mark-paid`);
    return response.data;
  },

  async getOverdueFees(): Promise<FeeStructureWithBalance[]> {
    const response = await api.get<FeeStructureWithBalance[]>('/fees/overdue');
    return response.data;
  },

  async generateFeesFromAttendance(): Promise<FeeGenerationSummary> {
    const response = await api.post<FeeGenerationSummary>('/fees/generate-from-attendance');
    return response.data;
  },
};
