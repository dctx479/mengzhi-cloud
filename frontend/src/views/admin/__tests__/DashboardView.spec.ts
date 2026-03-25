import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises, VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import DashboardView from '../DashboardView.vue'
import type { AdminStats, AIUsageData } from '@/types/admin'

// Mock echarts
vi.mock('echarts', () => ({
  default: {
    init: vi.fn(() => ({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn()
    }))
  },
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  }))
}))

// Mock admin API
const mockGetStats = vi.fn()
const mockGetAIUsage = vi.fn()

vi.mock('@/api/admin', () => ({
  adminApi: {
    getStats: () => mockGetStats(),
    getAIUsage: () => mockGetAIUsage()
  }
}))


describe('DashboardView.vue', () => {
  let wrapper: VueWrapper<any>

  const mockStats: AdminStats = {
    totalUsers: 150,
    totalEnterprises: 25,
    totalAIUsage: 5000,
    activeUsers: 80
  }

  const mockUsageData: AIUsageData[] = [
    { date: '2024-01-01', count: 100 },
    { date: '2024-01-02', count: 150 },
    { date: '2024-01-03', count: 200 },
    { date: '2024-01-04', count: 180 },
    { date: '2024-01-05', count: 220 }
  ]

  const createWrapper = () => {
    return mount(DashboardView, {
      global: {
        stubs: {
          'el-row': {
            template: '<div class="el-row"><slot /></div>',
            props: ['gutter']
          },
          'el-col': {
            template: '<div class="el-col"><slot /></div>',
            props: ['span']
          },
          'el-card': {
            template: '<div class="el-card"><div v-if="$slots.header" class="el-card__header"><slot name="header" /></div><slot /></div>'
          }
        }
      }
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetStats.mockResolvedValue({ data: mockStats })
    mockGetAIUsage.mockResolvedValue({ data: mockUsageData })
  })

  describe('Component Rendering', () => {
    it('should render the dashboard', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.dashboard').exists()).toBe(true)
    })

    it('should render stat cards', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const cards = wrapper.findAll('.el-card')
      expect(cards.length).toBeGreaterThanOrEqual(4)
    })

    it('should render chart card', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.chart-card').exists()).toBe(true)
      expect(wrapper.html()).toContain('AI使用趋势')
    })

    it('should render all stat labels', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.html()).toContain('总用户数')
      expect(wrapper.html()).toContain('总企业数')
      expect(wrapper.html()).toContain('AI调用次数')
      expect(wrapper.html()).toContain('活跃用户')
    })
  })

  describe('Data Loading', () => {
    it('should load stats on mount', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(mockGetStats).toHaveBeenCalled()
      expect(wrapper.vm.statsData).toEqual(mockStats)
    })

    it('should load AI usage data on mount', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(mockGetAIUsage).toHaveBeenCalled()
      expect(wrapper.vm.usageData).toEqual(mockUsageData)
    })

    it('should load both stats and usage in parallel', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(mockGetStats).toHaveBeenCalled()
      expect(mockGetAIUsage).toHaveBeenCalled()
    })

    it('should handle stats loading error', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockGetStats.mockRejectedValue(new Error('Stats load failed'))

      wrapper = createWrapper()
      await flushPromises()

      expect(consoleError).toHaveBeenCalledWith('加载数据失败:', expect.any(Error))
      consoleError.mockRestore()
    })

    it('should handle usage data loading error', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockGetAIUsage.mockRejectedValue(new Error('Usage load failed'))

      wrapper = createWrapper()
      await flushPromises()

      expect(consoleError).toHaveBeenCalledWith('加载数据失败:', expect.any(Error))
      consoleError.mockRestore()
    })

    it('should handle partial data loading failure', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockGetStats.mockResolvedValue({ data: mockStats })
      mockGetAIUsage.mockRejectedValue(new Error('Usage failed'))

      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.statsData).toEqual(mockStats)
      expect(consoleError).toHaveBeenCalled()
      consoleError.mockRestore()
    })
  })

  describe('Stats Display', () => {
    it('should display correct stat values', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const statValues = wrapper.findAll('.stat-value')
      expect(statValues.length).toBe(4)
      expect(statValues[0].text()).toBe('150')
      expect(statValues[1].text()).toBe('25')
      expect(statValues[2].text()).toBe('5000')
      expect(statValues[3].text()).toBe('80')
    })

    it('should display stat labels', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const statLabels = wrapper.findAll('.stat-label')
      expect(statLabels.length).toBe(4)
      expect(statLabels[0].text()).toBe('总用户数')
      expect(statLabels[1].text()).toBe('总企业数')
      expect(statLabels[2].text()).toBe('AI调用次数')
      expect(statLabels[3].text()).toBe('活跃用户')
    })

    it('should show 0 when stats are not loaded', async () => {
      mockGetStats.mockResolvedValue({ data: null })

      wrapper = createWrapper()
      await flushPromises()

      const statValues = wrapper.findAll('.stat-value')
      statValues.forEach((value) => {
        expect(value.text()).toBe('0')
      })
    })

    it('should handle undefined stats gracefully', async () => {
      mockGetStats.mockResolvedValue({ data: undefined })

      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.stats).toBeDefined()
      expect(wrapper.vm.stats.every((s: any) => s.value === 0)).toBe(true)
    })
  })

  describe('Chart Rendering', () => {
    it('should render chart after data loads', async () => {
      const echarts = await import('echarts')
      const mockChart = {
        setOption: vi.fn(),
        resize: vi.fn(),
        dispose: vi.fn()
      }
      vi.mocked(echarts.init).mockReturnValue(mockChart as any)

      wrapper = createWrapper()
      await flushPromises()

      expect(echarts.init).toHaveBeenCalled()
      expect(mockChart.setOption).toHaveBeenCalled()
    })

    it('should pass correct data to chart', async () => {
      const echarts = await import('echarts')
      const mockChart = {
        setOption: vi.fn(),
        resize: vi.fn(),
        dispose: vi.fn()
      }
      vi.mocked(echarts.init).mockReturnValue(mockChart as any)

      wrapper = createWrapper()
      await flushPromises()

      const chartOptions = mockChart.setOption.mock.calls[0][0]
      expect(chartOptions.xAxis.data).toEqual(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'])
      expect(chartOptions.series[0].data).toEqual([100, 150, 200, 180, 220])
    })

    it('should not render chart if chartRef is not available', async () => {
      const echarts = await import('echarts')

      wrapper = createWrapper()
      wrapper.vm.chartRef = null
      await wrapper.vm.renderChart()

      expect(echarts.init).not.toHaveBeenCalled()
    })

    it('should handle empty usage data', async () => {
      mockGetAIUsage.mockResolvedValue({ data: [] })

      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.usageData).toEqual([])
    })
  })

  describe('Computed Properties', () => {
    it('should compute stats array correctly', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const stats = wrapper.vm.stats
      expect(stats).toHaveLength(4)
      expect(stats[0]).toEqual({ label: '总用户数', value: 150 })
      expect(stats[1]).toEqual({ label: '总企业数', value: 25 })
      expect(stats[2]).toEqual({ label: 'AI调用次数', value: 5000 })
      expect(stats[3]).toEqual({ label: '活跃用户', value: 80 })
    })

    it('should update stats when data changes', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.statsData = {
        totalUsers: 200,
        totalEnterprises: 30,
        totalAIUsage: 6000,
        activeUsers: 100
      }
      await nextTick()

      const stats = wrapper.vm.stats
      expect(stats[0].value).toBe(200)
      expect(stats[1].value).toBe(30)
      expect(stats[2].value).toBe(6000)
      expect(stats[3].value).toBe(100)
    })
  })

  describe('Lifecycle', () => {
    it('should call loadData on mount', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(mockGetStats).toHaveBeenCalledTimes(1)
      expect(mockGetAIUsage).toHaveBeenCalledTimes(1)
    })

    it('should initialize with empty data', () => {
      wrapper = createWrapper()

      expect(wrapper.vm.statsData).toBeUndefined()
      expect(wrapper.vm.usageData).toEqual([])
    })
  })

  describe('Error Handling', () => {
    it('should not crash on API error', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockGetStats.mockRejectedValue(new Error('API Error'))
      mockGetAIUsage.mockRejectedValue(new Error('API Error'))

      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.dashboard').exists()).toBe(true)
      consoleError.mockRestore()
    })

    it('should display 0 values on error', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockGetStats.mockRejectedValue(new Error('API Error'))

      wrapper = createWrapper()
      await flushPromises()

      const statValues = wrapper.findAll('.stat-value')
      statValues.forEach((value) => {
        expect(value.text()).toBe('0')
      })
      consoleError.mockRestore()
    })
  })

  describe('Styling', () => {
    it('should have correct CSS classes', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.dashboard').exists()).toBe(true)
      expect(wrapper.find('.stat-card').exists()).toBe(true)
      expect(wrapper.find('.stat-value').exists()).toBe(true)
      expect(wrapper.find('.stat-label').exists()).toBe(true)
      expect(wrapper.find('.chart-card').exists()).toBe(true)
    })

    it('should apply correct styling to stat values', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const statValue = wrapper.find('.stat-value')
      expect(statValue.exists()).toBe(true)
    })
  })
})
