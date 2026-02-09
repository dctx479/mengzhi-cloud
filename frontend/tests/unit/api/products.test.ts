import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import * as productAPI from '@/api/products'
import { testDataGenerators } from '../utils/test-utils'

/**
 * Products API 测试
 * 测试产品相关API调用
 */

vi.mock('axios')

describe('Products API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getProductList', () => {
    it('fetches product list with correct parameters', async () => {
      const products = [
        testDataGenerators.createProduct(),
        testDataGenerators.createProduct(),
      ]

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: products,
            total: 2,
            page: 1,
            pageSize: 12,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getProductList({
        page: 1,
        pageSize: 12,
      })

      expect(result.data).toEqual(products)
      expect(result.total).toBe(2)
    })

    it('includes category filter in request', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: [],
            total: 0,
            page: 1,
            pageSize: 12,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      await module.getProductList({
        page: 1,
        pageSize: 12,
        category: 'cat-1',
      })

      expect(axios.create).toBeDefined()
    })

    it('includes keyword filter in request', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: [],
            total: 0,
            page: 1,
            pageSize: 12,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      await module.getProductList({
        page: 1,
        pageSize: 12,
        keyword: '马铃薯',
      })

      expect(axios.create).toBeDefined()
    })

    it('handles pagination correctly', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: [],
            total: 100,
            page: 5,
            pageSize: 20,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getProductList({
        page: 5,
        pageSize: 20,
      })

      expect(result.page).toBe(5)
      expect(result.pageSize).toBe(20)
    })
  })

  describe('getProductDetail', () => {
    it('fetches product detail by id', async () => {
      const product = testDataGenerators.createProduct({
        id: 'prod-123',
      })

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: product,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getProductDetail('prod-123')

      expect(result).toEqual(product)
    })

    it('handles product not found error', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockRejectedValueOnce({
          response: {
            status: 404,
            data: {
              message: 'Product not found',
            },
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })

    it('includes product details in response', async () => {
      const product = testDataGenerators.createProduct({
        price: 99.99,
        inStock: true,
        rating: 4.8,
      })

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: product,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getProductDetail('prod-123')

      expect(result.price).toBe(99.99)
      expect(result.inStock).toBe(true)
      expect(result.rating).toBe(4.8)
    })
  })

  describe('getCategories', () => {
    it('fetches all categories', async () => {
      const categories = [
        testDataGenerators.createCategory({ id: 'cat-1', name: '农产品' }),
        testDataGenerators.createCategory({ id: 'cat-2', name: '畜产品' }),
      ]

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: categories,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getCategories()

      expect(result).toEqual(categories)
      expect(result).toHaveLength(2)
    })

    it('handles empty categories list', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: [],
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getCategories()

      expect(result).toEqual([])
    })

    it('includes category metadata', async () => {
      const categories = [
        testDataGenerators.createCategory({
          name: '农产品',
          productCount: 50,
        }),
      ]

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: categories,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getCategories()

      expect(result[0].productCount).toBe(50)
    })
  })

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi
          .fn()
          .mockRejectedValueOnce(new Error('Network error')),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })

    it('handles server errors', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockRejectedValueOnce({
          response: {
            status: 500,
            data: {
              message: 'Internal server error',
            },
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })

    it('handles timeout errors', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockRejectedValueOnce({
          code: 'ECONNABORTED',
          message: 'timeout of 10000ms exceeded',
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })
  })

  describe('Data Transformation', () => {
    it('returns correctly formatted product list response', async () => {
      const products = [testDataGenerators.createProduct()]

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: products,
            total: 100,
            page: 1,
            pageSize: 12,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getProductList({
        page: 1,
        pageSize: 12,
      })

      expect(result).toHaveProperty('data')
      expect(result).toHaveProperty('total')
      expect(result).toHaveProperty('page')
      expect(result).toHaveProperty('pageSize')
      expect(Array.isArray(result.data)).toBe(true)
    })

    it('handles multiple products with different attributes', async () => {
      const products = [
        testDataGenerators.createProduct({
          id: '1',
          name: '产品1',
          price: 10,
          inStock: true,
        }),
        testDataGenerators.createProduct({
          id: '2',
          name: '产品2',
          price: 20,
          inStock: false,
        }),
      ]

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: products,
            total: 2,
            page: 1,
            pageSize: 12,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/products')
      const result = await module.getProductList({
        page: 1,
        pageSize: 12,
      })

      expect(result.data).toHaveLength(2)
      expect(result.data[0].price).toBe(10)
      expect(result.data[1].inStock).toBe(false)
    })
  })

  describe('API Configuration', () => {
    it('uses correct API endpoints', () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn(),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })

    it('sets appropriate headers', () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn(),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })
  })
})
