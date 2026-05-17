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
  const r = res as { data?: T } & T
  return r.data !== undefined ? r.data : r
}

export const getProductList = async (params: ProductListRequest): Promise<ProductListResponse> => {
  const res = await http.get<{
    code: number
    data: { items: Product[]; total: number; page: number; size: number }
    message: string
  }>('/v1/products', {
    params: {
      page: params.page,
      size: params.pageSize,     // 后端参数名为 size
      search: params.keyword,    // 后端参数名为 search
      category: params.category,
    },
  })
  const inner = unwrap<{ items: Product[]; total: number; page: number; size: number }>(res)
  return {
    data: inner.items || [],
    total: inner.total || 0,
    page: inner.page || 1,
    pageSize: params.pageSize,
  }
}

export const getProductDetail = async (id: string): Promise<ProductDetail> => {
  const res = await http.get<{ code: number; data: ProductDetail; message: string }>(
    `/v1/products/${id}`
  )
  return unwrap<ProductDetail>(res)
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
  // 后端参数名为 pageSize（非 page_size），后端返回 data.data（非 data.items）
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
  const res = await http.get<{ code: number; data: { items: Product[] }; message: string }>(
    '/v1/products',
    { params: { search: keyword } }
  )
  const inner = unwrap<{ items: Product[] }>(res)
  return inner?.items || []
}

export const getPopularProducts = async (limit = 10): Promise<Product[]> => {
  const res = await http.get<{ code: number; data: { items: Product[] }; message: string }>(
    '/v1/products-popular',
    { params: { limit } }
  )
  const inner = unwrap<{ items: Product[] }>(res)
  return inner?.items || []
}
