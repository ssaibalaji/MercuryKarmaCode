import api from './api';
import type { AdminStats, AdminUser, AdminUserUpdate } from '../types';

export const adminService = {
  async listUsers(): Promise<AdminUser[]> {
    const response = await api.get<AdminUser[]>('/admin/users');
    return response.data;
  },

  async updateUser(id: number, payload: AdminUserUpdate): Promise<AdminUser> {
    const response = await api.put<AdminUser>(`/admin/users/${id}`, payload);
    return response.data;
  },

  async getStats(): Promise<AdminStats> {
    const response = await api.get<AdminStats>('/admin/stats');
    return response.data;
  },
};
