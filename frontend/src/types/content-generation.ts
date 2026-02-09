/**
 * 内容生成相关类型定义
 */

// 模板类别类型
export type TemplateCategory = 'product' | 'slogan' | 'marketing' | 'social' | 'video'

// 难度等级
export type DifficultyLevel = 'easy' | 'medium' | 'hard'

// 文案风格
export type ContentStyle = 'professional' | 'casual' | 'emotional' | 'creative'

// 目标受众
export type TargetAudience = 'urban' | 'family' | 'health' | 'gourmet'

// 任务状态
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

// 内容模板接口
export interface ContentTemplate {
  id: string
  category: TemplateCategory
  name: string
  description: string
  sample: string
  difficulty: DifficultyLevel
  usage_count: number
  parameters?: Record<string, any>
  prompt?: string
  created_at: string
  updated_at: string
}

// 生成配置接口
export interface GenerationConfig {
  product_ids: string[]
  template_id: string
  count: number
  style: ContentStyle
  word_count: number
  target_audience: TargetAudience[]
  keywords: string[]
  avoid_words: string
  temperature: number
}

// 生成结果接口
export interface GenerationResult {
  id: string
  template_id: string
  product_id: string
  content: string
  word_count: number
  rating: number
  edited: boolean
  created_at: string
  updated_at: string
}

// 生成请求接口
export interface GenerationRequest {
  config: GenerationConfig
  batch_id?: string
}

// 生成响应接口
export interface GenerationResponse {
  id: string
  content: string
  metadata?: Record<string, any>
}

// 批量任务接口
export interface BatchTask {
  id: string
  name: string
  template: string
  template_id: string
  count: number
  progress: number
  status: TaskStatus
  results: GenerationResult[]
  error_message?: string
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
}

// 保存的配置接口
export interface SavedConfig {
  id: string
  name: string
  config: GenerationConfig
  created_at: string
  updated_at: string
}

// 历史记录接口
export interface HistoryRecord {
  id: string
  task_id: string
  template_id: string
  config: GenerationConfig
  results: GenerationResult[]
  status: TaskStatus
  created_at: string
}
