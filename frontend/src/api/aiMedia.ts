import request from '@/utils/request'
import type {
  AIMediaCostSummary,
  AIMediaProvider,
  AIMediaProviderForm,
  AIMediaProviderTestResult,
  AIMediaTask,
  MediaProviderType,
  MediaTaskStatus,
} from '@/types/aiMedia'

interface APIResponse<T> {
  code?: number
  data?: T
  message?: string
}

interface ListResponse<T> {
  items: T[]
  total?: number
  page?: number
}

/** Extract the nested `.data` field from the backend APIResponse wrapper.
 *  http.ts interceptor already strips the AxiosResponse layer, so `res` here
 *  is the JSON body: { code, data, message }.
 */
function unwrap<T>(res: unknown): T | undefined {
  const r = res as APIResponse<T>
  return r.data !== undefined ? r.data : undefined
}

const COST_SUMMARY_EMPTY: AIMediaCostSummary = { total_cost: 0, total_tasks: 0, by_provider: [] }

export const aiMediaApi = {
  getProviders: async (params?: { providerType?: MediaProviderType; includeInactive?: boolean }): Promise<AIMediaProvider[]> => {
    const res = await request.get<APIResponse<ListResponse<AIMediaProvider>>>('/v1/ai-media/admin/media-providers', {
      params,
    })
    const data = unwrap<ListResponse<AIMediaProvider>>(res)
    return data?.items ?? []
  },

  createProvider: async (data: AIMediaProviderForm): Promise<AIMediaProvider> => {
    const res = await request.post<APIResponse<AIMediaProvider>>('/v1/ai-media/admin/media-providers', data)
    const result = unwrap<AIMediaProvider>(res)
    if (!result) throw new Error('创建服务商失败：服务器未返回数据')
    return result
  },

  updateProvider: async (id: number, data: Partial<AIMediaProviderForm>): Promise<AIMediaProvider> => {
    const res = await request.put<APIResponse<AIMediaProvider>>(`/v1/ai-media/admin/media-providers/${id}`, data)
    const result = unwrap<AIMediaProvider>(res)
    if (!result) throw new Error('更新服务商失败：服务器未返回数据')
    return result
  },

  deleteProvider: async (id: number): Promise<void> => {
    await request.delete(`/v1/ai-media/admin/media-providers/${id}`)
  },

  testProvider: async (id: number): Promise<Pick<AIMediaProviderTestResult, 'success' | 'message'>> => {
    const res = await request.post<APIResponse<AIMediaProviderTestResult>>(
      `/v1/ai-media/admin/media-providers/${id}/test`
    )
    const result = unwrap<AIMediaProviderTestResult>(res)
    return { success: result?.success ?? false, message: result?.message ?? '测试请求未返回结果' }
  },

  healthCheckProvider: async (id: number): Promise<Pick<AIMediaProviderTestResult, 'success' | 'message'>> => {
    const res = await request.post<APIResponse<AIMediaProviderTestResult>>(
      `/v1/ai-media/admin/media-providers/${id}/health-check`
    )
    const result = unwrap<AIMediaProviderTestResult>(res)
    return { success: result?.success ?? false, message: result?.message ?? '健康检查未返回结果' }
  },

  getCosts: async (params?: { mediaType?: MediaProviderType }): Promise<AIMediaCostSummary> => {
    const res = await request.get<APIResponse<AIMediaCostSummary>>('/v1/ai-media/admin/media-generation/costs', {
      params,
    })
    return unwrap<AIMediaCostSummary>(res) ?? COST_SUMMARY_EMPTY
  },

  getTasks: async (params?: {
    status?: MediaTaskStatus
    mediaType?: MediaProviderType
    page?: number
    pageSize?: number
  }): Promise<{ items: AIMediaTask[]; total: number; page: number }> => {
    const res = await request.get<APIResponse<ListResponse<AIMediaTask>>>('/v1/ai-media/tasks', { params })
    const data = unwrap<ListResponse<AIMediaTask>>(res)
    return { items: data?.items ?? [], total: data?.total ?? 0, page: data?.page ?? 1 }
  },
}
