import request from '@/utils/request'

function unwrap<T>(res: unknown): T {
  const r = res as { data?: T }
  return r.data !== undefined ? r.data : (res as T)
}

export interface CulturalElement {
  id: number
  name: string
  type: string
  origin_region: string
  story_preview: string
  keywords: string[]
  status: string
  created_at: string
}

export interface Pagination {
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ElementListResponse {
  elements: CulturalElement[]
  pagination: Pagination
}

export interface CulturalElementDetail {
  id: number
  name: string
  type: string
  story: string
  origin_region: string
  keywords: string[]
  metadata: Record<string, unknown>
  source: string
  status: string
  created_at: string
  reviewed_at: string | null
}

export interface MatchedElement {
  element: {
    name: string
    type: string
    story: string
    origin_region: string
    keywords: string[]
  }
  score: number
  match_reason: string
  score_breakdown: {
    exact_match: number
    knowledge_graph: number
  }
  path_info: unknown
}

export interface MatchResponse {
  matched_elements: MatchedElement[]
  total_count: number
  query: Record<string, unknown>
}

export interface GraphStatistics {
  node_count?: number
  edge_count?: number
  [key: string]: unknown
}

export interface StatisticsOverview {
  elements: {
    total: number
    approved: number
    pending: number
  }
  by_type: Record<string, number>
  tasks: {
    total: number
    completed: number
    success_rate: number
  }
}

export interface ReviewTask {
  id: number
  element_id: number
  element_name?: string
  priority: string
  [key: string]: unknown
}

export interface GetElementsParams {
  type?: string
  origin_region?: string
  keyword?: string
  status?: string
  page?: number
  page_size?: number
}

export const getElements = async (params: GetElementsParams = {}): Promise<ElementListResponse> => {
  const query = { page: 1, page_size: 20, ...params }
  const res = await request.get<{ code: number; data: ElementListResponse; message: string }>('/v1/cultural/elements', { params: query })
  return unwrap<ElementListResponse>(res)
}

export const getElementDetail = async (id: number): Promise<CulturalElementDetail> => {
  const res = await request.get<{ code: number; data: CulturalElementDetail; message: string }>(`/v1/cultural/elements/${id}`)
  return unwrap<CulturalElementDetail>(res)
}

export interface MatchElementsParams {
  product_name: string
  origin?: string
  category?: string
  keywords?: string[]
  use_knowledge_graph?: boolean
  top_k?: number
}

export const matchElements = async (params: MatchElementsParams): Promise<MatchResponse> => {
  const res = await request.post<{ code: number; data: MatchResponse; message: string }>('/v1/cultural/match', null, { params })
  return unwrap<MatchResponse>(res)
}

export const getGraphStatistics = async (): Promise<GraphStatistics> => {
  const res = await request.get<{ code: number; data: GraphStatistics; message: string }>('/v1/cultural/graph/statistics')
  return unwrap<GraphStatistics>(res)
}

export const getStatisticsOverview = async (): Promise<StatisticsOverview> => {
  const res = await request.get<{ code: number; data: StatisticsOverview; message: string }>('/v1/cultural/statistics/overview')
  return unwrap<StatisticsOverview>(res)
}

export interface GetPendingReviewsParams {
  priority?: string
  limit?: number
}

export const getPendingReviews = async (params: GetPendingReviewsParams = {}): Promise<ReviewTask[]> => {
  const res = await request.get<{ code: number; data: ReviewTask[]; message: string }>('/v1/cultural/review/pending', { params })
  return unwrap<ReviewTask[]>(res)
}

export interface ReviewElementParams {
  decision: string
  comments?: string
  corrections?: string
}

export const reviewElement = async (elementId: number, params: ReviewElementParams): Promise<Record<string, unknown>> => {
  const res = await request.post<{ code: number; data: Record<string, unknown>; message: string }>(`/v1/cultural/review/element/${elementId}`, null, { params })
  return unwrap<Record<string, unknown>>(res)
}
