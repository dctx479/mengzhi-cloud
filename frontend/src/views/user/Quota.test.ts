import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Quota from '@/views/user/Quota.vue'
import * as userAPI from '@/api/user'

vi.mock('@/api/user', () => ({
  getQuota: vi.fn(),
  getQuotaHistory: vi.fn(),
}))

describe('Quota Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders quota page with title', () => {
    const wrapper = mount(Quota)
    expect(wrapper.find('.quota-page').exists()).toBe(true)
  })

  it('should display quota overview cards', async () => {
    const mockQuota = {
      chat_used: 50,
      chat_total: 100,
      content_used: 25,
      content_total: 50,
      storage_used: 500 * 1024 * 1024, // 500MB
      storage_total: 1024 * 1024 * 1024, // 1GB
    }

    vi.mocked(userAPI.getQuota).mockResolvedValue(mockQuota)
    vi.mocked(userAPI.getQuotaHistory).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    })

    const wrapper = mount(Quota)
    await wrapper.vm.$nextTick()

    // Check if quota data is loaded
    expect(wrapper.text()).toContain('AI对话次数')
    expect(wrapper.text()).toContain('内容生成次数')
    expect(wrapper.text()).toContain('文件存储')
  })

  it('should calculate quota percentages correctly', async () => {
    const wrapper = mount(Quota)
    const vm = wrapper.vm as any

    // Set test data
    vm.quotaData = {
      chat_used: 50,
      chat_total: 100,
      content_used: 25,
      content_total: 50,
      storage_used: 500 * 1024 * 1024,
      storage_total: 1024 * 1024 * 1024,
    }

    expect(vm.chatQuotaPercent).toBe(50)
    expect(vm.contentQuotaPercent).toBe(50)
    expect(vm.storageQuotaPercent).toBe(50)
  })

  it('should show upgrade hint when quota usage is high', async () => {
    const wrapper = mount(Quota)
    const vm = wrapper.vm as any

    // Set high usage
    vm.quotaData = {
      chat_used: 90,
      chat_total: 100,
      content_used: 25,
      content_total: 50,
      storage_used: 100,
      storage_total: 1000,
    }

    expect(vm.shouldShowUpgradeHint).toBe(true)
  })

  it('should format file size correctly', () => {
    const wrapper = mount(Quota)
    const vm = wrapper.vm as any

    expect(vm.formatFileSize(0)).toBe('0 B')
    expect(vm.formatFileSize(1024)).toContain('KB')
    expect(vm.formatFileSize(1024 * 1024)).toContain('MB')
    expect(vm.formatFileSize(1024 * 1024 * 1024)).toContain('GB')
  })

  it('should get progress color based on percentage', () => {
    const wrapper = mount(Quota)
    const vm = wrapper.vm as any

    expect(vm.getProgressColor(30)).toBe('#67c23a') // green
    expect(vm.getProgressColor(60)).toBe('#e6a23c') // orange
    expect(vm.getProgressColor(85)).toBe('#f56c6c') // red
  })

  it('should get quota type text correctly', () => {
    const wrapper = mount(Quota)
    const vm = wrapper.vm as any

    expect(vm.getQuotaTypeText('chat')).toBe('AI对话')
    expect(vm.getQuotaTypeText('content')).toBe('内容生成')
    expect(vm.getQuotaTypeText('storage')).toBe('文件存储')
  })

  it('should get quota type tag correctly', () => {
    const wrapper = mount(Quota)
    const vm = wrapper.vm as any

    expect(vm.getQuotaTypeTag('chat')).toBe('primary')
    expect(vm.getQuotaTypeTag('content')).toBe('success')
    expect(vm.getQuotaTypeTag('storage')).toBe('warning')
  })

  it('should display quota history', async () => {
    const mockHistory = [
      {
        id: '1',
        type: 'chat' as const,
        amount: 10,
        created_at: '2024-01-01T00:00:00Z',
        description: '使用对话功能',
      },
    ]

    vi.mocked(userAPI.getQuota).mockResolvedValue({
      chat_used: 10,
      chat_total: 100,
      content_used: 0,
      content_total: 50,
      storage_used: 0,
      storage_total: 1024 * 1024 * 1024,
    })

    vi.mocked(userAPI.getQuotaHistory).mockResolvedValue({
      items: mockHistory,
      total: 1,
      page: 1,
      page_size: 10,
    })

    const wrapper = mount(Quota)
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('使用对话功能')
  })

  it('should have upgrade plans available', () => {
    const wrapper = mount(Quota)
    const vm = wrapper.vm as any

    expect(vm.upgradePlans).toHaveLength(3)
    expect(vm.upgradePlans[0].id).toBe('pro')
    expect(vm.upgradePlans[1].id).toBe('business')
    expect(vm.upgradePlans[2].id).toBe('enterprise')
  })

  it('should format date time correctly', () => {
    const wrapper = mount(Quota)
    const vm = wrapper.vm as any

    const dateStr = '2024-01-01T12:00:00Z'
    const formatted = vm.formatDateTime(dateStr)
    expect(formatted).toBeTruthy()
    expect(formatted).toContain('2024')
  })
})
