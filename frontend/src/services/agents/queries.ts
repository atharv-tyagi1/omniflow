import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api-client';
import { Agent, AgentDetail } from './types';

export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (workspaceId: string) => [...agentKeys.lists(), workspaceId] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (workspaceId: string, id: string) => [...agentKeys.details(), workspaceId, id] as const,
};

export function useAgents(workspaceId: string | undefined) {
  return useQuery({
    queryKey: agentKeys.list(workspaceId!),
    queryFn: async (): Promise<Agent[]> => {
      const data = await fetchApi<Agent[]>('/api/v1/agents/');
      return data || [];
    },
    enabled: !!workspaceId,
  });
}

export function useAgent(workspaceId: string | undefined, agentId: string | undefined) {
  return useQuery({
    queryKey: agentKeys.detail(workspaceId!, agentId!),
    queryFn: async (): Promise<AgentDetail> => {
      const data = await fetchApi<AgentDetail>(`/api/v1/agents/${agentId}`);
      return data as any; // fetchApi strips the extra wrapped data if configured, but let's just cast to any and return. Actually fetchApi might return the parsed json directly.
    },
    enabled: !!workspaceId && !!agentId,
  });
}

export function useAgentRuns(workspaceId: string | undefined, agentId: string | undefined) {
  return useQuery({
    queryKey: [...agentKeys.details(), workspaceId, agentId, 'runs'],
    queryFn: async () => {
      const data = await fetchApi<any>(`/api/v1/agents/${agentId}/runs`);
      return data;
    },
    enabled: !!workspaceId && !!agentId,
  });
}
