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
  // 后端返回 APIResponse 结构: { code, message, data: { user, tokens } }
  const res = await http.post<{ code: number; message: string; data: { user: Record<string, unknown>; tokens: { access_token: string; refresh_token: string; expires_in: number } } | null }>('/v1/auth/login', data)

  // 检查业务状态码（后端错误也返回HTTP 200）
  if (res.code !== 200 || !res.data) {
    throw new Error(res.message || '登录失败')
  }

  const inner = res.data
  const token = inner.tokens?.access_token ?? ''
  if (!token) {
    throw new Error('登录响应中缺少有效token')
  }
  localStorage.setItem('token', token)

  // 归一化为前端 LoginResponse 格式
  const backendUser = inner.user ?? {}
  const user: User = {
    id: (backendUser.user_id as string) ?? '',
    username: (backendUser.username as string) ?? '',
    email: (backendUser.email as string) ?? '',
    phone: backendUser.phone as string | undefined,
    nickname: backendUser.nickname as string | undefined,
    avatar: backendUser.avatar_url as string | undefined,
    status: (backendUser.status as User['status']) ?? 'active',
    role: (backendUser.role as User['role']) ?? 'user',
    createdAt: (backendUser.created_at as string) ?? '',
    updatedAt: '',
  }
  return {
    token,
    user,
    expiresIn: inner.tokens?.expires_in ?? 1800,
  }
}

export const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
  const res = await http.post<{ code: number; message: string; data: RegisterResponse }>('/v1/auth/register', data)
  if (res.code !== 200 || !res.data) {
    throw new Error((res as any).message || '注册失败')
  }
  return (res as unknown as { data: RegisterResponse }).data ?? (res as unknown as RegisterResponse)
}

export async function logout(): Promise<void> {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export const getCurrentUser = (): Promise<User> =>
  http.get<{ code: number; message: string; data: Record<string, unknown> | null }>('/v1/auth/me').then((res) => {
    if (res.code !== 200 || !res.data) {
      throw new Error(res.message || '获取用户信息失败')
    }
    const u = res.data
    return {
      id: (u.user_id as string) ?? '',
      username: (u.username as string) ?? '',
      email: (u.email as string) ?? '',
      phone: u.phone as string | undefined,
      nickname: u.nickname as string | undefined,
      avatar: u.avatar_url as string | undefined,
      status: (u.status as User['status']) ?? 'active',
      role: (u.role as User['role']) ?? 'user',
      createdAt: (u.created_at as string) ?? '',
      updatedAt: '',
    } as User
  })

export const updateProfile = async (data: UpdateProfileRequest): Promise<User> => {
  const res = await http.put<{ code: number; message: string; data: any }>('/v1/auth/me', data)
  // PUT /auth/me may return {updated: true} or user data; re-fetch to ensure fresh user
  const inner = (res as unknown as { data: any }).data ?? res
  if (inner && inner.id) return inner as User
  // Fallback: re-fetch user profile
  return getCurrentUser()
}

export const changePassword = (oldPassword: string, newPassword: string): Promise<void> =>
  http.post('/v1/auth/change-password', { old_password: oldPassword, new_password: newPassword })

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
  const res = await http.get<{ code: number; data: { available: boolean } }>('/v1/auth/check-availability', {
    params: { field, value }
  })
  const inner = (res as unknown as { data: { available: boolean } }).data ?? res
  return inner.available ?? false
}

