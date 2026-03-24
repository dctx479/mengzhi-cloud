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
