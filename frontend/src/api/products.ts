/**
 * 产品 API 服务
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

export const getProductList = (params: ProductListRequest): Promise<ProductListResponse> =>
  http.get('/v1/products', { params })

export const getProductDetail = (id: string): Promise<ProductDetail> =>
  http.get(`/v1/products/${id}`)

export const getCategories = (): Promise<Category[]> =>
  http.get('/v1/products-categories')

export const getProductReviews = (
  productId: string,
  page = 1,
  pageSize = 10
): Promise<{ data: Review[]; total: number }> =>
  http.get(`/v1/products/${productId}/reviews`, { params: { page, pageSize } })

export const addProductReview = (
  productId: string,
  data: { rating: number; comment: string }
): Promise<Review> =>
  http.post(`/v1/products/${productId}/reviews`, data)

export const searchProducts = (keyword: string): Promise<Product[]> =>
  http.get('/v1/products/search', { params: { keyword } })

export const getPopularProducts = (limit = 10): Promise<Product[]> =>
  http.get('/v1/products-popular', { params: { limit } })
