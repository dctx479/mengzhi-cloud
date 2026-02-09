/**
 * 认证 API 服务
 */
import http from '@/utils/http'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
  UpdateProfileRequest,
} from '@/types/user'

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await http.post<LoginResponse>('/v1/auth/login', data)
  if (response.token) {
    localStorage.setItem('token', response.token)
  }
  return response
}

export const register = (data: RegisterRequest): Promise<RegisterResponse> =>
  http.post('/v1/auth/register', data)

export async function logout(): Promise<void> {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export const getCurrentUser = (): Promise<User> =>
  http.get('/v1/auth/me')

export const updateProfile = (data: UpdateProfileRequest): Promise<User> =>
  http.put('/v1/auth/profile', data)

export const changePassword = (oldPassword: string, newPassword: string): Promise<void> =>
  http.post('/v1/auth/change-password', { oldPassword, newPassword })

export async function verifyToken(): Promise<boolean> {
  try {
    const token = localStorage.getItem('token')
    if (!token) return false
    await getCurrentUser()
    return true
  } catch {
    return false
  }
}

export const checkAvailability = async (field: 'username' | 'email', value: string): Promise<boolean> => {
  const response = await http.get<{ available: boolean }>('/v1/auth/check-availability', {
    params: { field, value }
  })
  return response.available
}
