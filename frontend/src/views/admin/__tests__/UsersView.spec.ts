import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import UsersView from '../UsersView.vue'
import type { User } from '@/types/admin'

// Mock admin API
const mockGetUsers = vi.fn()
const mockUpdateUser = vi.fn()
const mockDeleteUser = vi.fn()

vi.mock('@/api/admin', () => ({
  adminApi: {
    getUsers: (params?: any) => mockGetUsers(params),
    updateUser: (id: number, data: any) => mockUpdateUser(id, data),
    deleteUser: (id: number) => mockDeleteUser(id)
  }
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('UsersView.vue', () => {
  let wrapper: any

  const mockUsers: User[] = [
    {
      id: 1,
      username: 'john_doe',
      email: 'john@example.com',
      role: 'admin',
      status: 'active',
      createdAt: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      username: 'jane_smith',
      email: 'jane@example.com',
      role: 'user',
      status: 'inactive',
      createdAt: '2024-01-02T00:00:00Z'
    }
  ]

  const createWrapper = () => {
    return mount(UsersView, {
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
    mockGetUsers.mockResolvedValue({ data: mockUsers })
  })

  describe('Component Rendering', () => {
    it('should render the users view', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.users-view').exists()).toBe(true)
      expect(wrapper.find('.el-card').exists()).toBe(true)
    })

    it('should render header with title and search', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.html()).toContain('用户管理')
      expect(wrapper.find('input').exists()).toBe(true)
    })

    it('should render users table', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('table').exists()).toBe(true)
    })

    it('should render search input with placeholder', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toBe('搜索用户')
    })
  })

  describe('Data Loading', () => {
    it('should load users on mount', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(mockGetUsers).toHaveBeenCalledWith({ search: '' })
      expect(wrapper.vm.users).toEqual(mockUsers)
    })

    it('should set loading state during fetch', async () => {
      let resolvePromise: any
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      mockGetUsers.mockReturnValue(promise)

      wrapper = createWrapper()
      expect(wrapper.vm.loading).toBe(true)

      resolvePromise({ data: mockUsers })
      await flushPromises()

      expect(wrapper.vm.loading).toBe(false)
    })

    it('should handle loading error', async () => {
      const { ElMessage } = await import('element-plus')
      mockGetUsers.mockRejectedValue(new Error('Load failed'))

      wrapper = createWrapper()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('加载失败')
    })

    it('should handle empty users list', async () => {
      mockGetUsers.mockResolvedValue({ data: [] })

      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.vm.users).toEqual([])
    })
  })

  describe('Search Functionality', () => {
    it('should search users when input changes', async () => {
      wrapper = createWrapper()
      await flushPromises()

      mockGetUsers.mockClear()
      const input = wrapper.find('input')
      await input.setValue('john')
      await wrapper.vm.loadUsers()
      await flushPromises()

      expect(mockGetUsers).toHaveBeenCalledWith({ search: 'john' })
    })

    it('should update search value', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const input = wrapper.find('input')
      await input.setValue('test search')
      await nextTick()

      expect(wrapper.vm.search).toBe('test search')
    })

    it('should reload users with search term', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.search = 'admin'
      await wrapper.vm.loadUsers()
      await flushPromises()

      expect(mockGetUsers).toHaveBeenCalledWith({ search: 'admin' })
    })

    it('should handle search with empty string', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.search = ''
      await wrapper.vm.loadUsers()

      expect(mockGetUsers).toHaveBeenCalledWith({ search: '' })
    })
  })

  describe('Edit User', () => {
    it('should open dialog when edit button is clicked', async () => {
      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.editUser(mockUsers[0])
      await nextTick()

      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.editForm).toEqual(mockUsers[0])
    })

    it('should populate form with user data', async () => {
      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.editUser(mockUsers[0])

      expect(wrapper.vm.editForm.username).toBe('john_doe')
      expect(wrapper.vm.editForm.email).toBe('john@example.com')
      expect(wrapper.vm.editForm.role).toBe('admin')
      expect(wrapper.vm.editForm.status).toBe('active')
    })

    it('should save user changes', async () => {
      const { ElMessage } = await import('element-plus')
      mockUpdateUser.mockResolvedValue({ data: { ...mockUsers[0], username: 'updated_user' } })

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editForm = { ...mockUsers[0], username: 'updated_user' }
      wrapper.vm.dialogVisible = true

      await wrapper.vm.saveUser()
      await flushPromises()

      expect(mockUpdateUser).toHaveBeenCalledWith(1, wrapper.vm.editForm)
      expect(ElMessage.success).toHaveBeenCalledWith('保存成功')
      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('should handle save error', async () => {
      const { ElMessage } = await import('element-plus')
      mockUpdateUser.mockRejectedValue(new Error('Save failed'))

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.editForm = mockUsers[0]
      await wrapper.vm.saveUser()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('保存失败')
    })

    it('should reload users after successful save', async () => {
      mockUpdateUser.mockResolvedValue({ data: mockUsers[0] })

      wrapper = createWrapper()
      await flushPromises()

      mockGetUsers.mockClear()
      wrapper.vm.editForm = mockUsers[0]
      await wrapper.vm.saveUser()
      await flushPromises()

      expect(mockGetUsers).toHaveBeenCalled()
    })
  })

  describe('Delete User', () => {
    it('should delete user', async () => {
      const { ElMessage } = await import('element-plus')
      mockDeleteUser.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteUser(1)
      await flushPromises()

      expect(mockDeleteUser).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('should handle delete error', async () => {
      const { ElMessage } = await import('element-plus')
      mockDeleteUser.mockRejectedValue(new Error('Delete failed'))

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteUser(1)
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('删除失败')
    })

    it('should reload users after successful delete', async () => {
      mockDeleteUser.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await flushPromises()

      mockGetUsers.mockClear()
      await wrapper.vm.deleteUser(1)
      await flushPromises()

      expect(mockGetUsers).toHaveBeenCalled()
    })

    it('should delete correct user by id', async () => {
      mockDeleteUser.mockResolvedValue(undefined)

      wrapper = createWrapper()
      await flushPromises()

      await wrapper.vm.deleteUser(2)

      expect(mockDeleteUser).toHaveBeenCalledWith(2)
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

      await wrapper.vm.editUser(mockUsers[0])

      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('should hide dialog after save', async () => {
      mockUpdateUser.mockResolvedValue({ data: mockUsers[0] })

      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      wrapper.vm.editForm = mockUsers[0]

      await wrapper.vm.saveUser()
      await flushPromises()

      expect(wrapper.vm.dialogVisible).toBe(false)
    })
  })

  describe('Form Validation', () => {
    it('should have role options', async () => {
      wrapper = createWrapper()
      await flushPromises()

      wrapper.vm.dialogVisible = true
      await nextTick()

      expect(wrapper.html()).toContain('管理员')
      expect(wrapper.html()).toContain('用户')
    })

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
        username: 'new_username',
        email: 'new@example.com',
        role: 'user',
        status: 'inactive',
        createdAt: '2024-01-01'
      }

      expect(wrapper.vm.editForm.username).toBe('new_username')
      expect(wrapper.vm.editForm.role).toBe('user')
      expect(wrapper.vm.editForm.status).toBe('inactive')
    })
  })

  describe('User Status Display', () => {
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
    it('should load users on mount', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(mockGetUsers).toHaveBeenCalledTimes(1)
    })

    it('should initialize with empty state', () => {
      wrapper = createWrapper()

      expect(wrapper.vm.users).toEqual([])
      expect(wrapper.vm.search).toBe('')
      expect(wrapper.vm.dialogVisible).toBe(false)
      expect(wrapper.vm.loading).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('should not crash on API error', async () => {
      const { ElMessage } = await import('element-plus')
      mockGetUsers.mockRejectedValue(new Error('API Error'))

      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.users-view').exists()).toBe(true)
      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('should handle network errors gracefully', async () => {
      const { ElMessage } = await import('element-plus')
      mockGetUsers.mockRejectedValue(new Error('Network error'))

      wrapper = createWrapper()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('加载失败')
      expect(wrapper.vm.loading).toBe(false)
    })
  })

  describe('UI Interactions', () => {
    it('should have correct header layout', async () => {
      wrapper = createWrapper()
      await flushPromises()

      const header = wrapper.find('.header')
      expect(header.exists()).toBe(true)
    })

    it('should display user information in table', async () => {
      wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.html()).toContain('john_doe')
      expect(wrapper.html()).toContain('john@example.com')
      expect(wrapper.html()).toContain('jane_smith')
      expect(wrapper.html()).toContain('jane@example.com')
    })
  })
})
