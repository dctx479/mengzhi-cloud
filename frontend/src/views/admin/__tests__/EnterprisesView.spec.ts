import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import EnterprisesView from '../EnterprisesView.vue'
import type { Enterprise } from '@/types/admin'

// Mock admin API
const mockGetEnterprises = vi.fn()
const mockUpdateEnterprise = vi.fn()
const mockDeleteEnterprise = vi.fn()

vi.mock('@/api/admin', () => ({
  adminApi: {
    getEnterprises: (params?: any) => mockGetEnterprises(params),
    updateEnterprise: (id: number, data: any) => mockUpdateEnterprise(id, data),
    deleteEnterprise: (id: number) => mockDeleteEnterprise(id)
  }
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('EnterprisesView.vue', () => {
  let wrapper: any

  const mockEnterprises: Enterprise[] = [
    {
      id: 1,
      name: 'Tech Corp',
      contactPerson: 'John Doe',
      email: 'contact@techcorp.com',
      status: 'active',
      createdAt: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      name: 'Innovation Ltd',
      contactPerson: 'Jane Smith',
      email: 'info@innovation.com',
      status: 'inactive',
      createdAt: '2024-01-02T00:00:00Z'
    }
  ]

  const createWrapper = () => {
    return mount(EnterprisesView, {
      global: {
        stubs: {
          'el-card': {
            template: '<div class="el-card"><div v-if="$slots.header" class="el-card__header"><slot name="header" /></div><slot /></div>'
          },
          'el-input': {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" @input.native="$emit(\'input\')" />',
            props: ['modelValue', 'placeholder', 'clearable']
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
          'el-button': {
            template: '<button @click="$emit(\'click\')"><slot /></button>',
            props: ['size', 'type']
          },
          'el-popconfirm': {
            template: '<div><slot name="reference" /></div>',
            props: ['title'],
            emits: ['confirm']
          },
          'el-dialog': {
            template: '<div v-if="modelValue" class="el-dialog"><slot /><div v-if="$slots.footer" class="el-dialog__footer"><slot name="footer" /></div></div>',
            props: ['modelValue', 'title', 'width'],
            emits: ['update:modelValue']
          },
          'el-form': {
            template: '<form><slot /></form>',
            props: ['model', 'labelWidth']
          },
          'el-form-item': {
            template: '<div><slot /></div>',
            props: ['label']
          },
          'el-select': {
            template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
            props: ['modelValue']
          },
          'el-option': {
            template: '<option :value="value">{{ label }}</option>',
            props: ['label', 'value']
          }
        }
      }
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetEnterprises.mockResolvedValue({ data: mockEnterprises })
  })

  describe('Component Rendering', () => {
    it('should render the enterprises view', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.enterprises-view').exists()).toBe(true)
      expect(wrapper.find('.el-card').exists()).toBe(true)
    })

    it('should render header with title and search', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.html()).toContain('企业管理')
      expect(wrapper.find('input').exists()).toBe(true)
    })

    it('should render enterprises table', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('table').exists()).toBe(true)
    })

    it('should render search input with placeholder', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toBe('搜索企业')
    })
  })

  describe('Data Loading', () => {
    it('should load enterprises on mount', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(mockGetEnterprises).toHaveBeenCalledWith({ search: '' })
      expect(wrapper.vm.enterprises).toEqual(mockEnterprises)
    })

    it('should set loading state during fetch', async () => {
      let resolvePromise: any
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      mockGetEnterprises.mockReturnValue(promise)

      wrapper = createWrapper()
      expect(wrapper.vm.loading).toBe(true)

      resolvePromise({ data: mockEnterprises })
      await flushPromises()

      expect(wrapper.vm.loading).toBe(false)
    })

    it('should handle loading error', async () => {
      const { ElMessage } = await import('element-plus')
      mockGetEnterprises.mockRejectedValue(new Error('Load failed'))

      wrapper = createWrapper()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('加载失败')
    })

    it('should handle empty enterprises list', async () => {
      mockGetEnterprises.mockResolvedValue({ data: [] })

      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.enterprises).toEqual([])
    })
  })

  describe('Search Functionality', () => {
    it('should search enterprises when input changes', async () => {
      wrapper = createWrapper()
      await flushPromises()

      mockGetEnterprises.mockClear()
      const input = wrapper.find('input')
      await input.setValue('Tech')
      await wrapper.vm.loadEnterprises()
      await flushPromises()

      expect(mockGetEnterprises).toHaveBeenCalledWith({ search: 'Tech' })
    })

    it('should update search value', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const input = wrapper.find('input')
      await input.setValue('test search')
      await nextTick()

      expect(wrapper.vm.search).toBe('test search')
    })

    it('should reload enterprises with search term', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.search = 'Innovation'
      await wrapper.vm.loadEnterprises()
      await flushPromises()

      expect(mockGetEnterprises).toHaveBeenCalledWith({ search: 'Innovation' })
    })

    it('should handle search with empty string', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.search = ''
      await wrapper.vm.loadEnterprises()

      expect(mockGetEnterprises).toHaveBeenCalledWith({ search: '' })
    })
  })

  describe('Edit Enterprise', () => {
    it('should open dialog when edit button is clicked', async () => {
      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.editEnterprise(mockEnterprises[0])
      await nextTick()

      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.editForm).toEqual(mockEnterprises[0])
    })

    it('should populate form with enterprise data', async () => {
      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.editEnterprise(mockEnterprises[0])

      expect(wrapper.vm.editForm.name).toBe('Tech Corp')
      expect(wrapper.vm.editForm.contactPerson).toBe('John Doe')
      expect(wrapper.vm.editForm.email).toBe('contact@techcorp.com')
      expect(wrapper.vm.editForm.status).toBe('active')
    })

    it('should save enterprise changes', async () => {
      const { ElMessage } = await import('element-plus')
      mockUpdateEnterprise.mockResolvedValue({ data: { ...mockEnterprises[0], name: 'Updated Corp' } })

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editForm = { ...mockEnterprises[0], name: 'Updated Corp' }
      wrapper.vm.dialogVisible = true

      await wrapper.vm.saveEnterprise()
      await flushPromises()

      expect(mockUpdateEnterprise).toHaveBeenCalledWith(1, wrapper.vm.editForm)
      expect(ElMessage.success).toHaveBeenCalledWith('保存成功')
      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('should handle save error', async () => {
      const { ElMessage } = await import('element-plus')
      mockUpdateEnterprise.mockRejectedValue(new Error('Save failed'))

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editForm = mockEnterprises[0]
      await wrapper.vm.saveEnterprise()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('保存失败')
    })

    it('should reload enterprises after successful save', async () => {
      mockUpdateEnterprise.mockResolvedValue({ data: mockEnterprises[0] })

      wrapper = createWrapper()
      await flushPromises()

      mockGetEnterprises.mockClear()
      wrapper.vm.editForm = mockEnterprises[0]
      await wrapper.vm.saveEnterprise()
      await flushPromises()

      expect(mockGetEnterprises).toHaveBeenCalled()
    })
  })

  describe('Delete Enterprise', () => {
    it('should delete enterprise', async () => {
      const { ElMessage } = await import('element-plus')
      mockDeleteEnterprise.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteEnterprise(1)
      await flushPromises()

      expect(mockDeleteEnterprise).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('should handle delete error', async () => {
      const { ElMessage } = await import('element-plus')
      mockDeleteEnterprise.mockRejectedValue(new Error('Delete failed'))

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteEnterprise(1)
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('删除失败')
    })

    it('should reload enterprises after successful delete', async () => {
      mockDeleteEnterprise.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await flushPromises()

      mockGetEnterprises.mockClear()
      await wrapper.vm.deleteEnterprise(1)
      await flushPromises()

      expect(mockGetEnterprises).toHaveBeenCalled()
    })

    it('should delete correct enterprise by id', async () => {
      mockDeleteEnterprise.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteEnterprise(2)

      expect(mockDeleteEnterprise).toHaveBeenCalledWith(2)
    })
  })

  describe('Dialog Management', () => {
    it('should close dialog on cancel', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      await nextTick()

      wrapper.vm.dialogVisible = false
      await nextTick()

      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('should show dialog when editing', async () => {
      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.editEnterprise(mockEnterprises[0])

      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('should hide dialog after save', async () => {
      mockUpdateEnterprise.mockResolvedValue({ data: mockEnterprises[0] })

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      wrapper.vm.editForm = mockEnterprises[0]

      await wrapper.vm.saveEnterprise()
      await flushPromises()

      expect(wrapper.vm.dialogVisible).toBe(false)
    })
  })

  describe('Form Validation', () => {
    it('should have status options', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      await nextTick()

      expect(wrapper.html()).toContain('激活')
      expect(wrapper.html()).toContain('禁用')
    })

    it('should update form fields', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editForm = {
        id: 1,
        name: 'New Enterprise',
        contactPerson: 'New Contact',
        email: 'new@example.com',
        status: 'inactive',
        createdAt: '2024-01-01'
      }

      expect(wrapper.vm.editForm.name).toBe('New Enterprise')
      expect(wrapper.vm.editForm.contactPerson).toBe('New Contact')
      expect(wrapper.vm.editForm.status).toBe('inactive')
    })

    it('should have all required form fields', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      await nextTick()

      expect(wrapper.html()).toContain('企业名称')
      expect(wrapper.html()).toContain('联系人')
      expect(wrapper.html()).toContain('邮箱')
      expect(wrapper.html()).toContain('状态')
    })
  })

  describe('Enterprise Status Display', () => {
    it('should display active status correctly', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.html()).toContain('active')
    })

    it('should display inactive status correctly', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.html()).toContain('inactive')
    })
  })

  describe('Lifecycle', () => {
    it('should load enterprises on mount', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(mockGetEnterprises).toHaveBeenCalledTimes(1)
    })

    it('should initialize with empty state', () => {
      wrapper = createWrapper()

      expect(wrapper.vm.enterprises).toEqual([])
      expect(wrapper.vm.search).toBe('')
      expect(wrapper.vm.dialogVisible).toBe(false)
      expect(wrapper.vm.loading).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('should not crash on API error', async () => {
      const { ElMessage } = await import('element-plus')
      mockGetEnterprises.mockRejectedValue(new Error('API Error'))

      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.enterprises-view').exists()).toBe(true)
      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('should handle network errors gracefully', async () => {
      const { ElMessage } = await import('element-plus')
      mockGetEnterprises.mockRejectedValue(new Error('Network error'))

      wrapper = createWrapper()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('加载失败')
      expect(wrapper.vm.loading).toBe(false)
    })

    it('should handle update errors without crashing', async () => {
      const { ElMessage } = await import('element-plus')
      mockUpdateEnterprise.mockRejectedValue(new Error('Update error'))

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editForm = mockEnterprises[0]
      await wrapper.vm.saveEnterprise()

      expect(ElMessage.error).toHaveBeenCalled()
      expect(wrapper.find('.enterprises-view').exists()).toBe(true)
    })
  })

  describe('UI Interactions', () => {
    it('should have correct header layout', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const header = wrapper.find('.header')
      expect(header.exists()).toBe(true)
    })

    it('should display enterprise information in table', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.html()).toContain('Tech Corp')
      expect(wrapper.html()).toContain('John Doe')
      expect(wrapper.html()).toContain('contact@techcorp.com')
      expect(wrapper.html()).toContain('Innovation Ltd')
      expect(wrapper.html()).toContain('Jane Smith')
      expect(wrapper.html()).toContain('info@innovation.com')
    })

    it('should have edit and delete buttons', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const buttons = wrapper.findAll('button')
      const buttonTexts = buttons.map((btn: any) => btn.text())
      expect(buttonTexts).toContain('编辑')
      expect(buttonTexts).toContain('删除')
    })
  })

  describe('Data Integrity', () => {
    it('should preserve enterprise data during edit', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const originalEnterprise = { ...mockEnterprises[0] }
      await wrapper.vm.editEnterprise(mockEnterprises[0])

      expect(wrapper.vm.editForm).toEqual(originalEnterprise)
      expect(wrapper.vm.editForm).not.toBe(mockEnterprises[0]) // Should be a copy
    })

    it('should not modify original data when editing form', async () => {
      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.editEnterprise(mockEnterprises[0])
      wrapper.vm.editForm.name = 'Modified Name'

      expect(mockEnterprises[0].name).toBe('Tech Corp')
    })
  })
})
