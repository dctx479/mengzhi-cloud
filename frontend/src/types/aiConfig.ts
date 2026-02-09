export interface AIConfig {
  id: string;
  name: string;
  provider: 'openai' | 'azure' | 'anthropic' | 'custom';
  apiKey: string;
  endpoint?: string;
  model: string;
  isActive: boolean;
  createdAt: string;
}

export interface AIConfigForm {
  name: string;
  provider: 'openai' | 'azure' | 'anthropic' | 'custom';
  apiKey: string;
  endpoint?: string;
  model: string;
  isActive: boolean;
}
