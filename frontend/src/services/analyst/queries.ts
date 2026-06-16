import { useQuery, useMutation } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api-client"
import { z } from "zod"

const AnalystResponseSchema = z.object({
  response: z.string().nullable(),
  error: z.string().nullable(),
  remaining: z.any().nullable(),
})

const RateLimitSchema = z.object({
  allowed: z.boolean().optional(),
  remaining: z.any().nullable().optional(),
})

export type AnalystResponse = z.infer<typeof AnalystResponseSchema>

export function useAnalystQuery() {
  return useMutation({
    mutationFn: async (query: string) => {
      const data = await fetchApi<AnalystResponse>(`/api/query`, {
        method: "POST",
        body: JSON.stringify({ query }),
        requiredCapability: "businessQuestions",
      })
      return AnalystResponseSchema.parse(data)
    },
  })
}

export function useAnalystLimits() {
  return useQuery({
    queryKey: ["analyst", "limits"],
    queryFn: async () => {
      return fetchApi<any>(`/api/limits`, {
        requiredCapability: "businessQuestions",
      })
    },
    staleTime: 30 * 1000,
  })
}
