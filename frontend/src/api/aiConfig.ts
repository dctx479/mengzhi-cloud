import request from '@/utils/request';
import type { AIConfig, AIConfigForm } from '@/types/aiConfig';

export const getAIConfigs = (enterpriseId: string) =>
  request.get<AIConfig[]>(`/api/enterprises/${enterpriseId}/ai-configs`);

export const createAIConfig = (enterpriseId: string, data: AIConfigForm) =>
  request.post<AIConfig>(`/api/enterprises/${enterpriseId}/ai-configs`, data);

export const updateAIConfig = (enterpriseId: string, configId: string, data: Partial<AIConfigForm>) =>
  request.patch<AIConfig>(`/api/enterprises/${enterpriseId}/ai-configs/${configId}`, data);

export const deleteAIConfig = (enterpriseId: string, configId: string) =>
  request.delete(`/api/enterprises/${enterpriseId}/ai-configs/${configId}`);

export const testAIConfig = (enterpriseId: string, configId: string) =>
  request.post<{ success: boolean; message: string }>(`/api/enterprises/${enterpriseId}/ai-configs/${configId}/test`);
