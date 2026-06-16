import { useQuery } from "@tanstack/react-query"
import { fetchApi, handleZodError } from "@/lib/api-client"
import { z } from "zod"

const TopicSchema = z.object({ topic: z.string(), count: z.number() })
const IntentSchema = z.object({ intent: z.string(), count: z.number() })

export const IntelSchemas = {
  topics: z.object({ data: z.object({ trending_topics: z.array(TopicSchema) }) }),
  intents: z.object({ data: z.object({ intent_distribution: z.array(IntentSchema) }) }),
  sentiment: z.object({ data: z.object({ sentiment_trend: z.record(z.string(), z.record(z.string(), z.number())) }) }),
}

export function useIntelTopics(workspaceId: string, days = 30) {
  return useQuery({
    queryKey: ["intel", "topics", workspaceId, days],
    queryFn: async () => {
      const data = await fetchApi<z.infer<typeof IntelSchemas.topics>>(`/api/v1/intel/topics/trending`, {
        params: { days: String(days) },
        requiredCapability: "intelTopics",
      })
      return data.data.trending_topics
    },
    enabled: !!workspaceId,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000,
  })
}

export function useIntelIntents(workspaceId: string, days = 30) {
  return useQuery({
    queryKey: ["intel", "intents", workspaceId, days],
    queryFn: async () => {
      const data = await fetchApi<z.infer<typeof IntelSchemas.intents>>(`/api/v1/intel/intents/distribution`, {
        params: { days: String(days) },
        requiredCapability: "intelTopics",
      })
      return data.data.intent_distribution
    },
    enabled: !!workspaceId,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000,
  })
}

export function useIntelSentiment(workspaceId: string, days = 30) {
  return useQuery({
    queryKey: ["intel", "sentiment", workspaceId, days],
    queryFn: async () => {
      const data = await fetchApi<z.infer<typeof IntelSchemas.sentiment>>(`/api/v1/intel/sentiment/trend`, {
        params: { days: String(days) },
        requiredCapability: "intelSentiment",
      })
      return data.data.sentiment_trend
    },
    enabled: !!workspaceId,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000,
  })
}
