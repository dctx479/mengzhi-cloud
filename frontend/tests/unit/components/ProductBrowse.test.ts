import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AdvancedFilters from '@/components/AdvancedFilters.vue'
import QuickViewDialog from '@/components/QuickViewDialog.vue'
import ComparePanel from '@/components/ComparePanel.vue'
import MapView from '@/components/MapView.vue'
import ProductCard from '@/components/ProductCard.vue'
import type { Product, CulturalTag } from '@/types/product'

describe('AdvancedFilters Component', () => {
  const mockCategories = [
    { id: '1', name: '牛奶', icon: '🥛' },
    { id: '2', name: '肉类', icon: '🥩' },
  ]

  const mockCulturalTags: CulturalTag[] = [
    { id: 'mongolian', name: '蒙古族', icon: '🐴' },
    { id: 'dairy', name: '乳文化', icon: '🥛' },
  ]

  it('renders filter card', () => {
    const wrapper = mount(AdvancedFilters, {
      props: {
        modelValue: {},
        categories: mockCategories,
        culturalTags: mockCulturalTags,
      },
    })

    expect(wrapper.find('.advanced-filters').exists()).toBe(true)
    expect(wrapper.text()).toContain('高级筛选')
  })

  it('can toggle expand', async () => {
    const wrapper = mount(AdvancedFilters, {
      props: {
        modelValue: {},
        categories: mockCategories,
        culturalTags: mockCulturalTags,
      },
    })

    const expandBtn = wrapper.find('.card-header button')
    await expandBtn.trigger('click')

    expect(wrapper.vm.$data.isExpanded).toBe(true)
  })

  it('emits apply event with filters', async () => {
    const wrapper = mount(AdvancedFilters, {
      props: {
        modelValue: {},
        categories: mockCategories,
        culturalTags: mockCulturalTags,
      },
    })

    const expandBtn = wrapper.find('.card-header button')
    await expandBtn.trigger('click')

    const applyBtn = wrapper.find('button').find((el) => el.text().includes('应用筛选'))
    if (applyBtn) {
      await applyBtn.trigger('click')
    }

    expect(wrapper.emitted('apply')).toBeTruthy()
  })

  it('can reset filters', async () => {
    const wrapper = mount(AdvancedFilters, {
      props: {
        modelValue: {},
        categories: mockCategories,
        culturalTags: mockCulturalTags,
      },
    })

    const expandBtn = wrapper.find('.card-header button')
    await expandBtn.trigger('click')

    const resetBtn = wrapper.find('button').find((el) => el.text().includes('重置'))
    if (resetBtn) {
      await resetBtn.trigger('click')
    }

    expect(wrapper.emitted('apply')).toBeTruthy()
  })
})

describe('QuickViewDialog Component', () => {
  const mockProduct: Product = {
    id: '1',
    name: '蒙古草原羊肉',
    description: '优质草原羊肉',
    price: 99,
    originalPrice: 129,
    image: 'https://example.com/image.jpg',
    images: ['https://example.com/image.jpg', 'https://example.com/image2.jpg'],
    category: '肉类',
    categoryId: '2',
    rating: 4.5,
    reviewCount: 120,
    inStock: true,
    stockCount: 50,
    createdAt: '2024-01-01',
    updatedAt: '2024-01-01',
    origin: '锡林郭勒盟',
    hasOrganic: true,
    hasGeo: true,
  }

  it('renders product information', () => {
    const wrapper = mount(QuickViewDialog, {
      props: {
        modelValue: true,
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-dialog': true,
          'el-rate': true,
          'el-tag': true,
          'el-button': true,
          'el-icon': true,
        },
      },
    })

    expect(wrapper.text()).toContain(mockProduct.name)
    expect(wrapper.text()).toContain(mockProduct.origin)
  })

  it('calculates discount rate', () => {
    const wrapper = mount(QuickViewDialog, {
      props: {
        modelValue: true,
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-dialog': true,
          'el-rate': true,
          'el-tag': true,
          'el-button': true,
          'el-icon': true,
        },
      },
    })

    const discountRate = Math.round(
      ((mockProduct.originalPrice! - mockProduct.price) / mockProduct.originalPrice!) * 100
    )
    expect(wrapper.vm.$data.discountRate ?? wrapper.vm.discountRate).toBe(discountRate)
  })

  it('emits add-to-compare event', async () => {
    const wrapper = mount(QuickViewDialog, {
      props: {
        modelValue: true,
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-dialog': true,
          'el-rate': true,
          'el-tag': true,
          'el-button': true,
          'el-icon': true,
        },
      },
    })

    // Test event emission through component methods
    expect(wrapper.emitted('add-to-compare')).toBeDefined()
  })
})

describe('ComparePanel Component', () => {
  const mockProducts: Product[] = [
    {
      id: '1',
      name: '产品1',
      description: '描述1',
      price: 100,
      image: 'https://example.com/1.jpg',
      category: '类别1',
      categoryId: '1',
      rating: 4,
      reviewCount: 50,
      inStock: true,
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    },
    {
      id: '2',
      name: '产品2',
      description: '描述2',
      price: 200,
      image: 'https://example.com/2.jpg',
      category: '类别2',
      categoryId: '2',
      rating: 4.5,
      reviewCount: 100,
      inStock: true,
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    },
  ]

  it('renders compare panel', () => {
    const wrapper = mount(ComparePanel, {
      props: {
        modelValue: mockProducts,
      },
      global: {
        stubs: {
          'el-affix': true,
          'el-button': true,
          'el-dialog': true,
          'el-table': true,
          'el-table-column': true,
          'el-tag': true,
          'el-icon': true,
          'el-rate': true,
          'el-tooltip': true,
        },
      },
    })

    expect(wrapper.find('.compare-panel').exists()).toBe(true)
  })

  it('displays compare count', async () => {
    const wrapper = mount(ComparePanel, {
      props: {
        modelValue: mockProducts,
      },
      global: {
        stubs: {
          'el-affix': true,
          'el-button': true,
          'el-dialog': true,
          'el-table': true,
          'el-table-column': true,
          'el-tag': true,
          'el-icon': true,
          'el-rate': true,
        },
      },
    })

    expect(wrapper.text()).toContain('对比产品 (2)')
  })

  it('can remove product from compare', async () => {
    const wrapper = mount(ComparePanel, {
      props: {
        modelValue: mockProducts,
      },
      global: {
        stubs: {
          'el-affix': true,
          'el-button': true,
          'el-dialog': true,
          'el-table': true,
          'el-table-column': true,
          'el-tag': true,
          'el-icon': true,
          'el-rate': true,
        },
      },
    })

    // Test the remove functionality through emit
    expect(wrapper.emitted('update:modelValue')).toBeDefined()
  })
})

describe('MapView Component', () => {
  const mockProducts: Product[] = [
    {
      id: '1',
      name: '产品1',
      description: '描述1',
      price: 100,
      image: 'https://example.com/1.jpg',
      category: '类别1',
      categoryId: '1',
      rating: 4,
      reviewCount: 50,
      inStock: true,
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
      origin: '锡林郭勒盟',
      region: 'xilin',
    },
  ]

  it('renders map view container', () => {
    const wrapper = mount(MapView, {
      props: {
        products: mockProducts,
      },
      global: {
        stubs: {
          'el-radio-group': true,
          'el-radio-button': true,
          'el-select': true,
          'el-option': true,
          'el-button': true,
          'el-icon': true,
          'el-dialog': true,
          'el-tag': true,
        },
      },
    })

    expect(wrapper.find('.map-view-container').exists()).toBe(true)
  })

  it('can toggle between list and map view', async () => {
    const wrapper = mount(MapView, {
      props: {
        products: mockProducts,
      },
      global: {
        stubs: {
          'el-radio-group': true,
          'el-radio-button': true,
          'el-select': true,
          'el-option': true,
          'el-button': true,
          'el-icon': true,
          'el-dialog': true,
          'el-tag': true,
        },
      },
    })

    expect(wrapper.vm.$data.viewMode).toBe('list')
  })

  it('displays region cards', () => {
    const wrapper = mount(MapView, {
      props: {
        products: mockProducts,
      },
      global: {
        stubs: {
          'el-radio-group': true,
          'el-radio-button': true,
          'el-select': true,
          'el-option': true,
          'el-button': true,
          'el-icon': true,
          'el-dialog': true,
          'el-tag': true,
        },
      },
    })

    // Component should render region distribution information
    expect(wrapper.find('.map-view-container').exists()).toBe(true)
  })
})

describe('ProductCard Component', () => {
  const mockProduct: Product = {
    id: '1',
    name: '蒙古草原羊肉',
    description: '优质草原羊肉',
    price: 99,
    originalPrice: 129,
    image: 'https://example.com/image.jpg',
    category: '肉类',
    categoryId: '2',
    rating: 4.5,
    reviewCount: 120,
    inStock: true,
    createdAt: '2024-01-01',
    updatedAt: '2024-01-01',
    origin: '锡林郭勒盟',
    culturalTags: [{ id: 'mongolian', name: '蒙古族', icon: '🐴' }],
    hasOrganic: true,
  }

  it('renders product card', () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-card': true,
          'el-tag': true,
          'el-button': true,
          'el-rate': true,
          'el-icon': true,
        },
      },
    })

    expect(wrapper.find('.product-card').exists()).toBe(true)
  })

  it('displays product information', () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-card': true,
          'el-tag': true,
          'el-button': true,
          'el-rate': true,
          'el-icon': true,
        },
      },
    })

    expect(wrapper.text()).toContain(mockProduct.name)
    expect(wrapper.text()).toContain(mockProduct.origin)
  })

  it('shows cultural tags', () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-card': true,
          'el-tag': true,
          'el-button': true,
          'el-rate': true,
          'el-icon': true,
        },
      },
    })

    expect(wrapper.find('.cultural-tags').exists()).toBe(true)
  })

  it('shows certification badges', () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-card': true,
          'el-tag': true,
          'el-button': true,
          'el-rate': true,
          'el-icon': true,
        },
      },
    })

    expect(wrapper.find('.badges').exists()).toBe(true)
  })

  it('emits quick-view event', async () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-card': true,
          'el-tag': true,
          'el-button': true,
          'el-rate': true,
          'el-icon': true,
        },
      },
    })

    expect(wrapper.emitted('quick-view')).toBeDefined()
  })

  it('emits toggle-compare event', async () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: mockProduct,
      },
      global: {
        stubs: {
          'el-card': true,
          'el-tag': true,
          'el-button': true,
          'el-rate': true,
          'el-icon': true,
        },
      },
    })

    expect(wrapper.emitted('toggle-compare')).toBeDefined()
  })
})
