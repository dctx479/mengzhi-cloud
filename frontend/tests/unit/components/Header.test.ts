import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Header from '@/components/Header.vue'
import { testDataGenerators } from '../utils/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '@/stores/user'

/**
 * Header 组件测试
 * 测试页头的登录/未登录状态、搜索功能和导航
 */

describe('Header Component', () => {
  let mockRouter: any

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

  it('navigates to products page with search keyword', async () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': {
            template: `
              <div>
                <input
                  class="el-input"
                  v-model="value"
                  @keyup.enter="$emit('keyup.enter')"
                />
              </div>
            `,
            props: ['modelValue'],
            emits: ['update:modelValue', 'keyup.enter'],
            methods: {
              handleEnter() {
                this.$emit('keyup.enter')
              },
            },
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

    // 设置搜索关键词
    const input = wrapper.find('.el-input')
    await input.setValue('马铃薯')
    await wrapper.vm.$nextTick()

    // 触发搜索
    await input.trigger('keyup.enter')
    await wrapper.vm.$nextTick()

    expect(mockRouter.push).toHaveBeenCalled()
  })

  it('does not navigate if search keyword is empty', async () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': {
            template: `
              <input
                class="el-input"
                v-model="value"
                @keyup.enter="$emit('keyup.enter')"
              />
            `,
            props: ['modelValue'],
            emits: ['update:modelValue', 'keyup.enter'],
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

    mockRouter.push.mockClear()

    // 清空搜索关键词并触发搜索
    const input = wrapper.find('.el-input')
    await input.setValue('')
    await wrapper.vm.$nextTick()
    await input.trigger('keyup.enter')
    await wrapper.vm.$nextTick()

    expect(mockRouter.push).not.toHaveBeenCalled()
  })

  it('handles user logout correctly', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const userStore = useUserStore()
    userStore.user = testDataGenerators.createUser()
    userStore.isLoggedIn = true
    userStore.logout = vi.fn().mockResolvedValue(undefined)

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
          'el-dropdown': { template: '<div><slot /></div>' },
          'el-dropdown-menu': { template: '<div><slot /></div>' },
          'el-dropdown-item': {
            template: '<div class="dropdown-item" @click="$emit(\'click\')"><slot /></div>',
            emits: ['click'],
          },
          'el-dropdown-divider': { template: '<hr />' },
          'el-avatar': { template: '<div></div>' },
        },
      },
    })

    await wrapper.vm.$nextTick()
  })

  it('shows login button links to login page', () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a :to="to" :href="to"><slot /></a>',
            props: ['to'],
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

    const links = wrapper.findAll('a')
    const loginLink = links.find(link => link.text().includes('登录'))
    expect(loginLink?.attributes('to')).toBe('/login')
  })

  it('shows register button links to register page', () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a :to="to" :href="to"><slot /></a>',
            props: ['to'],
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

    const links = wrapper.findAll('a')
    const registerLink = links.find(link => link.text().includes('注册'))
    expect(registerLink?.attributes('to')).toBe('/register')
  })

  it('displays search placeholder text', () => {
    const wrapper = mount(Header, {
      global: {
        mocks: { $router: mockRouter },
        plugins: [createPinia()],
        stubs: {
          'router-link': {
            template: '<a><slot /></a>',
          },
          'el-input': {
            template: '<input class="el-input" :placeholder="placeholder" />',
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

    const input = wrapper.find('.el-input')
    expect(input.attributes('placeholder')).toBe('搜索产品...')
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
