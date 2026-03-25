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

  // Computed
  const hasMore = computed(() => currentPage.value * pageSize.value < total.value)
  const filteredProducts = computed(() => {
    let filtered = products.value
    if (selectedCategory.value) {
      filtered = filtered.filter((p) => p.categoryId === selectedCategory.value)
    }
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(keyword) ||
          (p.description || '').toLowerCase().includes(keyword)
      )
    }
    return filtered
  })

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
      })
      products.value = response.data
      total.value = response.total
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch products'
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
    try {
      selectedCategory.value = categoryId
      currentPage.value = 1
      await fetchProducts()
    } catch (err) {
      // Error already handled in fetchProducts(), propagate for caller
      throw err
    }
  }

  const setSearchKeyword = async (keyword: string) => {
    try {
      searchKeyword.value = keyword
      currentPage.value = 1
      await fetchProducts()
    } catch (err) {
      // Error already handled in fetchProducts(), propagate for caller
      throw err
    }
  }

  const setPage = async (page: number) => {
    try {
      currentPage.value = page
      await fetchProducts()
    } catch (err) {
      // Error already handled in fetchProducts(), propagate for caller
      throw err
    }
  }

  const setPageSize = async (size: number) => {
    try {
      pageSize.value = size
      currentPage.value = 1
      await fetchProducts()
    } catch (err) {
      // Error already handled in fetchProducts(), propagate for caller
      throw err
    }
  }

  const clearFilters = async () => {
    try {
      selectedCategory.value = ''
      searchKeyword.value = ''
      currentPage.value = 1
      await fetchProducts()
    } catch (err) {
      // Error already handled in fetchProducts(), propagate for caller
      throw err
    }
  }

  const resetState = () => {
    products.value = []
    currentProduct.value = null
    selectedCategory.value = ''
    searchKeyword.value = ''
    currentPage.value = 1
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
    clearFilters,
    resetState,
  }
})
