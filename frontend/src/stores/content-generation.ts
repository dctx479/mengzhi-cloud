/**
 * 内容生成状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed, onScopeDispose } from 'vue'
import type {
  ContentTemplate,
  GenerationConfig,
  GenerationResult,
  BatchTask,
  TemplateCategory,
  SavedConfig,
} from '@/types/content-generation'
import * as contentAPI from '@/api/content-generation'

export const useContentGenerationStore = defineStore('contentGeneration', () => {
  // State - Templates
  const templates = ref<ContentTemplate[]>([])
  const selectedTemplate = ref<ContentTemplate | null>(null)
  const templatesLoading = ref(false)
  const templatesError = ref<string | null>(null)

  // State - Configuration
  const config = ref<GenerationConfig>({
    product_ids: [],
    template_id: '',
    count: 1,
    style: 'professional',
    word_count: 200,
    target_audience: [],
    keywords: [],
    avoid_words: '',
    temperature: 0.7,
  })

  // State - Generation
  const results = ref<GenerationResult[]>([])
  const generating = ref(false)
  const progress = ref(0)
  const generationError = ref<string | null>(null)

  // State - Batch Tasks
  const batchTasks = ref<BatchTask[]>([])
  const tasksLoading = ref(false)
  const currentTask = ref<BatchTask | null>(null)

  // State - Saved Configs
  const savedConfigs = ref<SavedConfig[]>([])
  const configsLoading = ref(false)

  // State - WebSocket
  let wsConnection: WebSocket | null = null

  // Computed
  const selectedCategory = computed(() => {
    return selectedTemplate.value?.category || ''
  })

  const filteredTemplates = computed(() => {
    if (!selectedTemplate.value) return []
    return templates.value.filter((t) => t.category === selectedTemplate.value?.category)
  })

  const templateCategories = computed(() => {
    const categories = new Map<string, { name: string; icon: string; count: number }>()
    templates.value.forEach((t) => {
      if (!categories.has(t.category)) {
        const categoryConfig = getCategoryInfo(t.category)
        categories.set(t.category, {
          name: categoryConfig.name,
          icon: categoryConfig.icon,
          count: 0,
        })
      }
      const cat = categories.get(t.category)!
      cat.count++
    })
    return Array.from(categories.entries()).map(([id, info]) => ({
      id,
      ...info,
    }))
  })

  const hasResults = computed(() => results.value.length > 0)
  const totalWordCount = computed(() => results.value.reduce((sum, r) => sum + r.word_count, 0))

  // Helper function for category info
  function getCategoryInfo(category: TemplateCategory) {
    const map: Record<TemplateCategory, { name: string; icon: string }> = {
      product: { name: '产品文案', icon: '📝' },
      slogan: { name: '广告语', icon: '💡' },
      marketing: { name: '营销方案', icon: '📊' },
      social: { name: '社交媒体', icon: '📱' },
      video: { name: '短视频脚本', icon: '🎬' },
    }
    return map[category]
  }

  // Actions
  const fetchTemplates = async () => {
    templatesLoading.value = true
    templatesError.value = null
    try {
      const data = await contentAPI.getTemplates()
      templates.value = data
    } catch (err) {
      templatesError.value = err instanceof Error ? err.message : 'Failed to fetch templates'
    } finally {
      templatesLoading.value = false
    }
  }

  const selectTemplate = (template: ContentTemplate) => {
    selectedTemplate.value = template
    config.value.template_id = template.id
  }

  const selectCategory = async (category: TemplateCategory) => {
    try {
      const data = await contentAPI.getTemplatesByCategory(category)
      templates.value = templates.value.filter((t) => t.category !== category)
      templates.value.push(...data)
    } catch (err) {
      templatesError.value = err instanceof Error ? err.message : 'Failed to fetch templates'
    }
  }

  const updateConfig = (newConfig: Partial<GenerationConfig>) => {
    config.value = { ...config.value, ...newConfig }
  }

  const addKeyword = (keyword: string) => {
    if (keyword && !config.value.keywords.includes(keyword)) {
      config.value.keywords.push(keyword)
    }
  }

  const removeKeyword = (keyword: string) => {
    config.value.keywords = config.value.keywords.filter((k) => k !== keyword)
  }

  const generateContent = async () => {
    if (!config.value.template_id || config.value.product_ids.length === 0) {
      generationError.value = 'Please select a template and at least one product'
      return
    }

    generating.value = true
    generationError.value = null
    progress.value = 0

    try {
      const request = {
        config: config.value,
      }

      const response = await contentAPI.generateContent(request)

      // Convert API response to GenerationResult format
      results.value = response.map((r, index) => ({
        id: `result-${Date.now()}-${index}`,
        template_id: config.value.template_id,
        product_id: config.value.product_ids[index % config.value.product_ids.length],
        content: r.content,
        word_count: r.content.split(/\s+/).length,
        rating: 0,
        edited: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }))

      progress.value = 100
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to generate content'
    } finally {
      generating.value = false
    }
  }

  const regenerateResult = async (result: GenerationResult) => {
    const index = results.value.indexOf(result)
    if (index === -1) return

    try {
      const response = await contentAPI.generateContent({
        config: config.value,
      })

      if (response.length > 0) {
        const newResult = response[0]
        results.value[index] = {
          ...result,
          content: newResult.content,
          word_count: newResult.content.split(/\s+/).length,
          edited: false,
          updated_at: new Date().toISOString(),
        }
      }
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to regenerate content'
    }
  }

  const updateResult = (resultId: string, content: string) => {
    const result = results.value.find((r) => r.id === resultId)
    if (result) {
      result.content = content
      result.word_count = content.split(/\s+/).length
      result.edited = true
      result.updated_at = new Date().toISOString()
    }
  }

  const rateResult = (resultId: string, rating: number) => {
    const result = results.value.find((r) => r.id === resultId)
    if (result) {
      result.rating = rating
    }
  }

  const deleteResult = (resultId: string) => {
    results.value = results.value.filter((r) => r.id !== resultId)
  }

  const clearResults = () => {
    results.value = []
  }

  const fetchBatchTasks = async () => {
    tasksLoading.value = true
    try {
      const tasks = await contentAPI.getBatchTasks()
      batchTasks.value = tasks
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to fetch tasks'
    } finally {
      tasksLoading.value = false
    }
  }

  const getBatchTask = async (taskId: string) => {
    try {
      const task = await contentAPI.getBatchTaskStatus(taskId)
      currentTask.value = task
      return task
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to fetch task'
      throw err
    }
  }

  const cancelBatchTask = async (taskId: string) => {
    try {
      await contentAPI.cancelBatchTask(taskId)
      const task = batchTasks.value.find((t) => t.id === taskId)
      if (task) {
        task.status = 'cancelled'
      }
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to cancel task'
    }
  }

  const exportResults = async (format: 'txt' | 'docx' | 'pdf', taskId?: string) => {
    try {
      const id = taskId || currentTask.value?.id
      if (!id) throw new Error('No task ID provided')

      let blob: Blob | string
      let filename: string

      if (format === 'txt') {
        blob = await contentAPI.exportResultsAsText(id)
        filename = `content-${id}.txt`
      } else if (format === 'docx') {
        blob = await contentAPI.exportResultsAsDocx(id)
        filename = `content-${id}.docx`
      } else {
        blob = await contentAPI.exportResultsAsPdf(id)
        filename = `content-${id}.pdf`
      }

      // Create download link
      if (typeof blob === 'string') {
        const element = document.createElement('a')
        element.setAttribute('href', `data:text/plain;charset=utf-8,${encodeURIComponent(blob)}`)
        element.setAttribute('download', filename)
        element.style.display = 'none'
        document.body.appendChild(element)
        element.click()
        document.body.removeChild(element)
      } else {
        const url = URL.createObjectURL(blob)
        const element = document.createElement('a')
        element.setAttribute('href', url)
        element.setAttribute('download', filename)
        element.style.display = 'none'
        document.body.appendChild(element)
        element.click()
        document.body.removeChild(element)
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to export results'
    }
  }

  const saveConfiguration = async (name: string) => {
    try {
      await contentAPI.saveConfig(name, config.value)
      await fetchSavedConfigs()
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to save configuration'
    }
  }

  const fetchSavedConfigs = async () => {
    configsLoading.value = true
    try {
      const configs = await contentAPI.getSavedConfigs()
      savedConfigs.value = configs
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to fetch saved configs'
    } finally {
      configsLoading.value = false
    }
  }

  const loadSavedConfig = async (configId: string) => {
    try {
      const savedConfig = await contentAPI.getSavedConfig(configId)
      config.value = savedConfig.config
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to load configuration'
    }
  }

  const deleteSavedConfig = async (configId: string) => {
    try {
      await contentAPI.deleteSavedConfig(configId)
      await fetchSavedConfigs()
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to delete configuration'
    }
  }

  const resetConfig = () => {
    config.value = {
      product_ids: [],
      template_id: '',
      count: 1,
      style: 'professional',
      word_count: 200,
      target_audience: [],
      keywords: [],
      avoid_words: '',
      temperature: 0.7,
    }
    selectedTemplate.value = null
    results.value = []
    generationError.value = null
    progress.value = 0
  }

  // WebSocket utilities
  const connectWebSocket = (taskId: string, onMessage: (data: any) => void, onError: (error: Event) => void) => {
    try {
      wsConnection = contentAPI.createGenerationWebSocket(taskId)

      wsConnection.onmessage = (event) => {
        const data = JSON.parse(event.data)
        onMessage(data)
      }

      wsConnection.onerror = onError

      wsConnection.onclose = () => {
        wsConnection = null
      }
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to connect WebSocket'
    }
  }

  const disconnectWebSocket = () => {
    if (wsConnection) {
      wsConnection.close()
      wsConnection = null
    }
  }

  // 自动清理 WebSocket 连接
  onScopeDispose(() => {
    disconnectWebSocket()
  })

  return {
    // State
    templates,
    selectedTemplate,
    templatesLoading,
    templatesError,
    config,
    results,
    generating,
    progress,
    generationError,
    batchTasks,
    tasksLoading,
    currentTask,
    savedConfigs,
    configsLoading,

    // Computed
    selectedCategory,
    filteredTemplates,
    templateCategories,
    hasResults,
    totalWordCount,

    // Actions
    fetchTemplates,
    selectTemplate,
    selectCategory,
    updateConfig,
    addKeyword,
    removeKeyword,
    generateContent,
    regenerateResult,
    updateResult,
    rateResult,
    deleteResult,
    clearResults,
    fetchBatchTasks,
    getBatchTask,
    cancelBatchTask,
    exportResults,
    saveConfiguration,
    fetchSavedConfigs,
    loadSavedConfig,
    deleteSavedConfig,
    resetConfig,
    connectWebSocket,
    disconnectWebSocket,
  }
})
