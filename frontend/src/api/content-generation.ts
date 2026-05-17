/**
 * 内容生成 API 服务
 */
import axios from 'axios'
import type {
  ContentTemplate,
  GenerationConfig,
  GenerationRequest,
  GenerationResponse,
  BatchTask,
  SavedConfig,
} from '@/types/content-generation'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const contentAPI = axios.create({
  baseURL: `${API_BASE}/v1/content-generation`,
  timeout: 30000,
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
    // 后端某些端点返回 Pydantic 模型直接，不用 success_response 包装
    // 检查是否存在 code 和 data 字段（仅当两者都存在时才解包）
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body && 'data' in body && body.code === 200) {
      return { ...response, data: body.data }
    }
    // 否则直接返回原始 response.data（已是最终数据或 Pydantic 序列化对象）
    return response
  },
  (error) => Promise.reject(error)
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

  // Backend returns {content, length, content_type, style, platform}
  // Map to GenerationResponse format expected by caller
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

  // Single result case
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
 * 流式生成内容 (WebSocket)
 */
export function createGenerationWebSocket(taskId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsBaseUrl = import.meta.env.VITE_WS_BASE || `${protocol}//${window.location.host}/api`
  return new WebSocket(`${wsBaseUrl}/v1/content-generation/stream/${taskId}`)
}

/**
 * 获取批量任务状态
 */
export async function getBatchTaskStatus(taskId: string): Promise<BatchTask> {
  const response = await contentAPI.get(`/tasks/${taskId}`)
  return response.data
}

/**
 * 获取所有批量任务
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
 * 导出结果为 TXT
 */
export async function exportResultsAsText(taskId: string): Promise<string> {
  const response = await contentAPI.get(`/tasks/${taskId}/export/txt`, { responseType: 'text' })
  return response.data
}

/**
 * 导出结果为 DOCX
 */
export async function exportResultsAsDocx(taskId: string): Promise<Blob> {
  const response = await contentAPI.get(`/tasks/${taskId}/export/docx`, { responseType: 'blob' })
  return response.data
}

/**
 * 导出结果为 PDF
 */
export async function exportResultsAsPdf(taskId: string): Promise<Blob> {
  const response = await contentAPI.get(`/tasks/${taskId}/export/pdf`, { responseType: 'blob' })
  return response.data
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

export default contentAPI
