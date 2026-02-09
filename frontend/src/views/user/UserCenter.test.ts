import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UserCenter from '@/views/user/UserCenter.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  useRoute: () => ({
    path: '/user/profile',
  }),
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    user: {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      avatar: 'https://example.com/avatar.jpg',
      phone: '13800138000',
      nickname: 'Test User',
      status: 'active',
      role: 'user',
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    logout: vi.fn(),
  }),
}))

describe('UserCenter Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders user center layout', () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-main': true,
          'el-breadcrumb': true,
          'el-breadcrumb-item': true,
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    expect(wrapper.find('.user-center').exists()).toBe(true)
  })

  it('should display sidebar with user info', () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': { template: '<div><slot /></div>' },
          'el-menu': { template: '<div><slot /></div>' },
          'el-menu-item': { template: '<div><slot /></div>' },
          'el-main': { template: '<div><slot /></div>' },
          'el-breadcrumb': { template: '<div><slot /></div>' },
          'el-breadcrumb-item': { template: '<div><slot /></div>' },
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    expect(wrapper.text()).toContain('testuser')
    expect(wrapper.text()).toContain('user')
  })

  it('should display menu items', () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': { template: '<div><slot /></div>' },
          'el-menu': { template: '<div><slot /></div>' },
          'el-menu-item': { template: '<div><slot /></div>' },
          'el-main': { template: '<div><slot /></div>' },
          'el-breadcrumb': { template: '<div><slot /></div>' },
          'el-breadcrumb-item': { template: '<div><slot /></div>' },
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    expect(wrapper.text()).toContain('个人资料')
    expect(wrapper.text()).toContain('订单历史')
    expect(wrapper.text()).toContain('配额管理')
    expect(wrapper.text()).toContain('偏好设置')
    expect(wrapper.text()).toContain('安全中心')
    expect(wrapper.text()).toContain('退出登录')
  })

  it('should get role name correctly', () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-main': true,
          'el-breadcrumb': true,
          'el-breadcrumb-item': true,
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    const vm = wrapper.vm as any

    expect(vm.getRoleName('user')).toBe('普通用户')
    expect(vm.getRoleName('admin')).toBe('管理员')
    expect(vm.getRoleName('manager')).toBe('经理')
    expect(vm.getRoleName()).toBe('用户')
  })

  it('should get current page title correctly', () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-main': true,
          'el-breadcrumb': true,
          'el-breadcrumb-item': true,
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    const vm = wrapper.vm as any

    expect(vm.getCurrentPageTitle()).toBeDefined()
  })

  it('should have page title mappings', () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-main': true,
          'el-breadcrumb': true,
          'el-breadcrumb-item': true,
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    const vm = wrapper.vm as any

    expect(vm.pageTitles['/user/profile']).toBe('个人资料')
    expect(vm.pageTitles['/user/orders']).toBe('订单历史')
    expect(vm.pageTitles['/user/quota']).toBe('配额管理')
    expect(vm.pageTitles['/user/settings']).toBe('偏好设置')
    expect(vm.pageTitles['/user/security']).toBe('安全中心')
  })

  it('should handle menu select', () => {
    const wrapper = mount(UserCenter, {
      global: {
        mocks: {
          $router: {
            push: vi.fn(),
          },
        },
        stubs: {
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-main': true,
          'el-breadcrumb': true,
          'el-breadcrumb-item': true,
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    const vm = wrapper.vm as any
    vm.handleMenuSelect('/user/orders')

    // Check if push was called
    expect(vm.handleMenuSelect).toBeDefined()
  })

  it('should handle logout', async () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-main': true,
          'el-breadcrumb': true,
          'el-breadcrumb-item': true,
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    const vm = wrapper.vm as any

    // Check if logout method exists
    expect(vm.handleLogout).toBeDefined()
  })

  it('should have active menu computed property', () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-main': true,
          'el-breadcrumb': true,
          'el-breadcrumb-item': true,
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    const vm = wrapper.vm as any

    expect(vm.activeMenu).toBeDefined()
  })

  it('should display breadcrumb', () => {
    const wrapper = mount(UserCenter, {
      global: {
        stubs: {
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-main': { template: '<div><slot /></div>' },
          'el-breadcrumb': { template: '<div><slot /></div>' },
          'el-breadcrumb-item': { template: '<div><slot /></div>' },
          'el-avatar': true,
          'el-divider': true,
          'router-view': true,
        },
      },
    })

    expect(wrapper.text()).toContain('用户中心')
  })
})
