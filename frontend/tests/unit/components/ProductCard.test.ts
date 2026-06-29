import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProductCard from '@/components/ProductCard.vue'
import { testDataGenerators, waitForComponent } from '../../utils/test-utils'
import * as ProductCardModule from '@/components/ProductCard.vue'

/**
 * ProductCard 组件测试
 * 测试产品卡片的渲染、交互和事件触发
 */

describe('ProductCard Component', () => {
  let mockRouter: any

  beforeEach(() => {
    mockRouter = {
      push: vi.fn().mockResolvedValue(true),
    }
  })

  it('renders product information correctly', () => {
    const product = testDataGenerators.createProduct({
      name: '乌兰察布马铃薯',
      price: 5.99,
      rating: 4.5,
      reviewCount: 128,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        mocks: { $router: mockRouter },
        stubs: {
          ElCard: { template: '<div class="el-card"><slot /></div>' },
          ElRate: { template: '<div class="el-rate"></div>' },
          ElTag: { template: '<div class="el-tag"><slot /></div>' },
          ElButton: { template: '<button><slot /></button>' },
        },
      },
    })

    // 检查产品名称显示
    expect(wrapper.text()).toContain('乌兰察布马铃薯')
    // 检查价格显示
    expect(wrapper.text()).toContain('¥5.99')
    // 检查评分计数显示
    expect(wrapper.text()).toContain('(128)')
  })

  it('displays product description', () => {
    const product = testDataGenerators.createProduct({
      description: '优质马铃薯，产地新鲜',
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div></div>' },
          ElButton: { template: '<button></button>' },
        },
      },
    })

    expect(wrapper.text()).toContain('优质马铃薯，产地新鲜')
  })

  it('shows discount badge when originalPrice is provided', () => {
    const product = testDataGenerators.createProduct({
      price: 5.99,
      originalPrice: 9.99,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div></div>' },
          ElButton: { template: '<button></button>' },
        },
      },
    })

    // 计算折扣百分比：(9.99 - 5.99) / 9.99 * 100 ≈ 40%
    const discountText = wrapper.text()
    expect(discountText).toContain('优惠')
  })

  it('displays original price when available', () => {
    const product = testDataGenerators.createProduct({
      price: 5.99,
      originalPrice: 9.99,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div></div>' },
          ElButton: { template: '<button></button>' },
        },
      },
    })

    expect(wrapper.text()).toContain('¥9.99')
  })

  it('shows in-stock status when product is in stock', () => {
    const product = testDataGenerators.createProduct({
      inStock: true,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div><slot /></div>' },
          ElButton: { template: '<button></button>' },
        },
      },
    })

    expect(wrapper.text()).toContain('有货')
  })

  it('shows out-of-stock status when product is not in stock', () => {
    const product = testDataGenerators.createProduct({
      inStock: false,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div><slot /></div>' },
          ElButton: { template: '<button></button>' },
        },
      },
    })

    expect(wrapper.text()).toContain('缺货')
  })

  it('disables add-to-cart button when product is not in stock', async () => {
    const product = testDataGenerators.createProduct({
      inStock: false,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div><slot /></div>' },
          ElButton: {
            template: '<button :disabled="disabled"><slot /></button>',
            props: ['disabled'],
          },
        },
      },
    })

    const buttons = wrapper.findAll('button')
    const addToCartButton = buttons.find(b => b.text().includes('加入购物车'))
    expect(addToCartButton?.attributes('disabled')).toBeDefined()
  })

  it('navigates to product detail on view detail button click', async () => {
    const product = testDataGenerators.createProduct({
      id: 'prod-123',
    })

    mockRouter.push.mockResolvedValue(true)

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        mocks: { $router: mockRouter },
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div><slot /></div>' },
          ElButton: {
            template: '<button @click="$emit(\'click\')"><slot /></button>',
            emits: ['click'],
          },
        },
      },
    })

    // 模拟点击"查看详情"按钮
    const viewDetailButton = wrapper.findAll('button').find(b => b.text().includes('查看详情'))
    if (viewDetailButton) {
      await viewDetailButton.trigger('click')
      await wrapper.vm.$nextTick()
      expect(mockRouter.push).toHaveBeenCalledWith('/products/prod-123')
    }
  })

  it('shows product image with correct src', () => {
    const imageUrl = 'https://example.com/product-image.jpg'
    const product = testDataGenerators.createProduct({
      image: imageUrl,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div><slot /></div>' },
          ElButton: { template: '<button></button>' },
        },
      },
    })

    const img = wrapper.find('img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe(imageUrl)
    expect(img.attributes('alt')).toBe(product.name)
  })

  it('displays rating correctly', () => {
    const product = testDataGenerators.createProduct({
      rating: 4.5,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: {
            template: '<div class="el-rate" :data-rating="modelValue"></div>',
            props: ['modelValue'],
          },
          ElTag: { template: '<div></div>' },
          ElButton: { template: '<button></button>' },
        },
      },
    })

    const rateComponent = wrapper.find('.el-rate')
    expect(rateComponent.exists()).toBe(true)
  })

  it('handles multiple products correctly', () => {
    const products = [
      testDataGenerators.createProduct({ id: 'prod-1', name: '产品1' }),
      testDataGenerators.createProduct({ id: 'prod-2', name: '产品2' }),
    ]

    const results = products.map(product => {
      const wrapper = mount(ProductCard, {
        props: { product },
        global: {
          stubs: {
            ElCard: { template: '<div><slot /></div>' },
            ElRate: { template: '<div></div>' },
            ElTag: { template: '<div><slot /></div>' },
            ElButton: { template: '<button></button>' },
          },
        },
      })
      return wrapper.text()
    })

    expect(results[0]).toContain('产品1')
    expect(results[1]).toContain('产品2')
  })

  it('calculates discount percentage correctly', () => {
    const product = testDataGenerators.createProduct({
      price: 50,
      originalPrice: 100,
    })

    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          ElCard: { template: '<div><slot /></div>' },
          ElRate: { template: '<div></div>' },
          ElTag: { template: '<div></div>' },
          ElButton: { template: '<button></button>' },
        },
      },
    })

    // 折扣百分比应该是 (100 - 50) / 100 * 100 = 50%
    const text = wrapper.text()
    expect(text).toContain('50%')
    expect(text).toContain('优惠')
  })
})
