import request from '@/utils/request';
import type { AIConfig, AIConfigApiItem, AIConfigForm } from '@/types/aiConfig';

/** 从后端 success_response 包装中提取内层 data */
function unwrap<T>(res: unknown): T {
  const r = res as { data?: T }
  return r.data !== undefined ? r.data : res as T
}

function normalizeAIConfig(item: AIConfigApiItem): AIConfig {
  return {
    id: String(item.id),
    name: item.name?.trim() || item.provider,
    provider: item.provider,
    apiKey: item.api_key || '',
    endpoint: item.base_url || '',
    model: item.default_model || '',
    isActive: item.is_active ?? true,
    createdAt: item.created_at || '',
  }
}

export interface ProviderInfo {
  id: string;
  name: string;
  group: string;
  enabled?: boolean;
}

export const getAIConfigs = async (enterpriseId: string): Promise<AIConfig[]> => {
  const res = await request.get<{ code: number; data: AIConfigApiItem[]; message: string }>(`/v1/enterprises/${enterpriseId}/ai-configs`)
  const items = unwrap<AIConfigApiItem[]>(res)
  return Array.isArray(items) ? items.map(normalizeAIConfig) : []
}

export const createAIConfig = async (enterpriseId: string, data: AIConfigForm): Promise<AIConfig> => {
  const res = await request.post<{ code: number; data: AIConfigApiItem; message: string }>(`/v1/enterprises/${enterpriseId}/ai-configs`, data)
  return normalizeAIConfig(unwrap<AIConfigApiItem>(res))
}

export const updateAIConfig = async (enterpriseId: string, configId: string, data: Partial<AIConfigForm>): Promise<AIConfig> => {
  const res = await request.patch<{ code: number; data: AIConfigApiItem; message: string }>(`/v1/enterprises/${enterpriseId}/ai-configs/${configId}`, data)
  return normalizeAIConfig(unwrap<AIConfigApiItem>(res))
}

export const deleteAIConfig = (enterpriseId: string, configId: string) =>
  request.delete(`/v1/enterprises/${enterpriseId}/ai-configs/${configId}`)

export const testAIConfig = async (enterpriseId: string, configId: string): Promise<{ success: boolean; message: string }> => {
  const res = await request.post<{ code: number; data: { success: boolean; message: string }; message: string }>(`/v1/enterprises/${enterpriseId}/ai-configs/${configId}/test`)
  return unwrap<{ success: boolean; message: string }>(res)
}

/** 获取当前用户可用的提供商列表 */
export const getAvailableProviders = async (): Promise<ProviderInfo[]> => {
  const res = await request.get<{ code: number; data: { providers: ProviderInfo[] }; message: string }>('/v1/available-providers')
  const data = unwrap<{ providers: ProviderInfo[] }>(res)
  return data?.providers ?? []
}

/** 管理员: 获取提供商设置（含启用状态） */
export const getProviderSettings = async (): Promise<{ providers: ProviderInfo[]; enabled_ids: string[] }> => {
  const res = await request.get<{ code: number; data: { providers: ProviderInfo[]; enabled_ids: string[] }; message: string }>('/admin/provider-settings')
  return unwrap<{ providers: ProviderInfo[]; enabled_ids: string[] }>(res)
}

/** 管理员: 更新提供商设置 */
export const updateProviderSettings = async (enabledIds: string[]): Promise<void> => {
  await request.put('/admin/provider-settings', { enabled_ids: enabledIds })
}

// ============================================
// 新增：全局AI服务商配置管理（管理员）
// ============================================

export interface GlobalAIConfig {
  id?: number
  provider: string
  provider_type: string
  api_endpoint: string
  api_key?: string
  api_key_encrypted?: string
  model_name: string
  is_active: boolean
  priority: number
  config_json?: Record<string, any>
  created_at?: string
  updated_at?: string
}

export interface TestResult {
  success: boolean
  message: string
  model?: string
}

/**
 * 获取所有AI服务商配置（管理员）
 */
export const getGlobalAIConfigs = async (): Promise<GlobalAIConfig[]> => {
  const res = await request.get<{ code: number; data: GlobalAIConfig[]; message: string }>('/v1/ai-config/')
  return unwrap<GlobalAIConfig[]>(res)
}

/**
 * 创建AI服务商配置（管理员）
 */
export const createGlobalAIConfig = async (data: GlobalAIConfig): Promise<void> => {
  await request.post('/v1/ai-config/', data)
}

/**
 * 更新AI服务商配置（管理员）
 */
export const updateGlobalAIConfig = async (provider: string, data: Partial<GlobalAIConfig>): Promise<void> => {
  await request.put(`/v1/ai-config/${provider}`, data)
}

/**
 * 删除AI服务商配置（管理员）
 */
export const deleteGlobalAIConfig = async (provider: string): Promise<void> => {
  await request.delete(`/v1/ai-config/${provider}`)
}

/**
 * 测试AI服务商连接（管理员）
 */
export const testGlobalAIConfig = async (provider: string): Promise<TestResult> => {
  const res = await request.post<{ code: number; data: TestResult; message: string }>(`/v1/ai-config/${provider}/test`)
  return unwrap<TestResult>(res)
}
