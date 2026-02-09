import axios from 'axios'
import type { AdminStats, User, Enterprise, AIUsageData } from '@/types/admin'

const api = axios.create({
  baseURL: '/api/admin'
})

export const adminApi = {
  getStats: () => api.get<AdminStats>('/stats'),

  getUsers: (params?: { search?: string }) => api.get<User[]>('/users', { params }),
  updateUser: (id: number, data: Partial<User>) => api.patch(`/users/${id}`, data),
  deleteUser: (id: number) => api.delete(`/users/${id}`),

  getEnterprises: (params?: { search?: string }) => api.get<Enterprise[]>('/enterprises', { params }),
  updateEnterprise: (id: number, data: Partial<Enterprise>) => api.patch(`/enterprises/${id}`, data),
  deleteEnterprise: (id: number) => api.delete(`/enterprises/${id}`),

  getAIUsage: () => api.get<AIUsageData[]>('/ai-usage')
}
