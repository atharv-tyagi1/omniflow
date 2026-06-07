import { z } from "zod"

// Zod schemas enforcing strict backend contracts
export const MetricTrendSchema = z.object({
  date: z.string(),
  value: z.number()
})

export const OverviewMetricsSchema = z.object({
  total_conversations: z.number(),
  conversation_trend: z.number().optional(),
  active_users: z.number(),
  user_trend: z.number().optional(),
  resolution_rate: z.number(),
  resolution_trend: z.number().optional(),
  csat_score: z.number(),
  csat_trend: z.number().optional(),
})

export type OverviewMetrics = z.infer<typeof OverviewMetricsSchema>
export type MetricTrend = z.infer<typeof MetricTrendSchema>
