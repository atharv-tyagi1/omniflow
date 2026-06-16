"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useAnalyticsOverview, useMetricTrend } from "@/services/analytics/queries"
import { MetricCard } from "@/components/dashboard/MetricCard"
import { TrendAreaChart, MultiLineChart } from "@/components/charts/Charts"
import { SkeletonCard, SkeletonChart, ErrorState, EmptyState, PageHeader, SectionCard } from "@/components/ui/dashboard-primitives"
import {
  MessageSquare, Users, CheckCircle, TrendingUp, Star,
  PhoneCall, Send, AlertTriangle, Activity, RefreshCw
} from "lucide-react"

function useAutoRefresh(refetch: () => void, intervalMs = 30000) {
  const [lastRefresh, setLastRefresh] = React.useState(new Date())
  React.useEffect(() => {
    const id = setInterval(() => {
      refetch()
      setLastRefresh(new Date())
    }, intervalMs)
    return () => clearInterval(id)
  }, [refetch, intervalMs])
  return lastRefresh
}

export default function OverviewPage() {
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""

  const { data: overview, isLoading, error, refetch } = useAnalyticsOverview(workspaceId, "7d")
  const { data: convTrend, isLoading: trendLoading } = useMetricTrend(workspaceId, "conversations", "7d")

  const lastRefresh = useAutoRefresh(refetch)

  // Safely extract trend data for chart
  const trendData = React.useMemo(() => {
    if (!convTrend) return []
    return convTrend.map((d: any) => ({ date: d.date?.slice(5) ?? d.date, value: d.value }))
  }, [convTrend])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Executive Overview"
        subtitle="Real-time workspace performance metrics"
      >
        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refreshed {lastRefresh.toLocaleTimeString()}</span>
        </button>
      </PageHeader>

      {/* KPI Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
        {isLoading ? (
          Array(5).fill(0).map((_, i) => <SkeletonCard key={i} />)
        ) : error ? (
          <div className="col-span-full">
            <ErrorState message="Failed to load overview metrics." onRetry={refetch} />
          </div>
        ) : overview ? (
          <>
            <MetricCard
              title="Total Conversations"
              value={overview.total_conversations?.toLocaleString() ?? "—"}
              trend={overview.conversation_trend}
              icon={<MessageSquare className="h-4 w-4" />}
            />
            <MetricCard
              title="Active Users"
              value={overview.active_users?.toLocaleString() ?? "—"}
              trend={overview.user_trend}
              icon={<Users className="h-4 w-4" />}
            />
            <MetricCard
              title="Resolution Rate"
              value={overview.resolution_rate != null ? `${(overview.resolution_rate * 100).toFixed(1)}%` : "—"}
              trend={overview.resolution_trend}
              icon={<CheckCircle className="h-4 w-4" />}
            />
            <MetricCard
              title="Avg CSAT"
              value={overview.csat_score?.toFixed(2) ?? "—"}
              trend={overview.csat_trend}
              icon={<Star className="h-4 w-4" />}
            />
            <MetricCard
              title="Conversation Growth"
              value={overview.conversation_trend != null ? `${overview.conversation_trend > 0 ? "+" : ""}${overview.conversation_trend}%` : "—"}
              icon={<TrendingUp className="h-4 w-4" />}
            />
          </>
        ) : (
          <div className="col-span-full">
            <EmptyState title="No metrics yet" description="Data will appear as conversations occur." />
          </div>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-7">
        <div className="lg:col-span-4">
          <SectionCard title="Conversation Volume" subtitle="Past 7 days">
            {trendLoading ? (
              <div className="h-[280px] flex items-center justify-center">
                <SkeletonChart className="w-full h-full" />
              </div>
            ) : trendData.length > 0 ? (
              <TrendAreaChart data={trendData} dataKey="conversations" label="Conversations" color="#6366f1" />
            ) : (
              <EmptyState title="No trend data" description="Trend data accumulates over time." />
            )}
          </SectionCard>
        </div>

        <div className="lg:col-span-3 space-y-4">
          <SectionCard title="Quick Stats" subtitle="Channel & escalation breakdown">
            <div className="space-y-3">
              {[
                { label: "Telegram Volume", icon: <Send className="h-4 w-4 text-sky-400" />, value: "—" },
                { label: "Voice Volume", icon: <PhoneCall className="h-4 w-4 text-violet-400" />, value: "—" },
                { label: "Escalation Rate", icon: <AlertTriangle className="h-4 w-4 text-amber-400" />, value: "—" },
                { label: "Messages Processed", icon: <Activity className="h-4 w-4 text-emerald-400" />, value: "—" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                  <div className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                    {item.icon}
                    {item.label}
                  </div>
                  <span className="text-sm font-semibold text-[var(--color-text-primary)]">{item.value}</span>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
