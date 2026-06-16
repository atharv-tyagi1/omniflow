import { useQuery } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api-client"
import { z } from "zod"

const CustomerSchema = z.object({
  id: z.string(),
  name: z.string().nullish(),
  email: z.string().nullish(),
  phone: z.string().nullish(),
  external_id: z.string().nullish(),
  created_at: z.string().optional(),
  metadata: z.record(z.string(), z.any()).nullish(),
})

export type Customer = z.infer<typeof CustomerSchema>

export function useCustomers(workspaceId: string, params: Record<string, string> = {}) {
  return useQuery({
    queryKey: ["customers", "list", workspaceId, params],
    queryFn: async () => {
      const data = await fetchApi<any>(`/api/v1/customers`, { params })
      if (Array.isArray(data)) return data
      if (data?.data) return data.data
      return []
    },
    enabled: !!workspaceId,
    staleTime: 60 * 1000,
  })
}

export function useCustomer(customerId: string) {
  return useQuery({
    queryKey: ["customers", "detail", customerId],
    queryFn: async () => {
      const data = await fetchApi<any>(`/api/v1/customers/${customerId}`)
      return data?.data ?? data
    },
    enabled: !!customerId,
    staleTime: 2 * 60 * 1000,
  })
}
