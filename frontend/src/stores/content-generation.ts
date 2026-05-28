/**
 * 内容生成状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ContentTemplate,
  GenerationConfig,
  GenerationResult,
  TemplateCategory,
  SavedConfig,
} from '@/types/content-generation'
import * as contentAPI from '@/api/content-generation'

export const useContentGenerationStore = defineStore('contentGeneration', () => {
  // State - Templates
  const templates = ref<ContentTemplate[]>([])
  const selectedTemplate = ref<ContentTemplate | null>(null)
  const activeCategory = ref<string>('')  // 当前选中的分类过滤器
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
    platform: 'general',
    content_type: 'copy',
  })

  // State - Generation
  const results = ref<GenerationResult[]>([])
  const generating = ref(false)
  const progress = ref(0)
  const generationError = ref<string | null>(null)

  // State - Saved Configs
  const savedConfigs = ref<SavedConfig[]>([])
  const configsLoading = ref(false)

  // Computed
  const selectedCategory = computed(() => activeCategory.value)

  const filteredTemplates = computed(() => {
    if (!activeCategory.value) return templates.value
    return templates.value.filter((t) => t.category === activeCategory.value)
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

  function getCategoryInfo(category: TemplateCategory): { name: string; icon: string } {
    const map: Record<TemplateCategory, { name: string; icon: string }> = {
      product: { name: '产品文案', icon: '📝' },
      slogan: { name: '广告语', icon: '💡' },
      marketing: { name: '营销方案', icon: '📊' },
      social: { name: '社交媒体', icon: '📱' },
      video: { name: '短视频脚本', icon: '🎬' },
    }
    return map[category] ?? { name: category, icon: '📄' }
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
    // 切换分类过滤器，不重新请求（模板已全部加载）
    activeCategory.value = activeCategory.value === category ? '' : category
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
    if (config.value.product_ids.length === 0) {
      generationError.value = '请选择至少一个产品'
      return
    }

    if (generating.value) return

    generating.value = true
    generationError.value = null
    progress.value = 0

    try {
      const request = {
        config: config.value,
      }

      const response = await contentAPI.generateContent(request)

      const responseArray = Array.isArray(response) ? response : [response]

      results.value = responseArray.map((r, index) => ({
        id: `result-${Date.now()}-${index}`,
        template_id: config.value.template_id,
        product_id: config.value.product_ids[index % config.value.product_ids.length],
        content: String(r.content ?? ''),
        word_count: Math.max(0, (String(r.content ?? '')).replace(/\s/g, '').length),
        rating: 0,
        edited: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }))

      progress.value = 100
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to generate content'
      results.value = []
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

      if (Array.isArray(response) && response.length > 0 && response[0] && typeof response[0] === 'object' && 'content' in response[0]) {
        const newResult = response[0]
        results.value[index] = {
          ...result,
          content: String(newResult.content ?? ''),
          word_count: Math.max(0, (String(newResult.content ?? '')).replace(/\s/g, '').length),
          edited: false,
          updated_at: new Date().toISOString(),
        }
      } else {
        generationError.value = 'Invalid response format from API'
      }
    } catch (err) {
      generationError.value = err instanceof Error ? err.message : 'Failed to regenerate content'
    }
  }

  const updateResult = (resultId: string, content: string) => {
    const result = results.value.find((r) => r.id === resultId)
    if (result) {
      result.content = content
      result.word_count = Math.max(0, (content || '').replace(/\s/g, '').length)
      result.edited = true
      result.updated_at = new Date().toISOString()
    }
  }

  const rateResult = (resultId: string, rating: number) => {
    const result = results.value.find((r) => r.id === resultId)
    if (result) {
      result.rating = Math.min(5, Math.max(0, rating))
    }
  }

  const deleteResult = (resultId: string) => {
    results.value = results.value.filter((r) => r.id !== resultId)
  }

  const clearResults = () => {
    results.value = []
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
      platform: 'general',
      content_type: 'copy',
    }
    selectedTemplate.value = null
    results.value = []
    generationError.value = null
    progress.value = 0
  }

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
    saveConfiguration,
    fetchSavedConfigs,
    loadSavedConfig,
    deleteSavedConfig,
    resetConfig,
  }
})
