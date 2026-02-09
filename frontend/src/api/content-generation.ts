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

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000/api'

const contentAPI = axios.create({
  baseURL: `${API_BASE}/content-generation`,
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

/**
 * 获取所有模板
 */
export async function getTemplates(): Promise<ContentTemplate[]> {
  const response = await contentAPI.get<ContentTemplate[]>('/templates')
  return response.data
}

/**
 * 获取指定类别的模板
 */
export async function getTemplatesByCategory(category: string): Promise<ContentTemplate[]> {
  const response = await contentAPI.get<ContentTemplate[]>('/templates', {
    params: { category },
  })
  return response.data
}

/**
 * 获取单个模板详情
 */
export async function getTemplateDetail(templateId: string): Promise<ContentTemplate> {
  const response = await contentAPI.get<ContentTemplate>(`/templates/${templateId}`)
  return response.data
}

/**
 * 生成内容
 */
export async function generateContent(request: GenerationRequest): Promise<GenerationResponse[]> {
  const response = await contentAPI.post<GenerationResponse[]>('/generate', request)
  return response.data
}

/**
 * 流式生成内容 (WebSocket)
 */
export function createGenerationWebSocket(taskId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsBaseUrl = import.meta.env.VITE_WS_BASE || `${protocol}//${window.location.host}/api`
  return new WebSocket(`${wsBaseUrl}/content-generation/stream/${taskId}`)
}

/**
 * 获取批量任务状态
 */
export async function getBatchTaskStatus(taskId: string): Promise<BatchTask> {
  const response = await contentAPI.get<BatchTask>(`/tasks/${taskId}`)
  return response.data
}

/**
 * 获取所有批量任务
 */
export async function getBatchTasks(): Promise<BatchTask[]> {
  const response = await contentAPI.get<BatchTask[]>('/tasks')
  return response.data
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
  const response = await contentAPI.get(`/tasks/${taskId}/export/txt`, {
    responseType: 'text',
  })
  return response.data
}

/**
 * 导出结果为 DOCX
 */
export async function exportResultsAsDocx(taskId: string): Promise<Blob> {
  const response = await contentAPI.get(`/tasks/${taskId}/export/docx`, {
    responseType: 'blob',
  })
  return response.data
}

/**
 * 导出结果为 PDF
 */
export async function exportResultsAsPdf(taskId: string): Promise<Blob> {
  const response = await contentAPI.get(`/tasks/${taskId}/export/pdf`, {
    responseType: 'blob',
  })
  return response.data
}

/**
 * 保存配置
 */
export async function saveConfig(name: string, config: GenerationConfig): Promise<SavedConfig> {
  const response = await contentAPI.post<SavedConfig>('/configs', { name, config })
  return response.data
}

/**
 * 获取已保存的配置列表
 */
export async function getSavedConfigs(): Promise<SavedConfig[]> {
  const response = await contentAPI.get<SavedConfig[]>('/configs')
  return response.data
}

/**
 * 获取单个已保存的配置
 */
export async function getSavedConfig(configId: string): Promise<SavedConfig> {
  const response = await contentAPI.get<SavedConfig>(`/configs/${configId}`)
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
export async function getHistory(limit = 20, offset = 0): Promise<any> {
  const response = await contentAPI.get('/history', {
    params: { limit, offset },
  })
  return response.data
}

/**
 * 获取统计数据
 */
export async function getStatistics(): Promise<any> {
  const response = await contentAPI.get('/statistics')
  return response.data
}

export default contentAPI
