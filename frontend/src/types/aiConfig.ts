export type AIProvider = 'openai' | 'azure' | 'anthropic' | 'deepseek' | 'qwen' | 'wenxin' | 'glm' | 'spark' | 'moonshot' | 'custom';

export interface AIConfig {
  id: string;
  name: string;
  provider: AIProvider;
  apiKey: string;
  endpoint?: string;
  model: string;
  isActive: boolean;
  createdAt: string;
}

export interface AIConfigForm {
  name: string;
  provider: AIProvider;
  apiKey: string;
  endpoint?: string;
  model: string;
  isActive: boolean;
}

export interface AIConfigApiItem {
  id: string | number;
  name?: string | null;
  provider: AIProvider;
  api_key?: string | null;
  base_url?: string | null;
  default_model?: string | null;
  is_active?: boolean | null;
  created_at?: string | null;
}
