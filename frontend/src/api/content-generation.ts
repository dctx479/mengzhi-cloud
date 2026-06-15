/**
 * 内容生成 API 服务
 */
import axios from 'axios'
import type {
  BatchTask,
  ContentTemplate,
  GenerationConfig,
  GenerationRequest,
  GenerationResponse,
  SavedConfig,
} from '@/types/content-generation'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const contentAPI = axios.create({
  baseURL: `${API_BASE}/v1/content-generation`,
  timeout: 120000,
})

// 添加 token 拦截器
contentAPI.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 添加响应拦截器 — 自动解包 {code, data, message} 结构
contentAPI.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body && 'data' in body && body.code === 200) {
      return { ...response, data: body.data }
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * 获取所有模板
 */
export async function getTemplates(): Promise<ContentTemplate[]> {
  const response = await contentAPI.get('/templates')
  return Array.isArray(response.data) ? response.data : []
}

/**
 * 获取指定类别的模板
 */
export async function getTemplatesByCategory(category: string): Promise<ContentTemplate[]> {
  const response = await contentAPI.get('/templates', { params: { category } })
  return Array.isArray(response.data) ? response.data : []
}

/**
 * 获取单个模板详情
 */
export async function getTemplateDetail(templateId: string): Promise<ContentTemplate> {
  const response = await contentAPI.get(`/templates/${templateId}`)
  return response.data
}

/**
 * 生成内容
 */
export async function generateContent(request: GenerationRequest): Promise<GenerationResponse[]> {
  const response = await contentAPI.post('/generate', request)
  const inner = response.data

  if (Array.isArray(inner)) {
    return inner.map((item: Record<string, unknown>) => ({
      id: (item.id as string) || `gen-${Date.now()}`,
      content: (item.content as string) ?? '',
      metadata: {
        length: item.length as number,
        content_type: item.content_type as string,
        style: item.style as string,
        platform: item.platform as string,
      }
    }))
  }

  return [{
    id: inner?.id || `gen-${Date.now()}`,
    content: inner?.content ?? '',
    metadata: {
      length: inner?.length,
      content_type: inner?.content_type,
      style: inner?.style,
      platform: inner?.platform,
    }
  }]
}

/**
 * 保存配置
 */
export async function saveConfig(name: string, config: GenerationConfig): Promise<SavedConfig> {
  const response = await contentAPI.post('/configs', { name, config })
  return response.data
}

/**
 * 获取已保存的配置列表
 */
export async function getSavedConfigs(): Promise<SavedConfig[]> {
  const response = await contentAPI.get('/configs')
  return Array.isArray(response.data) ? response.data : []
}

/**
 * 获取单个已保存的配置
 */
export async function getSavedConfig(configId: string): Promise<SavedConfig> {
  const response = await contentAPI.get(`/configs/${configId}`)
  return response.data
}

/**
 * 删除已保存的配置
 */
export async function deleteSavedConfig(configId: string): Promise<void> {
  await contentAPI.delete(`/configs/${configId}`)
}

/**
 * 创建模板（管理员）
 */
export async function createTemplate(data: {
  name: string
  description?: string
  category: string
  content_type: string
  platform: string
  system_prompt: string
  user_prompt_template: string
  variables?: unknown[]
  example_output?: string
  max_tokens?: number
  is_active?: boolean
}): Promise<ContentTemplate> {
  const response = await contentAPI.post('/templates', data)
  return response.data
}

/**
 * 更新模板（管理员）
 */
export async function updateTemplate(templateId: string, data: Partial<{
  name: string
  description: string
  category: string
  content_type: string
  platform: string
  system_prompt: string
  user_prompt_template: string
  variables: unknown[]
  example_output: string
  max_tokens: number
  is_active: boolean
}>): Promise<ContentTemplate> {
  const response = await contentAPI.put(`/templates/${templateId}`, data)
  return response.data
}

/**
 * 删除模板（管理员）
 */
export async function deleteTemplate(templateId: string): Promise<void> {
  await contentAPI.delete(`/templates/${templateId}`)
}

/**
 * 获取历史记录
 */
export async function getHistory(limit = 20, offset = 0): Promise<{ items: unknown[]; total: number }> {
  const response = await contentAPI.get('/history', { params: { limit, offset } })
  const data = response.data
  return (data && typeof data === 'object') ? data as { items: unknown[]; total: number } : { items: [], total: 0 }
}

/**
 * 获取统计数据
 */
export async function getStatistics(): Promise<Record<string, unknown>> {
  const response = await contentAPI.get('/statistics')
  return (response.data as Record<string, unknown>) ?? {}
}

/**
 * 创建批量内容生成任务（后台异步执行）
 */
export async function createBatchTask(request: GenerationRequest): Promise<BatchTask> {
 const response = await contentAPI.post("/tasks", { config: request })
 return response.data
}

/**
 * 获取批量任务列表
 */
export async function getBatchTasks(): Promise<BatchTask[]> {
  const response = await contentAPI.get('/tasks')
  return Array.isArray(response.data) ? response.data : []
}

/**
 * 取消批量任务
 */
export async function cancelBatchTask(taskId: string): Promise<void> {
  await contentAPI.post(`/tasks/${taskId}/cancel`)
}

/**
 * 导出批量任务结果
 */
export async function exportTaskResult(taskId: string, fmt: 'txt' | 'docx' | 'pdf'): Promise<void> {
  const res = await contentAPI.get<Blob>(`/tasks/${taskId}/export/${fmt}`, { responseType: 'blob' })
  const blob = res.data
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `batch-${taskId.slice(0, 8)}.${fmt}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * 重试失败的批量任务
 */
export async function retryBatchTask(taskId: string): Promise<BatchTask> {
  const response = await contentAPI.post(`/tasks/${taskId}/retry`)
  return response.data
}

/**
 * 批量导出多个任务结果
 */
export async function bulkExportTasks(taskIds: string[], format: 'txt' | 'docx' | 'pdf'): Promise<void> {
  const res = await contentAPI.post<Blob>('/tasks/bulk-export', { task_ids: taskIds, format }, { responseType: 'blob' })
  const blob = res.data
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `bulk-export-${Date.now()}.${format}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default contentAPI
