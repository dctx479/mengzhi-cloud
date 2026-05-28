import http from '@/utils/http'

export interface TaobaoItem {
  tb_num_iid: string
  name: string
  category: string
  sub_category: string | null
  price: number
  image: string
  images: string[]
  shop_title: string
  provcity: string
  volume: number | null
  item_url: string
  source: 'taobao'
}

export interface TaobaoSearchResult {
  items: TaobaoItem[]
  total: number
  page: number
  page_size: number
  warning?: string | null
}

export interface TaobaoImportRequest {
  keyword: string
  max_pages?: number
  page_size?: number
  adzone_id?: string
}

export interface TaobaoImportResponse {
  status: string
  keyword: string
}

export interface TaobaoStatusResponse {
  configured: boolean
  has_session: boolean
  session_expired: boolean
  session_source: 'db' | 'env' | null
  has_redirect_uri: boolean
  app_key_prefix: string | null
  note?: string | null
}

export interface TaobaoConfigResponse {
  has_session: boolean
  session_masked: string | null
  session_source: 'db' | 'env' | null
  expires_at: string | null
  taobao_user_id: string | null
}

export interface TaobaoOAuthUrlResponse {
  auth_url: string
  state: string
}

export interface TaobaoRefreshResponse {
  refreshed: boolean
  expires_at: string
}

type ApiResponse<T> = { code: number; data: T; message: string }

function unwrap<T>(res: unknown): T {
  const r = res as ApiResponse<T>
  return r?.data ?? (res as T)
}

export const getTaobaoStatus = async (): Promise<TaobaoStatusResponse> => {
  const res = await http.get<ApiResponse<TaobaoStatusResponse>>('/v1/taobao/status')
  return unwrap<TaobaoStatusResponse>(res)
}

export const getTaobaoConfig = async (): Promise<TaobaoConfigResponse> => {
  const res = await http.get<ApiResponse<TaobaoConfigResponse>>('/v1/taobao/config')
  return unwrap<TaobaoConfigResponse>(res)
}

export const updateTaobaoSession = async (session: string): Promise<void> => {
  await http.put('/v1/taobao/config', { session })
}

export const getTaobaoOAuthUrl = async (): Promise<TaobaoOAuthUrlResponse> => {
  const res = await http.get<ApiResponse<TaobaoOAuthUrlResponse>>('/v1/taobao/oauth/authorize')
  return unwrap<TaobaoOAuthUrlResponse>(res)
}

export const refreshTaobaoSession = async (): Promise<TaobaoRefreshResponse> => {
  const res = await http.post<ApiResponse<TaobaoRefreshResponse>>('/v1/taobao/oauth/refresh')
  return unwrap<TaobaoRefreshResponse>(res)
}

export const importFromTaobao = async (params: TaobaoImportRequest): Promise<TaobaoImportResponse> => {
  const res = await http.post<ApiResponse<TaobaoImportResponse>>('/v1/taobao/import', params)
  return unwrap<TaobaoImportResponse>(res)
}

export const searchTaobaoItems = async (
  keyword: string,
  page = 1,
  pageSize = 20,
  adzoneId?: string,
): Promise<TaobaoSearchResult> => {
  const res = await http.get<ApiResponse<TaobaoSearchResult>>('/v1/taobao/search', {
    params: { keyword, page, page_size: pageSize, adzone_id: adzoneId },
  })
  return unwrap<TaobaoSearchResult>(res)
}
