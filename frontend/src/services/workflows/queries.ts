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
      if (Array.isArray(data)) return data
      if (data?.data) return data.data
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
