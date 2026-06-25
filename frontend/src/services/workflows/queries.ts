import { useQuery } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api-client"
import { z } from "zod"

const WorkflowSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: z.string().optional(),
  trigger_type: z.string().nullable().optional(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
  is_active: z.boolean().optional(),
})

export type Workflow = z.infer<typeof WorkflowSchema>

export function useWorkflows(workspaceId: string) {
  return useQuery({
    queryKey: ["workflows", "list", workspaceId],
    queryFn: async () => {
      const data = await fetchApi<any>(`/api/v1/workflows`)
      if (data?.workflows && Array.isArray(data.workflows)) return data.workflows
      if (Array.isArray(data)) return data
      if (data?.data?.workflows) return data.data.workflows
      return []
    },
    enabled: !!workspaceId,
    staleTime: 60 * 1000,
    refetchInterval: 60 * 1000,
  })
}

export function useTelegramStats(workspaceId: string) {
  return useQuery({
    queryKey: ["telegram", "stats", workspaceId],
    queryFn: async () => {
      const data = await fetchApi<any>(`/api/v1/telegram/stats`)
      return data
    },
    enabled: !!workspaceId,
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
  })
}

export const useWorkflowDetails = (workspaceId: string, workflowId: string) => {
  return useQuery({
    queryKey: ["workflow_details", workspaceId, workflowId],
    queryFn: async () => {
      const res = await fetchApi<any>(`/api/v1/workflows/${workflowId}`)
      return res.data
    },
    enabled: !!workspaceId && !!workflowId,
  })
}

export const useWorkflowRuns = (workspaceId: string, workflowId: string) => {
  return useQuery({
    queryKey: ["workflow_runs", workspaceId, workflowId],
    queryFn: async () => {
      const res = await fetchApi<any>(`/api/v1/workflows/${workflowId}/runs`)
      return res.data?.runs || []
    },
    enabled: !!workspaceId && !!workflowId,
  })
}

export const useWorkflowRunDetails = (workspaceId: string, workflowId: string, runId: string) => {
  return useQuery({
    queryKey: ["workflow_run_details", workspaceId, workflowId, runId],
    queryFn: async () => {
      const res = await fetchApi<any>(`/api/v1/workflows/${workflowId}/runs/${runId}`)
      return res.data
    },
    enabled: !!workspaceId && !!workflowId && !!runId,
  })
}
