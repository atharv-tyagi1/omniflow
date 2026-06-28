export type AgentModelConfig = {
  provider: string;
  model_name: string;
  config: Record<string, any>;
};

export type AgentPromptConfig = {
  system_prompt: string;
  welcome_prompt?: string;
  fallback_prompt?: string;
};

export type AgentVersion = {
  id: string;
  version_number: number;
  is_published: boolean;
  created_at: string;
  prompt?: AgentPromptConfig;
  model?: AgentModelConfig;
};

export type Agent = {
  id: string;
  name: string;
  category: string;
  is_active: boolean;
  created_at: string;
  active_version_id?: string;
};

export type AgentDetail = Agent & {
  versions: AgentVersion[];
};

export type CreateAgentRequest = {
  name: string;
  category: string;
  is_active?: boolean;
};

export type CreateAgentVersionRequest = {
  prompt: AgentPromptConfig;
  model: AgentModelConfig;
  publish?: boolean;
};

export type AgentRunSummary = {
  id: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  conversation_id: string;
};

export type AgentRunDetail = AgentRunSummary & {
  steps: Array<{
    id: string;
    type: string;
    latency_ms: number;
    payload: any;
  }>;
  decision_trace?: {
    id: string;
    model_used: string;
    cost_tokens: number;
    latency_ms: number;
    memory_references: any;
    knowledge_references: any;
    tool_calls: any;
    workflow_calls: any;
  };
};

export type AgentChatRequest = {
  message: string;
  conversation_id?: string;
  workspace_policies?: string;
};

export type AgentChatResponse = {
  request_id: string;
  content: string;
  status: string;
  run_id?: string;
  conversation_id: string;
  latency_ms: number;
  tokens_used: number;
  knowledge_used: boolean;
  memory_used: boolean;
  tool_calls: any[];
};

export type ToolPolicyRequest = {
  tool_type: string;
  tool_config?: Record<string, any>;
  allowed_inputs?: Record<string, any>;
  allowed_outputs?: Record<string, any>;
  rate_limit?: number;
  approval_required?: boolean;
};

export type ToolPolicyResponse = ToolPolicyRequest & {
  id: string;
  version_id: string;
};
