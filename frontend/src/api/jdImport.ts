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
  app_key_prefix: string | null
  note?: string | null
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

export const importFromJd = async (params: JdImportRequest): Promise<JdImportResponse> => {
  const res = await http.post<ApiResponse<JdImportResponse>>('/v1/jd/import', params)
  return unwrap<JdImportResponse>(res)
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
