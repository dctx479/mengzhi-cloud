export type MediaProviderType = 'image' | 'video'

export type MediaTaskStatus = 'pending' | 'processing' | 'succeeded' | 'failed' | 'canceled'

export interface AIMediaProviderConfig {
  query_endpoint?: string
  submit_endpoint?: string
  validate_endpoint?: string
  timeout?: number
  model?: string
  [key: string]: unknown
}

export interface AIMediaProvider {
  id: number
  provider_uuid: string
  provider_code: string
  provider_name: string
  provider_type: MediaProviderType
  app_id?: string | null
  api_endpoint?: string | null
  default_model?: string | null
  is_active: boolean
  is_primary: boolean
  priority: number
  cost_per_unit: number
  rate_limit_per_minute: number
  config?: AIMediaProviderConfig | null
  health_status: string
  last_check_time?: string | null
  error_count: number
  last_error_message?: string | null
  last_error_time?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface AIMediaProviderForm {
  providerCode: string
  providerName: string
  providerType: MediaProviderType
  apiKey?: string
  appId?: string
  apiEndpoint?: string
  defaultModel?: string
  isActive: boolean
  isPrimary: boolean
  priority: number
  costPerUnit: number
  rateLimitPerMinute: number
  config?: AIMediaProviderConfig
}

export interface AIMediaProviderTestResult {
  success: boolean
  message: string
  provider: AIMediaProvider
}

export interface AIMediaGenerationResult {
  id: number
  result_uuid: string
  task_id: number
  media_id?: number | null
  file_url: string
  thumbnail_url?: string | null
  file_size?: number | null
  width?: number | null
  height?: number | null
  duration?: number | null
  metadata?: Record<string, unknown> | null
  created_at?: string | null
  updated_at?: string | null
}

export interface AIMediaTask {
  id: number
  task_uuid: string
  user_id: number
  enterprise_id?: number | null
  provider_id?: number | null
  provider?: AIMediaProvider | null
  media_type: MediaProviderType
  status: MediaTaskStatus
  prompt: string
  negative_prompt?: string | null
  model?: string | null
  width?: number | null
  height?: number | null
  duration?: number | null
  result_count: number
  provider_task_id?: string | null
  request_params?: Record<string, unknown> | null
  error_message?: string | null
  cost_amount: number
  started_at?: string | null
  completed_at?: string | null
  created_at?: string | null
  updated_at?: string | null
  results?: AIMediaGenerationResult[]
}

export interface AIMediaCostSummary {
  total_cost: number
  total_tasks: number
  by_provider: Array<{
    provider_name: string
    total_cost: number
    task_count: number
  }>
}
