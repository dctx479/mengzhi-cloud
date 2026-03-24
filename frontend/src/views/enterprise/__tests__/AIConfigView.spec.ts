import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import AIConfigView from '../AIConfigView.vue'
import * as aiConfigApi from '@/api/aiConfig'
import type { AIConfig } from '@/types/aiConfig'

// Mock the API module
vi.mock('@/api/aiConfig', () => ({
  getAIConfigs: vi.fn(),
  createAIConfig: vi.fn(),
  updateAIConfig: vi.fn(),
  deleteAIConfig: vi.fn(),
  testAIConfig: vi.fn()
}))

// Mock Element Plus components
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn((_options: any) => ({
      close: vi.fn()
    }))
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

describe('AIConfigView.vue', () => {
  let wrapper: any

  const mockConfigs: AIConfig[] = [
    {
      id: '1',
      name: 'OpenAI Config',
      provider: 'openai',
      apiKey: 'sk-test-key',
      model: 'gpt-4',
      isActive: true,
      createdAt: '2024-01-01T00:00:00Z'
    },
    {
      id: '2',
      name: 'Azure Config',
      provider: 'azure',
      apiKey: 'azure-key',
      endpoint: 'https://azure.openai.com',
      model: 'gpt-4',
      isActive: false,
      createdAt: '2024-01-02T00:00:00Z'
    }
  ]

  const createWrapper = () => {
    return mount(AIConfigView, {
      global: {
        stubs: {
          'el-card': {
            template: '<div class="el-card"><div v-if="$slots.header" class="el-card__header"><slot name="header" /></div><slot /></div>'
          },
          'el-button': {
            template: '<button @click="$emit(\'click\')"><slot /></button>',
            props: ['type', 'link', 'loading']
          },
          'el-table': {
            template: '<table><slot /></table>',
            props: ['data', 'loading']
          },
          'el-table-column': {
            template: '<td><slot :row="row" /></td>',
            props: ['prop', 'label', 'width']
          },
          'el-tag': {
            template: '<span :class="`el-tag--${type}`"><slot /></span>',
            props: ['type']
          },
          'el-dialog': {
            template: '<div v-if="modelValue" class="el-dialog"><div class="el-dialog__header"><slot name="header">{{ title }}</slot></div><slot /><div v-if="$slots.footer" class="el-dialog__footer"><slot name="footer" /></div></div>',
            props: ['modelValue', 'title', 'width'],
            emits: ['update:modelValue', 'close']
          },
          'AIConfigForm': {
            template: '<div class="ai-config-form"></div>',
            methods: {
              validate: vi.fn().mockResolvedValue(true)
            }
          }
        }
      }
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(aiConfigApi.getAIConfigs).mockResolvedValue(mockConfigs)
  })

  describe('Component Rendering', () => {
    it('should render the component', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.ai-config-view').exists()).toBe(true)
      expect(wrapper.find('.el-card').exists()).toBe(true)
    })

    it('should render header with title and add button', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.html()).toContain('AI配置管理')
      const buttons = wrapper.findAll('button')
      expect(buttons.some((btn: any) => btn.text().includes('添加配置'))).toBe(true)
    })

    it('should render table with configs', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('table').exists()).toBe(true)
    })
  })

  describe('Data Loading', () => {
    it('should load configs on mount', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(aiConfigApi.getAIConfigs).toHaveBeenCalledWith('1')
      expect(wrapper.vm.configs).toEqual(mockConfigs)
    })

    it('should handle loading error', async () => {
      const { ElMessage } = await import('element-plus')
      vi.mocked(aiConfigApi.getAIConfigs).mockRejectedValue(new Error('Network error'))

      wrapper = createWrapper()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('should set loading state during data fetch', async () => {
      let resolvePromise: any
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      vi.mocked(aiConfigApi.getAIConfigs).mockReturnValue(promise as any)

      wrapper = createWrapper()
      expect(wrapper.vm.loading).toBe(true)

      resolvePromise(mockConfigs)
      await flushPromises()

      expect(wrapper.vm.loading).toBe(false)
    })
  })

  describe('Add Configuration', () => {
    it('should open dialog when add button is clicked', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const addButton = wrapper.findAll('button').find((btn: any) =>
        btn.text().includes('添加配置')
      )
      await addButton.trigger('click')
      await nextTick()

      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('添加AI配置')
      expect(wrapper.vm.editingId).toBeUndefined()
    })

    it('should create new config on submit', async () => {
      const { ElMessage } = await import('element-plus')
      vi.mocked(aiConfigApi.createAIConfig).mockResolvedValue({
        id: '3',
        name: 'New Config',
        provider: 'openai',
        apiKey: 'new-key',
        model: 'gpt-4',
        isActive: true,
        createdAt: '2024-01-03T00:00:00Z'
      })

      wrapper = createWrapper()
      await flushPromises()

      // Open dialog
      wrapper.vm.dialogVisible = true
      wrapper.vm.formData = {
        name: 'New Config',
        provider: 'openai',
        apiKey: 'new-key',
        model: 'gpt-4',
        isActive: true
      }
      await nextTick()

      // Submit
      await wrapper.vm.handleSubmit()
      await flushPromises()

      expect(aiConfigApi.createAIConfig).toHaveBeenCalledWith('1', wrapper.vm.formData)
      expect(ElMessage.success).toHaveBeenCalledWith('添加成功')
      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('should handle create error', async () => {
      const { ElMessage } = await import('element-plus')
      vi.mocked(aiConfigApi.createAIConfig).mockRejectedValue(new Error('Create failed'))

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      wrapper.vm.formData = {
        name: 'New Config',
        provider: 'openai',
        apiKey: 'new-key',
        model: 'gpt-4',
        isActive: true
      }

      await wrapper.vm.handleSubmit()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalled()
      expect(wrapper.vm.submitting).toBe(false)
    })
  })

  describe('Edit Configuration', () => {
    it('should open dialog with config data when edit is clicked', async () => {
      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.handleEdit(mockConfigs[0])
      await nextTick()

      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.dialogTitle).toBe('编辑AI配置')
      expect(wrapper.vm.editingId).toBe('1')
      expect(wrapper.vm.formData.name).toBe('OpenAI Config')
    })

    it('should update config on submit', async () => {
      const { ElMessage } = await import('element-plus')
      vi.mocked(aiConfigApi.updateAIConfig).mockResolvedValue({
        ...mockConfigs[0],
        name: 'Updated Config'
      })

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editingId = '1'
      wrapper.vm.dialogVisible = true
      wrapper.vm.formData = {
        name: 'Updated Config',
        provider: 'openai',
        apiKey: 'sk-test-key',
        model: 'gpt-4',
        isActive: true
      }

      await wrapper.vm.handleSubmit()
      await flushPromises()

      expect(aiConfigApi.updateAIConfig).toHaveBeenCalledWith('1', '1', wrapper.vm.formData)
      expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('should handle update error', async () => {
      const { ElMessage } = await import('element-plus')
      vi.mocked(aiConfigApi.updateAIConfig).mockRejectedValue(new Error('Update failed'))

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editingId = '1'
      wrapper.vm.dialogVisible = true
      wrapper.vm.formData = mockConfigs[0]

      await wrapper.vm.handleSubmit()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalled()
    })
  })

  describe('Delete Configuration', () => {
    it('should delete config after confirmation', async () => {
      const { ElMessage, ElMessageBox } = await import('element-plus')
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
      vi.mocked(aiConfigApi.deleteAIConfig).mockResolvedValue(undefined as any)

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.handleDelete(mockConfigs[0])
      await flushPromises()

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定删除该配置吗？',
        '提示',
        { type: 'warning' }
      )
      expect(aiConfigApi.deleteAIConfig).toHaveBeenCalledWith('1', '1')
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('should not delete if user cancels', async () => {
      const { ElMessageBox } = await import('element-plus')
      vi.mocked(ElMessageBox.confirm).mockRejectedValue('cancel')

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.handleDelete(mockConfigs[0])
      await flushPromises()

      expect(aiConfigApi.deleteAIConfig).not.toHaveBeenCalled()
    })

    it('should handle delete error', async () => {
      const { ElMessage, ElMessageBox } = await import('element-plus')
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
      vi.mocked(aiConfigApi.deleteAIConfig).mockRejectedValue(new Error('Delete failed'))

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.handleDelete(mockConfigs[0])
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalled()
    })
  })

  describe('Test Configuration', () => {
    it('should test config connection successfully', async () => {
      const { ElMessage } = await import('element-plus')
      vi.mocked(aiConfigApi.testAIConfig).mockResolvedValue({
        success: true,
        message: '连接成功'
      })

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.handleTest(mockConfigs[0])
      await flushPromises()

      expect(aiConfigApi.testAIConfig).toHaveBeenCalledWith('1', '1')
      expect(ElMessage.success).toHaveBeenCalled()
    })

    it('should handle test failure', async () => {
      const { ElMessage } = await import('element-plus')
      vi.mocked(aiConfigApi.testAIConfig).mockRejectedValue(new Error('Connection failed'))

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.handleTest(mockConfigs[0])
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('should show loading message during test', async () => {
      const { ElMessage } = await import('element-plus')
      let resolvePromise: any
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      vi.mocked(aiConfigApi.testAIConfig).mockReturnValue(promise as any)

      wrapper = createWrapper()
      await flushPromises()

      const testPromise = wrapper.vm.handleTest(mockConfigs[0])
      expect(ElMessage.info).toHaveBeenCalledWith({
        message: '测试中...',
        duration: 0
      })

      resolvePromise({ success: true, message: '连接成功' })
      await testPromise
      await flushPromises()
    })
  })

  describe('Form Reset', () => {
    it('should reset form when dialog closes', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.formData = {
        name: 'Test',
        provider: 'azure',
        apiKey: 'key',
        endpoint: 'endpoint',
        model: 'model',
        isActive: false
      }

      wrapper.vm.resetForm()

      expect(wrapper.vm.formData).toEqual({
        name: '',
        provider: 'openai',
        apiKey: '',
        endpoint: '',
        model: '',
        isActive: true
      })
    })
  })

  describe('Provider Mapping', () => {
    it('should have correct provider map', () => {
      wrapper = createWrapper()

      expect(wrapper.vm.providerMap).toEqual({
        openai: 'OpenAI',
        azure: 'Azure',
        anthropic: 'Anthropic',
        custom: '自定义'
      })
    })
  })

  describe('Form Validation', () => {
    it('should validate form before submit', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true)
      }

      await wrapper.vm.handleSubmit()

      expect(wrapper.vm.formRef.validate).toHaveBeenCalled()
    })

    it('should not submit if validation fails', async () => {
      const { ElMessage: _ElMessage } = await import('element-plus')
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      wrapper.vm.formRef = {
        validate: vi.fn().mockRejectedValue(false)
      }

      await wrapper.vm.handleSubmit()

      expect(aiConfigApi.createAIConfig).not.toHaveBeenCalled()
      expect(aiConfigApi.updateAIConfig).not.toHaveBeenCalled()
    })
  })
})
