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

export const getProductList = async (params: ProductListRequest): Promise<ProductListResponse> => {
  const res = await http.get<{
    code: number
    data: { items: Record<string, unknown>[]; pagination?: { total: number; page: number; size: number }; total?: number; page?: number; size?: number }
    message: string
  }>('/v1/products', {
    params: {
      page: params.page,
      size: params.pageSize,     // 后端参数名为 size
      search: params.keyword,    // 后端参数名为 search
      category: params.category,
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
  const res = await http.get<{ code: number; data: { categories: Category[] }; message: string }>(
    '/v1/products-categories'
  )
  const inner = unwrap<{ categories: Category[] }>(res)
  return inner?.categories || []
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

export const getPopularProducts = async (limit = 10): Promise<Product[]> => {
  const res = await http.get<{ code: number; data: { items: Record<string, unknown>[] }; message: string }>(
    '/v1/products-popular',
    { params: { limit } }
  )
  const inner = unwrap<{ items: Record<string, unknown>[] }>(res)
  return (inner?.items || []).map(mapProduct)
}
