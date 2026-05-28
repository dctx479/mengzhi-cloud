import http from '@/utils/http'

export interface JdGoodsItem {
  jd_sku_id: string
  name: string
  category: string
  sub_category: string | null
  price: number
  image: string
  images: string[]
  shop_name: string
  source: 'jd'
}

export interface JdSearchResult {
  items: JdGoodsItem[]
  total: number
  page: number
  page_size: number
  warning?: string | null
}

export interface JdImportRequest {
  keyword: string
  max_pages?: number
  page_size?: number
}

export interface JdImportResponse {
  status: string
  keyword: string
}

export interface JdStatusResponse {
  configured: boolean
  has_access_token: boolean
  token_expired: boolean
  token_source: 'db' | 'env' | null
  app_key_prefix: string | null
  has_redirect_uri: boolean
  note?: string | null
}

export interface JdConfigResponse {
  has_token: boolean
  token_masked: string | null
  token_source: 'db' | 'env' | null
  expires_at: string | null
  uid: string | null
}

export interface JdOAuthUrlResponse {
  auth_url: string
  state: string
}

export interface JdRefreshResponse {
  refreshed: boolean
  expires_at: string
}

type ApiResponse<T> = { code: number; data: T; message: string }

function unwrap<T>(res: unknown): T {
  const r = res as ApiResponse<T>
  return r?.data ?? (res as T)
}

export const getJdStatus = async (): Promise<JdStatusResponse> => {
  const res = await http.get<ApiResponse<JdStatusResponse>>('/v1/jd/status')
  return unwrap<JdStatusResponse>(res)
}

export const getJdConfig = async (): Promise<JdConfigResponse> => {
  const res = await http.get<ApiResponse<JdConfigResponse>>('/v1/jd/config')
  return unwrap<JdConfigResponse>(res)
}

export const updateJdAccessToken = async (accessToken: string): Promise<void> => {
  await http.put('/v1/jd/config', { access_token: accessToken })
}

export const importFromJd = async (params: JdImportRequest): Promise<JdImportResponse> => {
  const res = await http.post<ApiResponse<JdImportResponse>>('/v1/jd/import', params)
  return unwrap<JdImportResponse>(res)
}

export const getJdOAuthUrl = async (): Promise<JdOAuthUrlResponse> => {
  const res = await http.get<ApiResponse<JdOAuthUrlResponse>>('/v1/jd/oauth/authorize')
  return unwrap<JdOAuthUrlResponse>(res)
}

export const refreshJdToken = async (): Promise<JdRefreshResponse> => {
  const res = await http.post<ApiResponse<JdRefreshResponse>>('/v1/jd/oauth/refresh')
  return unwrap<JdRefreshResponse>(res)
}

export const searchJdGoods = async (
  keyword: string,
  page = 1,
  pageSize = 20,
): Promise<JdSearchResult> => {
  const res = await http.get<ApiResponse<JdSearchResult>>('/v1/jd/search', {
    params: { keyword, page, page_size: pageSize },
  })
  return unwrap<JdSearchResult>(res)
}
