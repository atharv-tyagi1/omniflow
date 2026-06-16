import { useQuery } from "@tanstack/react-query"
import { fetchApi, handleZodError } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { OverviewMetricsSchema, MetricTrendSchema } from "./schemas"
import { z } from "zod"

export function useAnalyticsOverview(workspaceId: string, period: string) {
  return useQuery({
    queryKey: queryKeys.analytics.overview(workspaceId, { period }),
    queryFn: async () => {
      const data = await fetchApi(`/api/v1/analytics/overview`, {
        params: { period },
        requiredCapability: "analyticsOverview",
      })
      try {
        return OverviewMetricsSchema.parse(data)
      } catch (error) {
        handleZodError(error)
      }
    },
    enabled: !!workspaceId,
    retry: (failureCount, error) => {
      // Do not retry validation errors or disabled capability errors
      if ((error as any).code === "VALIDATION_ERROR" || (error as any).code === "CAPABILITY_DISABLED") return false
      return failureCount < 3
    }
  })
}

export function useMetricTrend(workspaceId: string, metric: string, period: string) {
  return useQuery({
    queryKey: queryKeys.analytics.trends(workspaceId, metric, { period }),
    queryFn: async () => {
      const data = await fetchApi(`/api/v1/analytics/trends`, {
        params: { period, metric },
        requiredCapability: "analyticsTrends",
      })
      try {
        return z.array(MetricTrendSchema).parse(data)
      } catch (error) {
        handleZodError(error)
      }
    },
    enabled: !!workspaceId,
    retry: (failureCount, error) => {
      if ((error as any).code === "VALIDATION_ERROR" || (error as any).code === "CAPABILITY_DISABLED") return false
      return failureCount < 3
    }
  })
}
