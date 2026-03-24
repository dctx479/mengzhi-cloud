/**
 * AI 模型配置 API（使用企业级 AI 配置端点）
 */
import http from '@/utils/http'
import { useUserStore } from '@/stores/user'

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

export const getModelConfigs = async (): Promise<{ data: Record<string, ModelConfig | null> }> => {
  try {
    const userStore = useUserStore()
    const enterpriseId = userStore.user?.id ?? '1'
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
  } catch {
    return { data: { deepseek: null, qwen: null, zhipu: null, custom: null } }
  }
}

export const saveModelConfig = async (provider: string, config: Partial<ModelConfig>): Promise<void> => {
  const userStore = useUserStore()
  const enterpriseId = userStore.user?.id ?? '1'
  await http.post(`/v1/enterprises/${enterpriseId}/ai-configs`, {
    name: `${provider}-config`,
    provider,
    apiKey: config.apiKey,
    endpoint: config.baseUrl,
    model: config.model,
    isActive: config.enabled ?? true,
  })
}
