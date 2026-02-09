export interface AdminStats {
  totalUsers: number
  totalEnterprises: number
  totalAIUsage: number
  activeUsers: number
}

export interface User {
  id: number
  username: string
  email: string
  role: string
  status: string
  createdAt: string
}

export interface Enterprise {
  id: number
  name: string
  contactPerson: string
  email: string
  status: string
  createdAt: string
}

export interface AIUsageData {
  date: string
  count: number
}
