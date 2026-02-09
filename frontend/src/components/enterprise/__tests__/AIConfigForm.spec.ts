import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import AIConfigForm from '../AIConfigForm.vue'
import type { AIConfigForm as AIConfigFormType } from '@/types/aiConfig'

describe('AIConfigForm.vue', () => {
  let wrapper: any

  const createWrapper = (props = {}) => {
    return mount(AIConfigForm, {
      props,
      global: {
        stubs: {
          'el-form': {
            template: '<form><slot /></form>',
            methods: {
              validate: vi.fn().mockResolvedValue(true)
            }
          },
          'el-form-item': {
            template: '<div><slot /></div>'
          },
          'el-input': {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue', 'type', 'placeholder', 'showPassword']
          },
          'el-select': {
            template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
            props: ['modelValue', 'placeholder']
          },
          'el-option': {
            template: '<option :value="value">{{ label }}</option>',
            props: ['label', 'value']
          },
          'el-switch': {
            template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
            props: ['modelValue']
          }
        }
      }
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('should render form with all fields', () => {
      wrapper = createWrapper()

      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.html()).toContain('配置名称')
      expect(wrapper.html()).toContain('AI提供商')
      expect(wrapper.html()).toContain('API密钥')
      expect(wrapper.html()).toContain('模型')
      expect(wrapper.html()).toContain('启用状态')
    })

    it('should render provider options correctly', () => {
      wrapper = createWrapper()

      const options = wrapper.findAll('option')
      expect(options.length).toBeGreaterThanOrEqual(4)

      const optionTexts = options.map((opt: any) => opt.text())
      expect(optionTexts).toContain('OpenAI')
      expect(optionTexts).toContain('Azure OpenAI')
      expect(optionTexts).toContain('Anthropic')
      expect(optionTexts).toContain('自定义')
    })

    it('should show endpoint field when provider is azure', async () => {
      wrapper = createWrapper()

      const select = wrapper.find('select')
      await select.setValue('azure')
      await nextTick()

      expect(wrapper.html()).toContain('端点地址')
    })

    it('should show endpoint field when provider is custom', async () => {
      wrapper = createWrapper()

      const select = wrapper.find('select')
      await select.setValue('custom')
      await nextTick()

      expect(wrapper.html()).toContain('端点地址')
    })

    it('should not show endpoint field for openai provider', async () => {
      wrapper = createWrapper()

      const select = wrapper.find('select')
      await select.setValue('openai')
      await nextTick()

      // Count how many times "端点地址" appears (should be 0 or only in v-if="false")
      const endpointCount = (wrapper.html().match(/端点地址/g) || []).length
      expect(endpointCount).toBe(0)
    })
  })

  describe('Form Data Binding', () => {
    it('should initialize with default values', () => {
      wrapper = createWrapper()

      const inputs = wrapper.findAll('input')
      const select = wrapper.find('select')

      expect(select.element.value).toBe('openai')
      expect(inputs[inputs.length - 1].element.checked).toBe(true) // isActive switch
    })

    it('should update form when modelValue prop changes', async () => {
      const modelValue: AIConfigFormType = {
        name: 'Test Config',
        provider: 'anthropic',
        apiKey: 'test-key',
        endpoint: '',
        model: 'claude-3-opus',
        isActive: false
      }

      wrapper = createWrapper({ modelValue })
      await nextTick()

      const inputs = wrapper.findAll('input')
      expect(inputs[0].element.value).toBe('Test Config')
      expect(wrapper.find('select').element.value).toBe('anthropic')
    })

    it('should emit update:modelValue when form data changes', async () => {
      wrapper = createWrapper()

      const nameInput = wrapper.findAll('input')[0]
      await nameInput.setValue('New Config')
      await nextTick()

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      const emittedValues = wrapper.emitted('update:modelValue')
      expect(emittedValues[emittedValues.length - 1][0]).toMatchObject({
        name: 'New Config'
      })
    })
  })

  describe('Form Validation', () => {
    it('should have validation rules for required fields', () => {
      wrapper = createWrapper()

      // Access the component instance to check rules
      const component = wrapper.vm
      expect(component.rules).toBeDefined()
      expect(component.rules.name).toBeDefined()
      expect(component.rules.provider).toBeDefined()
      expect(component.rules.apiKey).toBeDefined()
      expect(component.rules.model).toBeDefined()
    })

    it('should expose validate method', () => {
      wrapper = createWrapper()

      expect(wrapper.vm.validate).toBeDefined()
      expect(typeof wrapper.vm.validate).toBe('function')
    })

    it('should validate form successfully with valid data', async () => {
      wrapper = createWrapper()

      const result = await wrapper.vm.validate()
      expect(result).toBeTruthy()
    })
  })

  describe('User Interactions', () => {
    it('should handle name input change', async () => {
      wrapper = createWrapper()

      const nameInput = wrapper.findAll('input')[0]
      await nameInput.setValue('My AI Config')
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1][0].name).toBe('My AI Config')
    })

    it('should handle provider selection change', async () => {
      wrapper = createWrapper()

      const select = wrapper.find('select')
      await select.setValue('azure')
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1][0].provider).toBe('azure')
    })

    it('should handle API key input change', async () => {
      wrapper = createWrapper()

      const inputs = wrapper.findAll('input')
      const apiKeyInput = inputs[1] // Second input is API key
      await apiKeyInput.setValue('sk-test-key-123')
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1][0].apiKey).toBe('sk-test-key-123')
    })

    it('should handle model input change', async () => {
      wrapper = createWrapper()

      const inputs = wrapper.findAll('input')
      const modelInput = inputs[2] // Third input is model
      await modelInput.setValue('gpt-4')
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1][0].model).toBe('gpt-4')
    })

    it('should handle isActive switch toggle', async () => {
      wrapper = createWrapper()

      const inputs = wrapper.findAll('input')
      const switchInput = inputs[inputs.length - 1] // Last input is the switch
      await switchInput.setChecked(false)
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1][0].isActive).toBe(false)
    })
  })

  describe('Conditional Rendering', () => {
    it('should show endpoint field for azure provider', async () => {
      wrapper = createWrapper({
        modelValue: {
          name: '',
          provider: 'azure',
          apiKey: '',
          endpoint: '',
          model: '',
          isActive: true
        }
      })
      await nextTick()

      expect(wrapper.html()).toContain('端点地址')
    })

    it('should show endpoint field for custom provider', async () => {
      wrapper = createWrapper({
        modelValue: {
          name: '',
          provider: 'custom',
          apiKey: '',
          endpoint: '',
          model: '',
          isActive: true
        }
      })
      await nextTick()

      expect(wrapper.html()).toContain('端点地址')
    })

    it('should hide endpoint field for openai provider', async () => {
      wrapper = createWrapper({
        modelValue: {
          name: '',
          provider: 'openai',
          apiKey: '',
          endpoint: '',
          model: '',
          isActive: true
        }
      })
      await nextTick()

      const endpointCount = (wrapper.html().match(/端点地址/g) || []).length
      expect(endpointCount).toBe(0)
    })

    it('should hide endpoint field for anthropic provider', async () => {
      wrapper = createWrapper({
        modelValue: {
          name: '',
          provider: 'anthropic',
          apiKey: '',
          endpoint: '',
          model: '',
          isActive: true
        }
      })
      await nextTick()

      const endpointCount = (wrapper.html().match(/端点地址/g) || []).length
      expect(endpointCount).toBe(0)
    })
  })

  describe('Props and Emits', () => {
    it('should accept modelValue prop', () => {
      const modelValue: AIConfigFormType = {
        name: 'Test',
        provider: 'openai',
        apiKey: 'key',
        endpoint: '',
        model: 'gpt-4',
        isActive: true
      }

      wrapper = createWrapper({ modelValue })
      expect(wrapper.props('modelValue')).toEqual(modelValue)
    })

    it('should emit update:modelValue with correct structure', async () => {
      wrapper = createWrapper()

      const nameInput = wrapper.findAll('input')[0]
      await nameInput.setValue('Test Config')
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1][0]).toHaveProperty('name')
      expect(emitted[emitted.length - 1][0]).toHaveProperty('provider')
      expect(emitted[emitted.length - 1][0]).toHaveProperty('apiKey')
      expect(emitted[emitted.length - 1][0]).toHaveProperty('model')
      expect(emitted[emitted.length - 1][0]).toHaveProperty('isActive')
    })
  })
})
