import { vi } from 'vitest'

/**
 * Mock数据和函数
 */

export const mockRouterPush = vi.fn().mockResolvedValue(true)
export const mockRouterReplace = vi.fn().mockResolvedValue(true)

export const mockRouter = {
  push: mockRouterPush,
  replace: mockRouterReplace,
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  currentRoute: {
    value: {
      path: '/',
      name: 'home',
      params: {},
      query: {},
    },
  },
}

export const mockElMessage = {
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
}

export const mockElMessageBox = {
  confirm: vi.fn().mockResolvedValue(true),
  alert: vi.fn().mockResolvedValue(true),
}

export const mockAxios = {
  post: vi.fn(),
  get: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
  create: vi.fn(() => mockAxios),
  defaults: {
    headers: {
      common: {},
    },
  },
}

/**
 * Mock localStorage操作日志（用于测试）
 */
export const localStorageLog = {
  setItems: [] as Array<{ key: string; value: string }>,
  getItems: [] as Array<{ key: string }>,
  removeItems: [] as Array<{ key: string }>,

  reset() {
    this.setItems = []
    this.getItems = []
    this.removeItems = []
  },
}

/**
 * 重置所有Mock
 */
export function resetAllMocks() {
  mockRouterPush.mockClear()
  mockRouterReplace.mockClear()
  mockElMessage.success.mockClear()
  mockElMessage.error.mockClear()
  mockElMessage.warning.mockClear()
  mockElMessage.info.mockClear()
  mockElMessageBox.confirm.mockClear()
  mockElMessageBox.alert.mockClear()
  mockAxios.post.mockClear()
  mockAxios.get.mockClear()
  mockAxios.put.mockClear()
  mockAxios.patch.mockClear()
  mockAxios.delete.mockClear()
  localStorageLog.reset()
}
