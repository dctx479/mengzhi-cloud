import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import Header from '@/components/Header.vue'
import { testDataGenerators } from '../utils/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '@/stores/user'
import type { Router } from 'vue-router'

describe('Header Component', () => {
  let mockRouter: Partial<Router>

  beforeEach(() => {
    setActivePinia(createPinia())
    mockRouter = {
      push: vi.fn().mockResolvedValue(true),
      currentRoute: {
        value: {
          path: '/',
        },
      },
    }
  })

  it('displays logo and title', () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': {
            template: '<input class="el-input" />',
            props: ['modelValue', 'placeholder'],
            emits: ['update:modelValue', 'keyup.enter'],
          },
          'el-icon': { template: '<i></i>' },
          'Search': { template: '<i></i>' },
          'el-dropdown': { template: '<div><slot /></div>' },
          'el-dropdown-menu': { template: '<div><slot /></div>' },
          'el-dropdown-item': { template: '<div><slot /></div>' },
          'el-dropdown-divider': { template: '<hr />' },
          'el-avatar': { template: '<div class="avatar"></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('AI赋能云平台')
  })

  it('displays navigation menu items', () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': { template: '<input class="el-input" />' },
          'el-icon': { template: '<i></i>' },
          'Search': { template: '<i></i>' },
          'el-dropdown': { template: '<div><slot /></div>' },
          'el-dropdown-menu': { template: '<div><slot /></div>' },
          'el-dropdown-item': { template: '<div><slot /></div>' },
          'el-dropdown-divider': { template: '<hr />' },
          'el-avatar': { template: '<div></div>' },
        },
      },
    })

    const text = wrapper.text()
    expect(text).toContain('首页')
    expect(text).toContain('产品')
    expect(text).toContain('AI助手')
  })

  it('shows login/register buttons when not logged in', () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': { template: '<input class="el-input" />' },
          'el-icon': { template: '<i></i>' },
          'Search': { template: '<i></i>' },
          'el-dropdown': { template: '<div><slot /></div>' },
          'el-dropdown-menu': { template: '<div><slot /></div>' },
          'el-dropdown-item': { template: '<div><slot /></div>' },
          'el-dropdown-divider': { template: '<hr />' },
          'el-avatar': { template: '<div></div>' },
        },
      },
    })

    const text = wrapper.text()
    expect(text).toContain('登录')
    expect(text).toContain('注册')
  })

  it('shows user menu when logged in', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const userStore = useUserStore()
    userStore.user = testDataGenerators.createUser({
      username: 'testuser',
      avatar: 'https://example.com/avatar.jpg',
    })
    userStore.isLoggedIn = true

    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [pinia],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': { template: '<input class="el-input" />' },
          'el-icon': { template: '<i></i>' },
          'Search': { template: '<i></i>' },
          'el-dropdown': {
            template: '<div class="dropdown"><slot /></div>',
          },
          'el-dropdown-menu': { template: '<div><slot /></div>' },
          'el-dropdown-item': {
            template: '<div class="dropdown-item"><slot /></div>',
            emits: ['click'],
          },
          'el-dropdown-divider': { template: '<hr />' },
          'el-avatar': { template: '<div class="avatar"></div>' },
        },
      },
    })

    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('testuser')
  })

  it('displays search input', () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': {
            template: '<input class="search-input" :placeholder="placeholder" />',
            props: ['modelValue', 'placeholder'],
          },
          'el-icon': { template: '<i></i>' },
          'Search': { template: '<i></i>' },
          'el-dropdown': { template: '<div><slot /></div>' },
          'el-dropdown-menu': { template: '<div><slot /></div>' },
          'el-dropdown-item': { template: '<div><slot /></div>' },
          'el-dropdown-divider': { template: '<hr />' },
          'el-avatar': { template: '<div></div>' },
        },
      },
    })

    const searchInput = wrapper.find('.search-input')
    expect(searchInput.exists()).toBe(true)
  })

  it('has correct header structure', () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': { template: '<input class="el-input" />' },
          'el-icon': { template: '<i></i>' },
          'Search': { template: '<i></i>' },
          'el-dropdown': { template: '<div><slot /></div>' },
          'el-dropdown-menu': { template: '<div><slot /></div>' },
          'el-dropdown-item': { template: '<div><slot /></div>' },
          'el-dropdown-divider': { template: '<hr />' },
          'el-avatar': { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.find('.header').exists()).toBe(true)
    expect(wrapper.find('.header-container').exists()).toBe(true)
    expect(wrapper.find('.header-logo').exists()).toBe(true)
    expect(wrapper.find('.header-nav').exists()).toBe(true)
    expect(wrapper.find('.header-user').exists()).toBe(true)
  })
})
