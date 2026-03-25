/**
 * AI 模型配置 API（使用企业级 AI 配置端点）
 */
import http from '@/utils/http'

interface ModelConfig {
  provider: string
  apiKey?: string
  baseUrl?: string
  model?: string
  enabled?: boolean
}

function unwrap<T>(res: unknown): T {
  const r = res as { data?: T } & T
  return r.data !== undefined ? r.data : r
}

/**
 * 获取当前企业的模型配置
 * @param enterpriseId - 企业ID（必需）
 * 
 * 注意: enterpriseId 必须由调用方提供（从 useUserStore 或路由参数获取）
 * API 层不应该依赖 Pinia store，以保持层级分离和可测试性
 */
export const getModelConfigs = async (enterpriseId: string): Promise<{ data: Record<string, ModelConfig | null> }> => {
  if (!enterpriseId) {
    throw new Error('enterpriseId is required')
  }
  
  try {
    const res = await http.get(`/v1/enterprises/${enterpriseId}/ai-configs`)
    const items = unwrap<any[]>(res)
    // 按 provider 分组
    const grouped: Record<string, ModelConfig | null> = {
      deepseek: null,
      qwen: null,
      zhipu: null,
      custom: null,
    }
    if (Array.isArray(items)) {
      for (const cfg of items) {
        const key = cfg.provider
        if (key && key in grouped) {
          grouped[key] = {
            provider: cfg.provider,
            apiKey: cfg.apiKey || cfg.api_key,
            baseUrl: cfg.endpoint || cfg.base_url,
            model: cfg.model,
            enabled: cfg.isActive ?? cfg.is_active ?? true,
          }
        }
      }
    }
    return { data: grouped }
  } catch (err) {
    console.error('Failed to fetch model configs:', err)
    return { data: { deepseek: null, qwen: null, zhipu: null, custom: null } }
  }
}

/**
 * 保存模型配置
 * @param enterpriseId - 企业ID（必需）
 * @param provider - 配置提供商
 * @param config - 配置数据
 * 
 * 注意: enterpriseId 必须由调用方提供，API 层不应该依赖 Pinia store
 */
export const saveModelConfig = async (enterpriseId: string, provider: string, config: Partial<ModelConfig>): Promise<void> => {
  if (!enterpriseId) {
    throw new Error('enterpriseId is required')
  }
  
  await http.post(`/v1/enterprises/${enterpriseId}/ai-configs`, {
    name: `${provider}-config`,
    provider,
    apiKey: config.apiKey,
    endpoint: config.baseUrl,
    model: config.model,
    isActive: config.enabled ?? true,
  })
}
