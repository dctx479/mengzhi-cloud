import request from '@/utils/request'

export interface BrandStoryRequest {
  product_name: string
  origin: string
  features?: string
  purpose?: string
  style?: string
  word_count?: string
  category?: string
  keywords?: string[]
  use_culture?: boolean
  product_id?: number
  save_record?: boolean
  auto_generate_image?: boolean
}

export interface BrandStoryResponse {
  story: string
  cultural_elements: string[]
  tokens: { input?: number; output?: number; total?: number }
  cost: number
  metadata: Record<string, unknown>
  record_id?: number
  image_url?: string
}

export interface BrandStoryRecord {
  id: number
  product_name: string
  origin: string
  style: string
  story: string
  cultural_elements: string[]
  tokens_used: number
  cost: number
  created_at: string
  status: string
}

/**
 * 生成品牌故事
 * 注意: 后端使用 response_model 直接返回对象，无 {code,data,message} 包装
 */
export const generateBrandStory = async (
  payload: BrandStoryRequest,
): Promise<BrandStoryResponse> => {
  return await request.post<BrandStoryResponse>('/v1/brand-story/generate', payload)
}

/**
 * 获取品牌故事历史记录列表
 */
export const getBrandStoryRecords = async (
  skip = 0,
  limit = 20,
): Promise<BrandStoryRecord[]> => {
  return await request.get<BrandStoryRecord[]>('/v1/brand-story/records', {
    params: { skip, limit },
  })
}

/**
 * 获取单条品牌故事记录详情
 */
export const getBrandStoryRecord = async (
  recordId: number,
): Promise<BrandStoryRecord> => {
  return await request.get<BrandStoryRecord>(`/v1/brand-story/records/${recordId}`)
}
