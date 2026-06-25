import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api-client"

export interface WorkflowDraftData {
  workflow: {
    id: string
    name: string
    trigger_type: string
    status: string
    active_version_id: string | null
  }
  draft_version_id: string | null
  nodes: any[]
  edges: any[]
}

export const useWorkflowDraft = (workspaceId: string, workflowId: string) => {
  return useQuery({
    queryKey: ["workflow_draft", workspaceId, workflowId],
    queryFn: async (): Promise<WorkflowDraftData> => {
      const res = await fetchApi(`/api/v1/workflows/${workflowId}`)
      return res.data
    },
    enabled: !!workspaceId && !!workflowId,
  })
}

export const useSaveDraft = (workspaceId: string, workflowId: string) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (draft: { nodes: any[]; edges: any[] }) => {
      return fetchApi(`/api/v1/workflows/${workflowId}/draft`, {
        method: "PUT",
        body: JSON.stringify(draft),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow_draft", workspaceId, workflowId] })
    },
  })
}

export const usePublishWorkflow = (workspaceId: string, workflowId: string) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      return fetchApi(`/api/v1/workflows/${workflowId}/publish`, {
        method: "POST",
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow_draft", workspaceId, workflowId] })
      queryClient.invalidateQueries({ queryKey: ["workflows", workspaceId] })
    },
  })
}
