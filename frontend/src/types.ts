// API Types matching FastAPI server

export interface ProjectRequest {
  project_overview: string;
  context?: Record<string, unknown>;
}

export interface FileInfo {
  path: string;
  language: string;
  content?: string;
}

export interface RequirementInfo {
  id: string;
  description: string;
  priority: string;
  status: string;
}

export interface ProjectPlanResponse {
  project_name: string;
  description: string;
  tech_stack: string[];
  requirements: RequirementInfo[];
}

export interface GeneratedCodeResponse {
  files: FileInfo[];
  language: string;
  framework?: string;
}

export interface EvaluationResponse {
  quality_level: string;
  score: number;
  issues: Array<{
    severity: string;
    message: string;
    line?: number;
  }>;
  suggestions: string[];
  summary: string;
}

export interface PipelineResponse {
  task_id: string;
  status: string;
  success: boolean;
  project_plan?: ProjectPlanResponse;
  generated_code?: GeneratedCodeResponse;
  evaluation?: EvaluationResponse;
  iterations: number;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_stage?: string;
  result?: PipelineResponse;
}

// API 설정 관련 타입
export type ProviderType = 'preset' | 'custom';

export type PresetProvider = 'openai' | 'anthropic' | 'google' | 'azure' | 'deepseek' | 'cohere' | 'mistral' | 'xai';

export interface ApiConfig {
  providerType: ProviderType;
  provider?: PresetProvider;
  customName?: string;
  customBaseUrl?: string;
  customModel?: string;
  apiKey: string;
  temperature?: number;
  maxTokens?: number;
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
  provider?: string;
  model?: string;
}
