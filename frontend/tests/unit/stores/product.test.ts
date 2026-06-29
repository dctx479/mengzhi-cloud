import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProductStore } from '@/stores/product'
import * as productAPI from '@/api/products'
import { testDataGenerators } from '../../utils/test-utils'

/**
 * Product Store 测试
 * 测试产品列表、分类、搜索和分页功能
 */

vi.mock('@/api/products', () => ({
  getProductList: vi.fn(),
  getProductDetail: vi.fn(),
  getCategories: vi.fn(),
}))

describe('Product Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('fetchProducts', () => {
    it('fetches and stores products', async () => {
      const store = useProductStore()
      const products = [
        testDataGenerators.createProduct({ id: 'prod-1' }),
        testDataGenerators.createProduct({ id: 'prod-2' }),
      ]

      vi.mocked(productAPI.getProductList).mockResolvedValueOnce({
        data: products,
        total: 2,
        page: 1,
        pageSize: 12,
      })

      await store.fetchProducts()

      expect(store.products).toEqual(products)
      expect(store.total).toBe(2)
      expect(store.loading).toBe(false)
    })

    it('sets loading state during fetch', async () => {
      const store = useProductStore()

      vi.mocked(productAPI.getProductList).mockImplementation(
        () =>
          new Promise(resolve => {
            setTimeout(() => {
              resolve({
                data: [],
                total: 0,
                page: 1,
                pageSize: 12,
              })
            }, 100)
          })
      )

      const promise = store.fetchProducts()
      expect(store.loading).toBe(true)
      await promise
      expect(store.loading).toBe(false)
    })

    it('handles fetch error', async () => {
      const store = useProductStore()
      const errorMessage = 'Failed to fetch products'

      vi.mocked(productAPI.getProductList).mockRejectedValueOnce(
        new Error(errorMessage)
      )

      await store.fetchProducts()

      expect(store.error).toBe(errorMessage)
      expect(store.products).toEqual([])
    })

    it('passes correct parameters to API', async () => {
      const store = useProductStore()
      store.selectedCategory.value = 'cat-1'
      store.searchKeyword.value = 'keyword'
      store.currentPage.value = 2

      vi.mocked(productAPI.getProductList).mockResolvedValueOnce({
        data: [],
        total: 0,
        page: 2,
        pageSize: 12,
      })

      await store.fetchProducts()

      expect(productAPI.getProductList).toHaveBeenCalledWith({
        page: 2,
        pageSize: 12,
        category: 'cat-1',
        keyword: 'keyword',
      })
    })
  })

  describe('fetchProductDetail', () => {
    it('fetches and stores product detail', async () => {
      const store = useProductStore()
      const product = testDataGenerators.createProduct({ id: 'prod-1' })

      vi.mocked(productAPI.getProductDetail).mockResolvedValueOnce(product)

      const result = await store.fetchProductDetail('prod-1')

      expect(store.currentProduct).toEqual(product)
      expect(result).toEqual(product)
    })

    it('handles fetch detail error', async () => {
      const store = useProductStore()
      const errorMessage = 'Product not found'

      vi.mocked(productAPI.getProductDetail).mockRejectedValueOnce(
        new Error(errorMessage)
      )

      try {
        await store.fetchProductDetail('invalid-id')
      } catch (err) {
        // Expected error
      }

      expect(store.error).toBe(errorMessage)
    })
  })

  describe('fetchCategories', () => {
    it('fetches and stores categories', async () => {
      const store = useProductStore()
      const categories = [
        testDataGenerators.createCategory({ id: 'cat-1', name: '农产品' }),
        testDataGenerators.createCategory({ id: 'cat-2', name: '畜产品' }),
      ]

      vi.mocked(productAPI.getCategories).mockResolvedValueOnce(categories)

      await store.fetchCategories()

      expect(store.categories).toEqual(categories)
    })

    it('handles categories fetch error', async () => {
      const store = useProductStore()

      vi.mocked(productAPI.getCategories).mockRejectedValueOnce(
        new Error('Failed to fetch categories')
      )

      await store.fetchCategories()

      expect(store.categories).toEqual([])
    })
  })

  describe('setCategory', () => {
    it('sets category and resets pagination', async () => {
      const store = useProductStore()
      store.currentPage.value = 5

      vi.mocked(productAPI.getProductList).mockResolvedValueOnce({
        data: [],
        total: 0,
        page: 1,
        pageSize: 12,
      })

      await store.setCategory('cat-1')

      expect(store.selectedCategory).toBe('cat-1')
      expect(store.currentPage).toBe(1)
    })
  })

  describe('setSearchKeyword', () => {
    it('sets search keyword and resets pagination', async () => {
      const store = useProductStore()
      store.currentPage.value = 5

      vi.mocked(productAPI.getProductList).mockResolvedValueOnce({
        data: [],
        total: 0,
        page: 1,
        pageSize: 12,
      })

      await store.setSearchKeyword('马铃薯')

      expect(store.searchKeyword).toBe('马铃薯')
      expect(store.currentPage).toBe(1)
    })
  })

  describe('setPage', () => {
    it('updates current page', async () => {
      const store = useProductStore()

      vi.mocked(productAPI.getProductList).mockResolvedValueOnce({
        data: [],
        total: 0,
        page: 2,
        pageSize: 12,
      })

      await store.setPage(2)

      expect(store.currentPage).toBe(2)
    })
  })

  describe('setPageSize', () => {
    it('updates page size and resets to page 1', async () => {
      const store = useProductStore()
      store.currentPage.value = 5

      vi.mocked(productAPI.getProductList).mockResolvedValueOnce({
        data: [],
        total: 0,
        page: 1,
        pageSize: 20,
      })

      await store.setPageSize(20)

      expect(store.pageSize).toBe(20)
      expect(store.currentPage).toBe(1)
    })
  })

  describe('clearFilters', () => {
    it('clears all filters and resets pagination', async () => {
      const store = useProductStore()
      store.selectedCategory.value = 'cat-1'
      store.searchKeyword.value = 'keyword'
      store.currentPage.value = 3

      vi.mocked(productAPI.getProductList).mockResolvedValueOnce({
        data: [],
        total: 0,
        page: 1,
        pageSize: 12,
      })

      await store.clearFilters()

      expect(store.selectedCategory).toBe('')
      expect(store.searchKeyword).toBe('')
      expect(store.currentPage).toBe(1)
    })
  })

  describe('resetState', () => {
    it('resets all state to initial values', () => {
      const store = useProductStore()

      // Set some values
      store.products.value = [testDataGenerators.createProduct()]
      store.selectedCategory.value = 'cat-1'
      store.searchKeyword.value = 'keyword'
      store.currentPage.value = 3
      store.error.value = 'Some error'

      store.resetState()

      expect(store.products).toEqual([])
      expect(store.selectedCategory).toBe('')
      expect(store.searchKeyword).toBe('')
      expect(store.currentPage).toBe(1)
      expect(store.error).toBe(null)
    })
  })

  describe('Computed Properties', () => {
    it('hasMore returns true when more products available', () => {
      const store = useProductStore()
      store.currentPage.value = 1
      store.pageSize.value = 12
      store.total.value = 30

      expect(store.hasMore).toBe(true)
    })

    it('hasMore returns false when all products loaded', () => {
      const store = useProductStore()
      store.currentPage.value = 3
      store.pageSize.value = 12
      store.total.value = 30

      expect(store.hasMore).toBe(false)
    })

    it('filteredProducts filters by category', () => {
      const store = useProductStore()
      const products = [
        testDataGenerators.createProduct({ categoryId: 'cat-1' }),
        testDataGenerators.createProduct({ categoryId: 'cat-2' }),
        testDataGenerators.createProduct({ categoryId: 'cat-1' }),
      ]

      store.products.value = products
      store.selectedCategory.value = 'cat-1'

      expect(store.filteredProducts).toHaveLength(2)
      expect(store.filteredProducts[0].categoryId).toBe('cat-1')
    })

    it('filteredProducts filters by keyword', () => {
      const store = useProductStore()
      const products = [
        testDataGenerators.createProduct({ name: '马铃薯' }),
        testDataGenerators.createProduct({ name: '玉米' }),
        testDataGenerators.createProduct({ name: '土豆马铃薯' }),
      ]

      store.products.value = products
      store.searchKeyword.value = '马铃薯'

      expect(store.filteredProducts).toHaveLength(2)
    })

    it('filteredProducts applies both category and keyword filters', () => {
      const store = useProductStore()
      const products = [
        testDataGenerators.createProduct({
          categoryId: 'cat-1',
          name: '马铃薯',
        }),
        testDataGenerators.createProduct({
          categoryId: 'cat-2',
          name: '马铃薯',
        }),
        testDataGenerators.createProduct({
          categoryId: 'cat-1',
          name: '玉米',
        }),
      ]

      store.products.value = products
      store.selectedCategory.value = 'cat-1'
      store.searchKeyword.value = '马铃薯'

      expect(store.filteredProducts).toHaveLength(1)
      expect(store.filteredProducts[0].categoryId).toBe('cat-1')
      expect(store.filteredProducts[0].name).toBe('马铃薯')
    })
  })

  describe('State Management', () => {
    it('initializes with correct default state', () => {
      const store = useProductStore()

      expect(store.products).toEqual([])
      expect(store.categories).toEqual([])
      expect(store.currentProduct).toBe(null)
      expect(store.loading).toBe(false)
      expect(store.error).toBe(null)
      expect(store.selectedCategory).toBe('')
      expect(store.searchKeyword).toBe('')
      expect(store.currentPage).toBe(1)
      expect(store.pageSize).toBe(12)
      expect(store.total).toBe(0)
    })

    it('maintains state across multiple operations', async () => {
      const store = useProductStore()
      const products = [testDataGenerators.createProduct()]

      vi.mocked(productAPI.getProductList).mockResolvedValue({
        data: products,
        total: 1,
        page: 1,
        pageSize: 12,
      })

      await store.fetchProducts()
      expect(store.products).toHaveLength(1)

      await store.setCategory('cat-1')
      expect(store.selectedCategory).toBe('cat-1')
      expect(store.currentPage).toBe(1)
    })
  })

  describe('Error Handling', () => {
    it('clears error on new fetch', async () => {
      const store = useProductStore()
      store.error.value = 'Previous error'

      vi.mocked(productAPI.getProductList).mockResolvedValueOnce({
        data: [],
        total: 0,
        page: 1,
        pageSize: 12,
      })

      await store.fetchProducts()

      expect(store.error).toBe(null)
    })

    it('maintains error state on failed fetch', async () => {
      const store = useProductStore()
      const errorMessage = 'Network error'

      vi.mocked(productAPI.getProductList).mockRejectedValueOnce(
        new Error(errorMessage)
      )

      await store.fetchProducts()

      expect(store.error).toBe(errorMessage)
    })
  })
})
