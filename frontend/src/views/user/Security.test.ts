import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Security from '@/views/user/Security.vue'
import * as userAPI from '@/api/user'

vi.mock('@/api/user', () => ({
  changePassword: vi.fn(),
  getSecurityLogs: vi.fn(),
  getDevices: vi.fn(),
  removeDevice: vi.fn(),
  bindPhone: vi.fn(),
  bindEmail: vi.fn(),
  sendVerificationCode: vi.fn(),
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    user: {
      email: 'test@example.com',
      phone: '13800138000',
    },
    fetchCurrentUser: vi.fn(),
    logout: vi.fn(),
  }),
}))

describe('Security Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders security page', () => {
    const wrapper = mount(Security)
    expect(wrapper.find('.security-page').exists()).toBe(true)
  })

  it('should display password management section', () => {
    const wrapper = mount(Security)
    expect(wrapper.text()).toContain('密码管理')
    expect(wrapper.text()).toContain('当前密码')
    expect(wrapper.text()).toContain('新密码')
  })

  it('should display contact methods section', () => {
    const wrapper = mount(Security)
    expect(wrapper.text()).toContain('联系方式')
    expect(wrapper.text()).toContain('邮箱地址')
    expect(wrapper.text()).toContain('手机号')
  })

  it('should display login history section', () => {
    const wrapper = mount(Security)
    expect(wrapper.text()).toContain('登录历史')
  })

  it('should display device management section', () => {
    const wrapper = mount(Security)
    expect(wrapper.text()).toContain('设备管理')
  })

  it('should get event text correctly', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.getEventText('login')).toBe('登录')
    expect(vm.getEventText('logout')).toBe('登出')
    expect(vm.getEventText('password_change')).toBe('修改密码')
    expect(vm.getEventText('phone_bind')).toBe('绑定手机')
    expect(vm.getEventText('email_change')).toBe('更改邮箱')
  })

  it('should parse user agent correctly', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.parseUserAgent('Windows NT')).toBe('Windows')
    expect(vm.parseUserAgent('Macintosh')).toBe('macOS')
    expect(vm.parseUserAgent('Linux')).toBe('Linux')
    expect(vm.parseUserAgent('iPhone')).toBe('iPhone')
    expect(vm.parseUserAgent('Android')).toBe('Android')
    expect(vm.parseUserAgent('Unknown')).toBe('未知设备')
  })

  it('should format date time correctly', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    const dateStr = '2024-01-01T12:00:00Z'
    const formatted = vm.formatDateTime(dateStr)
    expect(formatted).toBeTruthy()
  })

  it('should load security logs on mount', async () => {
    const mockLogs = [
      {
        id: '1',
        event_type: 'login',
        ip_address: '192.168.1.1',
        user_agent: 'Chrome',
        created_at: '2024-01-01T00:00:00Z',
        success: true,
      },
    ]

    vi.mocked(userAPI.getSecurityLogs).mockResolvedValue({
      items: mockLogs,
      total: 1,
    })

    const wrapper = mount(Security)
    await wrapper.vm.$nextTick()

    expect(userAPI.getSecurityLogs).toHaveBeenCalled()
  })

  it('should load devices on mount', async () => {
    const mockDevices = [
      {
        id: '1',
        device_name: 'Chrome on Windows',
        device_type: 'Desktop',
        ip_address: '192.168.1.1',
        last_login: '2024-01-01T00:00:00Z',
        is_current: true,
      },
    ]

    vi.mocked(userAPI.getDevices).mockResolvedValue(mockDevices)

    const wrapper = mount(Security)
    await wrapper.vm.$nextTick()

    expect(userAPI.getDevices).toHaveBeenCalled()
  })

  it('should initialize password form with empty values', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.passwordForm).toEqual({
      old_password: '',
      new_password: '',
      confirm_password: '',
    })
  })

  it('should have password validation rules', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.passwordRules).toBeDefined()
    expect(vm.passwordRules.old_password).toBeDefined()
    expect(vm.passwordRules.new_password).toBeDefined()
    expect(vm.passwordRules.confirm_password).toBeDefined()
  })

  it('should initialize phone form with empty values', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.phoneForm).toEqual({
      phone: '',
      verification_code: '',
    })
  })

  it('should have phone validation rules', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.phoneRules).toBeDefined()
    expect(vm.phoneRules.phone).toBeDefined()
    expect(vm.phoneRules.verification_code).toBeDefined()
  })

  it('should initialize email form with empty values', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.emailForm).toEqual({
      email: '',
      verification_code: '',
    })
  })

  it('should have email validation rules', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.emailRules).toBeDefined()
    expect(vm.emailRules.email).toBeDefined()
    expect(vm.emailRules.verification_code).toBeDefined()
  })

  it('should show bind phone dialog', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.bindPhoneDialogVisible).toBe(false)
    vm.handleBindPhone()
    expect(vm.bindPhoneDialogVisible).toBe(true)
  })

  it('should show change email dialog', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.changeEmailDialogVisible).toBe(false)
    vm.handleChangeEmail()
    expect(vm.changeEmailDialogVisible).toBe(true)
  })

  it('should have empty security logs initially', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.securityLogs).toEqual([])
    expect(vm.logTotal).toBe(0)
  })

  it('should have empty devices initially', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.devices).toEqual([])
  })

  it('should initialize countdown to 0', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.countDown).toBe(0)
  })

  it('should have loading flags set to false initially', () => {
    const wrapper = mount(Security)
    const vm = wrapper.vm as any

    expect(vm.loadingLogs).toBe(false)
    expect(vm.loadingDevices).toBe(false)
    expect(vm.changingPassword).toBe(false)
    expect(vm.sendingCode).toBe(false)
  })
})
