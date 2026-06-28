/**
 * 产品 API 服务
 *
 * 注意：后端返回 { code, data, message } 包装格式，此处统一解包。
 */
import http from '@/utils/http'
import type {
  Product,
  ProductDetail,
  ProductListRequest,
  ProductListResponse,
  Category,
  Review,
} from '@/types/product'

/** 解包后端 { code, data, message } 包装，提取 data 字段 */
function unwrap<T>(res: unknown): T {
  const r = res as { data?: T | null }
  if (r.data !== undefined && r.data !== null) return r.data
  return res as T
}

/** 将后端 snake_case 产品字段映射为前端 Product 类型 */
function mapProduct(raw: Record<string, unknown>): Product {
  const specs = (raw.specifications ?? {}) as Record<string, unknown>
  return {
    id: String(raw.id ?? ''),
    name: (raw.name as string) ?? '',
    description: (raw.description as string) ?? '',
    price: Number(raw.price ?? specs.price ?? 0),
    image: (raw.main_image_url as string) ?? '',
    images: (raw.image_urls as string[]) ?? [],
    category: (raw.category as string) ?? '',
    categoryId: (raw.sub_category as string) ?? '',
    rating: 0,
    reviewCount: 0,
    inStock: raw.status === 'published',
    createdAt: (raw.created_at as string) ?? '',
    updatedAt: (raw.updated_at as string) ?? '',
    origin: (raw.origin_province as string) ?? '',
    region: (raw.origin_province as string) ?? '',
    specifications: specs as Record<string, string>,
  }
}

/** 地区代码→中文名映射 (前端用code, 后端用中文名) */
const REGION_CODE_TO_NAME: Record<string, string> = {
  xilin: '锡林郭勒盟',
  hulun: '呼伦贝尔市',
  chifeng: '赤峰市',
  tongliao: '通辽市',
  wulanchabu: '乌兰察布市',
  baotou: '包头市',
  huhhot: '呼和浩特市',
}

function mapSortParams(sortBy?: string): { sort_by?: string; sort_order?: string } {
  if (!sortBy) return {}
  const map: Record<string, [string, string]> = {
    newest: ['created_at', 'desc'],
    popular: ['created_at', 'desc'],
    priceHigh: ['price', 'desc'],
    priceLow: ['price', 'asc'],
    price_asc: ['price', 'asc'],
    price_desc: ['price', 'desc'],
  }
  const [field, order] = map[sortBy] ?? ['created_at', 'desc']
  return { sort_by: field, sort_order: order }
}

export const getProductList = async (params: ProductListRequest): Promise<ProductListResponse> => {
  const sort = mapSortParams(params.sortBy)
  const regionName = params.regions?.length
    ? params.regions.map(code => REGION_CODE_TO_NAME[code] || code).join(',')
    : undefined

  const res = await http.get<{
    code: number
    data: { items: Record<string, unknown>[]; pagination?: { total: number; page: number; size: number }; total?: number; page?: number; size?: number }
    message: string
  }>('/v1/products', {
    params: {
      page: params.page,
      size: params.pageSize,
      search: params.keyword,
      category: params.category,
      region: regionName,
      sort_by: sort.sort_by,
      sort_order: sort.sort_order,
    },
  })
  const inner = unwrap<{ items: Record<string, unknown>[]; pagination?: { total: number; page: number; size: number }; total?: number; page?: number }>(res)
  return {
    data: (inner.items || []).map(mapProduct),
    total: inner.pagination?.total ?? inner.total ?? 0,
    page: inner.pagination?.page ?? inner.page ?? 1,
    pageSize: params.pageSize,
  }
}

export const getProductDetail = async (id: string): Promise<ProductDetail> => {
  const res = await http.get<{ code: number; data: Record<string, unknown>; message: string }>(
    `/v1/products/${id}`
  )
  const raw = unwrap<Record<string, unknown>>(res)
  return mapProduct(raw) as ProductDetail
}

export const getCategories = async (): Promise<Category[]> => {
  const res = await http.get<{ code: number; data: { categories: string[] | Category[] }; message: string }>(
    '/v1/products-categories'
  )
  const inner = unwrap<{ categories: string[] | Category[] }>(res)
  const list = inner?.categories || []
  // 后端可能返回字符串数组或对象数组，统一映射为 Category
  return list.map((c, idx) => {
    if (typeof c === 'string') {
      return { id: c, name: c, productCount: undefined }
    }
    return { id: c.id ?? c.name ?? String(idx), name: c.name ?? '', productCount: c.productCount }
  })
}

export const getProductReviews = async (
  productId: string,
  page = 1,
  pageSize = 10
): Promise<{ data: Review[]; total: number }> => {
  const res = await http.get<{ code: number; data: { data: Review[]; total: number }; message: string }>(
    `/v1/products/${productId}/reviews`,
    { params: { page, pageSize } }
  )
  const inner = unwrap<{ data: Review[]; total: number }>(res)
  return { data: inner.data || [], total: inner.total || 0 }
}

export const addProductReview = async (
  productId: string,
  data: { rating: number; comment: string }
): Promise<Review> => {
  const res = await http.post<{ code: number; data: Review; message: string }>(
    `/v1/products/${productId}/reviews`,
    data
  )
  return unwrap<Review>(res)
}

export const searchProducts = async (keyword: string): Promise<Product[]> => {
  const res = await http.get<{ code: number; data: { items: Record<string, unknown>[] }; message: string }>(
    '/v1/products',
    { params: { search: keyword } }
  )
  const inner = unwrap<{ items: Record<string, unknown>[] }>(res)
  return (inner?.items || []).map(mapProduct)
}

// ============ 导出/备份 ============

export const exportProductsExcel = () => window.open('/api/v1/export/products?format=excel', '_blank')
export const exportProductsJSON = () => window.open('/api/v1/export/products/json', '_blank')
export const exportProductsBackup = () => window.open('/api/v1/export/products/backup', '_blank')

export const getPopularProducts = async (limit = 10): Promise<Product[]> => {
  const res = await http.get<{ code: number; data: { items: Record<string, unknown>[] }; message: string }>(
    '/v1/products-popular',
    { params: { limit } }
  )
  const inner = unwrap<{ items: Record<string, unknown>[] }>(res)
  return (inner?.items || []).map(mapProduct)
}
