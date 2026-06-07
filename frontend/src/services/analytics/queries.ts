import { useQuery } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { OverviewMetricsSchema, OverviewMetrics, MetricTrendSchema, MetricTrend } from "./schemas"
import { z } from "zod"

export function useAnalyticsOverview(workspaceId: string, period: string = "7d") {
  return useQuery({
    queryKey: queryKeys.analytics.overview(workspaceId, { period }),
    queryFn: async () => {
      const data = await fetchApi(`/api/v1/analytics/overview?workspace_id=${workspaceId}&period=${period}`)
      return OverviewMetricsSchema.parse(data)
    },
    enabled: !!workspaceId
  })
}

export function useAnalyticsTrends(workspaceId: string, metric: string, period: string = "30d") {
  return useQuery({
    queryKey: queryKeys.analytics.trends(workspaceId, metric, { period }),
    queryFn: async () => {
      const data = await fetchApi(`/api/v1/analytics/trends?workspace_id=${workspaceId}&metric=${metric}&period=${period}`)
      return z.array(MetricTrendSchema).parse(data.trends || data)
    },
    enabled: !!workspaceId
  })
}
