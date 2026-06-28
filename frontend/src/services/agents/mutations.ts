import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api-client';
import { CreateAgentRequest, CreateAgentVersionRequest, Agent, AgentVersion } from './types';
import { agentKeys } from './queries';

export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ workspaceId, data }: { workspaceId: string; data: CreateAgentRequest }): Promise<Agent> => {
      const response = await fetchApi<any>('/api/v1/agents/', {
        method: 'POST',
        body: JSON.stringify(data),
        params: { workspace_id: workspaceId },
      });
      return response.data;
    },
    onSuccess: (_, { workspaceId }) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.list(workspaceId) });
    },
  });
}

export function useUpdateAgentVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ 
      workspaceId, 
      agentId, 
      data 
    }: { 
      workspaceId: string; 
      agentId: string; 
      data: CreateAgentVersionRequest 
    }): Promise<AgentVersion> => {
      const response = await fetchApi<any>(`/api/v1/agents/${agentId}/versions`, {
        method: 'POST',
        body: JSON.stringify(data),
        params: { workspace_id: workspaceId },
      });
      return response.data;
    },
    onSuccess: (_, { workspaceId, agentId }) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.detail(workspaceId, agentId) });
      queryClient.invalidateQueries({ queryKey: agentKeys.list(workspaceId) });
    },
  });
}
