import { useQuery } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api-client"
import { z } from "zod"

const ConversationSchema = z.object({
  id: z.string(),
  channel: z.string().nullable().optional(),
  status: z.string(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  customer_id: z.string().nullable().optional(),
  title: z.string().nullable().optional(),
})

const ConversationListSchema = z.object({
  data: z.array(ConversationSchema),
  total: z.number().optional(),
  page: z.number().optional(),
  per_page: z.number().optional(),
})

export type Conversation = z.infer<typeof ConversationSchema>

interface ConversationFilters {
  status?: string
  channel?: string
  search?: string
  page?: number
  limit?: number
}

export function useConversations(workspaceId: string, filters: ConversationFilters = {}) {
  return useQuery({
    queryKey: ["conversations", "list", workspaceId, filters],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (filters.status) params.status = filters.status
      if (filters.channel) params.channel = filters.channel
      if (filters.search) params.search = filters.search
      if (filters.page) params.page = String(filters.page)
      if (filters.limit) params.limit = String(filters.limit)

      const data = await fetchApi<any>(`/api/v1/conversations`, { params })
      // Handle both array and wrapped response formats
      if (Array.isArray(data)) return { data, total: data.length }
      if (data?.data) return data
      return { data: [], total: 0 }
    },
    enabled: !!workspaceId,
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
  })
}

export function useConversationIntel(conversationId: string) {
  return useQuery({
    queryKey: ["conversations", "intel", conversationId],
    queryFn: async () => {
      const data = await fetchApi<any>(`/api/v1/intel/conversation/${conversationId}`)
      return data?.data?.intel ?? null
    },
    enabled: !!conversationId,
    staleTime: 5 * 60 * 1000,
  })
}
