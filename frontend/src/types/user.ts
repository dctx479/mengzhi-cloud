/**
 * 用户相关类型定义
 */

export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  phone?: string
  nickname?: string
  status: 'active' | 'inactive' | 'banned'
  role: 'user' | 'admin' | 'manager'
  createdAt: string
  updatedAt: string
}

export interface UserProfile extends User {
  bio?: string
  location?: string
  website?: string
  totalChats?: number
  totalProducts?: number
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  user: User
  expiresIn: number
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  user_type: string
  verification_code: string
}

export interface RegisterResponse {
  user: User
  message: string
}

export interface UpdateProfileRequest {
  username?: string
  nickname?: string
  avatar?: string
  phone?: string
  bio?: string
  location?: string
  website?: string
}

// 订单相关类型
export interface OrderItem {
  id: number
  product_id: number
  product: {
    id: number
    name: string
    image: string
    price: number
  }
  quantity: number
  price: number
  subtotal: number
}

export interface Order {
  id: number
  order_no: string
  user_id: string
  package_id?: number
  package_name?: string
  package_type?: string
  amount?: number
  original_amount?: number
  discount_amount?: number
  items: OrderItem[]
  status: 'pending' | 'completed' | 'cancelled' | 'shipped'
  total_amount: number
  created_at: string
  updated_at: string
}

export interface OrdersResponse {
  items: Order[]
  total: number
  page: number
  page_size: number
}

// 配额相关类型
export interface QuotaData {
  chat_used: number
  chat_total: number
  content_used: number
  content_total: number
  storage_used: number
  storage_total: number
}

export interface QuotaHistory {
  id: string
  type: 'chat' | 'content' | 'storage'
  amount: number
  created_at: string
  description: string
}

export interface QuotaHistoryResponse {
  items: QuotaHistory[]
  total: number
  page: number
  page_size: number
}

// 设置相关类型
export interface UserSettings {
  email_notifications: boolean
  sms_notifications: boolean
  profile_public: boolean
  language: string
  theme: 'light' | 'dark' | 'auto'
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

export interface SecurityLog {
  id: string
  event_type: string
  ip_address: string
  user_agent: string
  created_at: string
  success: boolean
}
