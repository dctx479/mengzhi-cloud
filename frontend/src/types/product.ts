/**
 * 产品相关类型定义
 */

export interface CulturalTag {
  id: string
  name: string
  icon: string
  description?: string
}

export interface LocationCoord {
  latitude: number
  longitude: number
}

export interface Product {
  id: string
  name: string
  description: string
  price: number
  originalPrice?: number
  image: string
  images?: string[]
  category: string
  categoryId: string
  rating: number
  reviewCount: number
  inStock: boolean
  stockCount?: number
  createdAt: string
  updatedAt: string
  // 农产品特定字段
  origin?: string // 产地
  region?: string // 地区
  location?: LocationCoord // 地理位置坐标
  culturalTags?: CulturalTag[] // 文化标签
  hasOrganic?: boolean // 有机认证
  hasGeo?: boolean // 地理标志
  hasQuality?: boolean // 质量认证
  unit?: string // 单位
  supplier?: string // 供应商
  specifications?: Record<string, string> // 规格参数
}

export interface ProductDetail extends Product {
  tags?: string[]
  benefits?: string[]
  relatedProducts?: Product[]
}

export interface AdvancedFilters {
  category?: string[]
  priceRange?: [number, number]
  regions?: string[]
  culturalTags?: string[]
  certifications?: string[]
  sortBy?: 'recommend' | 'price_asc' | 'price_desc' | 'newest' | 'sales'
}

export interface ProductListRequest {
  page: number
  pageSize: number
  category?: string
  keyword?: string
  sortBy?: 'newest' | 'popular' | 'priceHigh' | 'priceLow'
  // 高级筛选字段
  priceMin?: number
  priceMax?: number
  regions?: string[]
  culturalTags?: string[]
  certifications?: string[]
}

export interface ProductListResponse {
  data: Product[]
  total: number
  page: number
  pageSize: number
}

export interface Category {
  id: string
  name: string
  icon?: string
  description?: string
  productCount?: number
}

export interface Review {
  id: string
  productId: string
  userId: string
  userName: string
  userAvatar?: string
  rating: number
  comment: string
  createdAt: string
}
