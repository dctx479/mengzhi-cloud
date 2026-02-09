import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import type { ComponentMountingOptions } from '@vue/test-utils'
import { vi } from 'vitest'

/**
 * 测试工具函数
 * 提供组件挂载、Mock路由、Mock Store等功能
 */

interface MountOptions extends ComponentMountingOptions<any> {
  router?: boolean
  pinia?: boolean
}

/**
 * 创建测试用的Pinia Store
 */
export function createTestPinia() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return pinia
}

/**
 * 创建测试用的路由
 */
export function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
      { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
      { path: '/products', name: 'products', component: { template: '<div>Products</div>' } },
      { path: '/products/:id', name: 'product-detail', component: { template: '<div>Detail</div>' } },
      { path: '/chat', name: 'chat', component: { template: '<div>Chat</div>' } },
      { path: '/user/profile', name: 'profile', component: { template: '<div>Profile</div>' } },
    ],
  })
}

/**
 * 挂载Vue组件用于测试
 */
export function mountComponent(
  component: any,
  options: MountOptions = {}
) {
  const {
    router: useRouter = false,
    pinia: usePinia = false,
    ...restOptions
  } = options

  const global = {
    ...restOptions.global,
    plugins: [],
  }

  if (usePinia) {
    const pinia = createTestPinia()
    global.plugins?.push(pinia)
  }

  if (useRouter) {
    const router = createTestRouter()
    global.plugins?.push(router)
  }

  return mount(component, {
    ...restOptions,
    global,
  })
}

/**
 * 测试数据生成器
 */
export const testDataGenerators = {
  /**
   * 生成测试用户数据
   */
  createUser(overrides = {}) {
    return {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      avatar: 'https://example.com/avatar.jpg',
      phone: '13800000000',
      status: 'active' as const,
      role: 'user' as const,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
      ...overrides,
    }
  },

  /**
   * 生成测试产品数据
   */
  createProduct(overrides = {}) {
    return {
      id: 'prod-1',
      name: '乌兰察布马铃薯',
      description: '优质马铃薯，产地新鲜',
      price: 5.99,
      originalPrice: 9.99,
      image: 'https://example.com/product.jpg',
      category: '农产品',
      categoryId: 'cat-1',
      rating: 4.5,
      reviewCount: 128,
      inStock: true,
      stockCount: 100,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
      ...overrides,
    }
  },

  /**
   * 生成测试消息数据
   */
  createMessage(overrides = {}) {
    return {
      id: 'msg-1',
      content: '你好，我可以帮你什么？',
      role: 'assistant' as const,
      timestamp: new Date().toISOString(),
      status: 'sent' as const,
      ...overrides,
    }
  },

  /**
   * 生成测试对话数据
   */
  createChat(overrides = {}) {
    return {
      id: 'chat-1',
      title: '新对话',
      messages: [],
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
      userId: '1',
      ...overrides,
    }
  },

  /**
   * 生成测试分类数据
   */
  createCategory(overrides = {}) {
    return {
      id: 'cat-1',
      name: '农产品',
      icon: 'category',
      description: '新鲜农产品',
      productCount: 50,
      ...overrides,
    }
  },
}

/**
 * Mock axios响应
 */
export function mockAxiosResponse(data: any, status = 200) {
  return Promise.resolve({
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: {},
  })
}

/**
 * Mock axios错误
 */
export function mockAxiosError(message: string, status = 500) {
  return Promise.reject(
    new Error(message)
  )
}

/**
 * 等待异步操作完成
 */
export async function flushPromises() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

/**
 * 等待DOM更新
 */
export async function waitForComponent(wrapper: VueWrapper) {
  await wrapper.vm.$nextTick()
  await flushPromises()
  await wrapper.vm.$nextTick()
}

/**
 * 查找组件
 */
export function findByTestId(wrapper: VueWrapper, testId: string) {
  return wrapper.find(`[data-testid="${testId}"]`)
}

/**
 * 触发事件
 */
export async function triggerEvent(wrapper: VueWrapper, selector: string, event: string) {
  const element = wrapper.find(selector)
  await element.trigger(event)
  await wrapper.vm.$nextTick()
}

/**
 * 设置输入框值
 */
export async function setInputValue(wrapper: VueWrapper, selector: string, value: string) {
  const input = wrapper.find(selector)
  await input.setValue(value)
  await input.trigger('input')
  await wrapper.vm.$nextTick()
}
