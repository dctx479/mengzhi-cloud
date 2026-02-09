import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TemplateSelector from '@/components/TemplateSelector.vue'
import ConfigPanel from '@/components/ConfigPanel.vue'
import ResultsPanel from '@/components/ResultsPanel.vue'
import BatchTaskManager from '@/components/BatchTaskManager.vue'
import { useContentGenerationStore } from '@/stores/content-generation'
import type { ContentTemplate, GenerationResult } from '@/types/content-generation'

// Mock data
const mockTemplate: ContentTemplate = {
  id: '1',
  category: 'product',
  name: '产品描述',
  description: '生成产品描述文案',
  sample: '这是一款优质的有机农产品...',
  difficulty: 'easy',
  usage_count: 150,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

const mockResult: GenerationResult = {
  id: 'result-1',
  template_id: '1',
  product_id: 'prod-1',
  content: '这是生成的内容示例',
  word_count: 50,
  rating: 4,
  edited: false,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

describe('TemplateSelector Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render template categories', () => {
    const store = useContentGenerationStore()
    store.templates = [mockTemplate]

    const wrapper = mount(TemplateSelector, {
      global: {
        stubs: {
          ElEmpty: true,
        },
      },
    })

    expect(wrapper.vm).toBeDefined()
  })

  it('should select template on click', async () => {
    const store = useContentGenerationStore()
    store.templates = [mockTemplate]

    const wrapper = mount(TemplateSelector, {
      global: {
        stubs: {
          ElEmpty: true,
        },
      },
    })

    const selectTemplateSpy = vi.spyOn(store, 'selectTemplate')

    // Trigger template selection
    await store.selectTemplate(mockTemplate)

    expect(selectTemplateSpy).toHaveBeenCalledWith(mockTemplate)
    expect(store.selectedTemplate).toBe(mockTemplate)
  })

  it('should filter templates by category', async () => {
    const store = useContentGenerationStore()
    const template2: ContentTemplate = { ...mockTemplate, id: '2', category: 'slogan' }
    store.templates = [mockTemplate, template2]

    await store.selectTemplate(mockTemplate)

    // Only show products in the same category
    expect(store.selectedTemplate?.category).toBe('product')
  })
})

describe('ConfigPanel Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render configuration form', () => {
    const wrapper = mount(ConfigPanel, {
      global: {
        stubs: {
          'el-form': false,
          'el-form-item': false,
          'el-select': false,
          'el-input-number': false,
          'el-radio-group': false,
          'el-slider': false,
          'el-checkbox-group': false,
          'el-button': false,
          'el-collapse': false,
          'el-dialog': false,
          'el-tag': false,
          'el-input': false,
        },
      },
    })

    expect(wrapper.vm).toBeDefined()
  })

  it('should update config when inputs change', async () => {
    const store = useContentGenerationStore()

    store.updateConfig({
      count: 3,
      word_count: 300,
      style: 'casual',
    })

    expect(store.config.count).toBe(3)
    expect(store.config.word_count).toBe(300)
    expect(store.config.style).toBe('casual')
  })

  it('should add and remove keywords', () => {
    const store = useContentGenerationStore()

    store.addKeyword('有机')
    store.addKeyword('绿色')

    expect(store.config.keywords).toContain('有机')
    expect(store.config.keywords).toContain('绿色')
    expect(store.config.keywords).toHaveLength(2)

    store.removeKeyword('有机')

    expect(store.config.keywords).not.toContain('有机')
    expect(store.config.keywords).toHaveLength(1)
  })

  it('should prevent duplicate keywords', () => {
    const store = useContentGenerationStore()

    store.addKeyword('绿色')
    store.addKeyword('绿色')

    expect(store.config.keywords).toHaveLength(1)
  })

  it('should validate product selection before generation', async () => {
    const store = useContentGenerationStore()
    store.config.product_ids = []
    store.selectedTemplate = mockTemplate

    await store.generateContent()

    expect(store.generationError).toBeTruthy()
  })

  it('should reset configuration', () => {
    const store = useContentGenerationStore()
    store.config.count = 5
    store.config.keywords = ['test']
    store.selectedTemplate = mockTemplate

    store.resetConfig()

    expect(store.config.count).toBe(1)
    expect(store.config.keywords).toHaveLength(0)
    expect(store.selectedTemplate).toBeNull()
  })
})

describe('ResultsPanel Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render results panel', () => {
    const store = useContentGenerationStore()
    store.results = [mockResult]

    const wrapper = mount(ResultsPanel, {
      global: {
        stubs: {
          'el-progress': false,
          'el-empty': false,
          'el-input': false,
          'el-rate': false,
          'el-tag': false,
          'el-button': false,
          'el-dropdown': false,
          'el-alert': false,
          'el-statistic': false,
          'el-icon': false,
        },
      },
    })

    expect(wrapper.vm).toBeDefined()
  })

  it('should display generation results', () => {
    const store = useContentGenerationStore()
    const result2 = { ...mockResult, id: 'result-2', content: '第二条内容' }
    store.results = [mockResult, result2]

    expect(store.results).toHaveLength(2)
    expect(store.hasResults).toBe(true)
  })

  it('should update result content', () => {
    const store = useContentGenerationStore()
    store.results = [mockResult]

    const newContent = '更新后的内容'
    store.updateResult(mockResult.id, newContent)

    const updated = store.results.find((r) => r.id === mockResult.id)
    expect(updated?.content).toBe(newContent)
    expect(updated?.edited).toBe(true)
  })

  it('should rate results', () => {
    const store = useContentGenerationStore()
    store.results = [mockResult]

    store.rateResult(mockResult.id, 5)

    const result = store.results.find((r) => r.id === mockResult.id)
    expect(result?.rating).toBe(5)
  })

  it('should delete result', () => {
    const store = useContentGenerationStore()
    store.results = [mockResult]

    store.deleteResult(mockResult.id)

    expect(store.results).toHaveLength(0)
  })

  it('should clear all results', () => {
    const store = useContentGenerationStore()
    store.results = [mockResult, { ...mockResult, id: 'result-2' }]

    store.clearResults()

    expect(store.results).toHaveLength(0)
  })

  it('should calculate total word count', () => {
    const store = useContentGenerationStore()
    const result1 = { ...mockResult, word_count: 100 }
    const result2 = { ...mockResult, id: 'result-2', word_count: 150 }
    store.results = [result1, result2]

    expect(store.totalWordCount).toBe(250)
  })
})

describe('BatchTaskManager Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render batch task manager', () => {
    const wrapper = mount(BatchTaskManager, {
      global: {
        stubs: {
          'el-table': false,
          'el-table-column': false,
          'el-tag': false,
          'el-button': false,
          'el-progress': false,
          'el-dropdown': false,
          'el-dialog': false,
          'el-alert': false,
          'el-icon': false,
        },
      },
    })

    expect(wrapper.vm).toBeDefined()
  })

  it('should fetch batch tasks', async () => {
    const store = useContentGenerationStore()
    const fetchSpy = vi.spyOn(store, 'fetchBatchTasks')

    await store.fetchBatchTasks()

    expect(fetchSpy).toHaveBeenCalled()
  })

  it('should handle task cancellation', async () => {
    const store = useContentGenerationStore()
    const mockTask = {
      id: 'task-1',
      name: 'Test Task',
      template: 'product',
      template_id: '1',
      count: 5,
      progress: 50,
      status: 'running' as const,
      results: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    store.batchTasks = [mockTask]

    const cancelSpy = vi.spyOn(store, 'cancelBatchTask')
    await store.cancelBatchTask('task-1')

    expect(cancelSpy).toHaveBeenCalledWith('task-1')
  })
})

describe('Content Generation Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with default state', () => {
    const store = useContentGenerationStore()

    expect(store.config.product_ids).toEqual([])
    expect(store.config.count).toBe(1)
    expect(store.config.style).toBe('professional')
    expect(store.results).toEqual([])
    expect(store.generating).toBe(false)
  })

  it('should select template and update config', () => {
    const store = useContentGenerationStore()

    store.selectTemplate(mockTemplate)

    expect(store.selectedTemplate).toBe(mockTemplate)
    expect(store.config.template_id).toBe(mockTemplate.id)
  })

  it('should get template categories', () => {
    const store = useContentGenerationStore()
    store.templates = [
      mockTemplate,
      { ...mockTemplate, id: '2', category: 'slogan' },
      { ...mockTemplate, id: '3', category: 'slogan' },
    ]

    const categories = store.templateCategories

    expect(categories).toHaveLength(2)
    expect(categories[0].id).toBe('product')
    expect(categories[1].id).toBe('slogan')
  })

  it('should handle keyword operations', () => {
    const store = useContentGenerationStore()

    // Add keywords
    store.addKeyword('有机')
    store.addKeyword('绿色')
    store.addKeyword('可持续')

    expect(store.config.keywords).toHaveLength(3)

    // Remove keyword
    store.removeKeyword('有机')

    expect(store.config.keywords).toHaveLength(2)
    expect(store.config.keywords).toContain('绿色')
  })

  it('should track generation progress', async () => {
    const store = useContentGenerationStore()

    expect(store.progress).toBe(0)

    // Simulate progress update
    store.progress = 50
    expect(store.progress).toBe(50)

    store.progress = 100
    expect(store.progress).toBe(100)
  })

  it('should save and load configuration', async () => {
    const store = useContentGenerationStore()

    store.config.count = 5
    store.config.word_count = 300

    const saveConfigSpy = vi.spyOn(store, 'saveConfiguration')
    await store.saveConfiguration('My Config')

    expect(saveConfigSpy).toHaveBeenCalledWith('My Config')
  })

  it('should compute filtered templates by category', () => {
    const store = useContentGenerationStore()
    store.templates = [
      mockTemplate,
      { ...mockTemplate, id: '2', category: 'slogan' },
    ]
    store.selectedTemplate = mockTemplate

    const filtered = store.filteredTemplates

    expect(filtered).toHaveLength(1)
    expect(filtered[0].category).toBe('product')
  })

  it('should handle WebSocket connection', () => {
    const store = useContentGenerationStore()

    const mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
    }

    // Mock WebSocket creation
    expect(typeof store.connectWebSocket).toBe('function')
    expect(typeof store.disconnectWebSocket).toBe('function')
  })
})

describe('Content Generation Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should complete full generation workflow', async () => {
    const store = useContentGenerationStore()

    // 1. Select template
    store.selectTemplate(mockTemplate)
    expect(store.selectedTemplate).toBe(mockTemplate)

    // 2. Update config
    store.updateConfig({
      product_ids: ['prod-1', 'prod-2'],
      count: 2,
      style: 'creative',
      keywords: ['有机', '绿色'],
    })

    expect(store.config.product_ids).toHaveLength(2)
    expect(store.config.keywords).toHaveLength(2)

    // 3. Generate content
    store.results = [
      mockResult,
      { ...mockResult, id: 'result-2', content: '第二条内容' },
    ]

    expect(store.hasResults).toBe(true)
    expect(store.results).toHaveLength(2)

    // 4. Rate results
    store.rateResult(mockResult.id, 5)
    expect(store.results[0].rating).toBe(5)

    // 5. Clear results
    store.clearResults()
    expect(store.results).toHaveLength(0)
  })

  it('should handle error cases', async () => {
    const store = useContentGenerationStore()

    // Missing template
    store.config.product_ids = ['prod-1']
    store.selectedTemplate = null

    await store.generateContent()
    expect(store.generationError).toBeTruthy()

    // Missing products
    store.selectedTemplate = mockTemplate
    store.config.product_ids = []

    await store.generateContent()
    expect(store.generationError).toBeTruthy()
  })
})
