/**
 * 产品状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Product, ProductDetail, Category } from '@/types/product'
import * as productAPI from '@/api/products'

export const useProductStore = defineStore('product', () => {
  // State
  const products = ref<Product[]>([])
  const categories = ref<Category[]>([])
  const currentProduct = ref<ProductDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const selectedCategory = ref<string>('')
  const searchKeyword = ref<string>('')
  const currentPage = ref(1)
  const pageSize = ref(12)
  const total = ref(0)
  const selectedRegions = ref<string[]>([])
  const sortBy = ref<'newest' | 'popular' | 'priceHigh' | 'priceLow' | ''>('')

  // Computed
  const hasMore = computed(() => currentPage.value * pageSize.value < total.value)
  // 直接返回服务端已过滤的结果，避免与 fetchProducts 的服务端过滤产生双重过滤
  const filteredProducts = computed(() => products.value)

  // Actions
  const fetchProducts = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await productAPI.getProductList({
        page: currentPage.value,
        pageSize: pageSize.value,
        category: selectedCategory.value || undefined,
        keyword: searchKeyword.value || undefined,
        regions: selectedRegions.value.length ? selectedRegions.value : undefined,
        sortBy: sortBy.value || undefined,
      })
      // Guard against unexpected API response shape
      products.value = Array.isArray(response?.data) ? response.data : []
      total.value = typeof response?.total === 'number' ? response.total : 0
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch products'
      throw err  // Re-throw so callers (setCategory etc.) can handle if needed
    } finally {
      loading.value = false
    }
  }

  const fetchProductDetail = async (id: string) => {
    loading.value = true
    error.value = null
    try {
      const product = await productAPI.getProductDetail(id)
      currentProduct.value = product
      return product
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch product'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchCategories = async () => {
    try {
      const data = await productAPI.getCategories()
      categories.value = data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch categories'
    }
  }

  const setCategory = async (categoryId: string) => {
    selectedCategory.value = categoryId
    currentPage.value = 1
    await fetchProducts()
  }

  const setSearchKeyword = async (keyword: string) => {
    searchKeyword.value = keyword
    currentPage.value = 1
    await fetchProducts()
  }

  const setPage = async (page: number) => {
    currentPage.value = page
    await fetchProducts()
  }

  const setPageSize = async (size: number) => {
    pageSize.value = size
    currentPage.value = 1
    await fetchProducts()
  }

  const clearFilters = async () => {
    selectedCategory.value = ''
    searchKeyword.value = ''
    selectedRegions.value = []
    sortBy.value = ''
    currentPage.value = 1
    await fetchProducts()
  }

  const setRegion = async (regions: string[]) => {
    selectedRegions.value = regions
    currentPage.value = 1
    await fetchProducts()
  }

  const setSortBy = async (sort: typeof sortBy.value) => {
    sortBy.value = sort
    currentPage.value = 1
    await fetchProducts()
  }

  const setAdvancedFilters = async (filters: {
    regions?: string[]
    sortBy?: typeof sortBy.value
  }) => {
    if (filters.regions !== undefined) selectedRegions.value = filters.regions
    if (filters.sortBy !== undefined) sortBy.value = filters.sortBy
    currentPage.value = 1
    await fetchProducts()
  }

  const resetState = () => {
    products.value = []
    currentProduct.value = null
    selectedCategory.value = ''
    searchKeyword.value = ''
    selectedRegions.value = []
    sortBy.value = ''
    currentPage.value = 1
    pageSize.value = 12
    total.value = 0
    error.value = null
  }

  return {
    // State
    products,
    categories,
    currentProduct,
    loading,
    error,
    selectedCategory,
    searchKeyword,
    selectedRegions,
    sortBy,
    currentPage,
    pageSize,
    total,
    // Computed
    hasMore,
    filteredProducts,
    // Actions
    fetchProducts,
    fetchProductDetail,
    fetchCategories,
    setCategory,
    setSearchKeyword,
    setPage,
    setPageSize,
    setRegion,
    setSortBy,
    setAdvancedFilters,
    clearFilters,
    resetState,
  }
})
