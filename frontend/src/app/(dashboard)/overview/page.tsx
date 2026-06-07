"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { useAnalyticsOverview } from "@/services/analytics/queries"
import { MetricCard } from "@/components/dashboard/MetricCard"
import { MessageSquare, Users, CheckCircle, Star } from "lucide-react"

export default function OverviewPage() {
  const { workspace } = useAuth()
  const workspaceId = workspace?.id || ""
  
  const { 
    data: overview, 
    isLoading, 
    error,
    refetch 
  } = useAnalyticsOverview(workspaceId, "7d")

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Overview</h1>
        <p className="text-[var(--color-text-muted)]">
          Welcome back. Here's what's happening in your workspace today.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          Array(4).fill(0).map((_, i) => (
            <div key={i} className="h-32 rounded-2xl bg-[var(--color-surface-elevated)] animate-pulse" />
          ))
        ) : error ? (
          <div className="col-span-full rounded-2xl border border-[var(--color-error)] bg-[var(--color-error)]/10 p-4 text-[var(--color-error)]">
            Failed to load overview metrics.
          </div>
        ) : overview ? (
          <>
            <MetricCard
              title="Total Conversations"
              value={overview.total_conversations.toLocaleString()}
              trend={overview.conversation_trend}
              icon={<MessageSquare className="h-4 w-4" />}
            />
            <MetricCard
              title="Active Users"
              value={overview.active_users.toLocaleString()}
              trend={overview.user_trend}
              icon={<Users className="h-4 w-4" />}
            />
            <MetricCard
              title="Resolution Rate"
              value={`${(overview.resolution_rate * 100).toFixed(1)}%`}
              trend={overview.resolution_trend}
              icon={<CheckCircle className="h-4 w-4" />}
            />
            <MetricCard
              title="Average CSAT"
              value={overview.csat_score.toFixed(1)}
              trend={overview.csat_trend}
              icon={<Star className="h-4 w-4" />}
            />
          </>
        ) : null}
      </div>

      {/* Placeholders for widgets that use API capability registry and widget isolation */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="col-span-4 rounded-2xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] h-[400px] flex items-center justify-center text-[var(--color-text-muted)]">
          [Trend Chart Widget]
        </div>
        <div className="col-span-3 rounded-2xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] h-[400px] flex items-center justify-center text-[var(--color-text-muted)]">
          [Activity Feed Widget]
        </div>
      </div>
    </div>
  )
}
