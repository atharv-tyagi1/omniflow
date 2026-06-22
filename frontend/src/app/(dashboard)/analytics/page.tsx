"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { DashboardWidget } from "@/components/dashboard/DashboardWidget"
import { ChartContainer } from "@/components/dashboard/ChartContainer"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts"
import { PermissionGuard } from "@/components/layout/PermissionGuard"
import { canViewAnalytics } from "@/lib/permissions"
import { useAnalyticsOverview, useMetricTrend } from "@/services/analytics/queries"

export default function AnalyticsPage() {
  const { workspace } = useAuth()
  
  const overviewQuery = useAnalyticsOverview(workspace?.id ?? "", "7d")
  const trendQuery = useMetricTrend(workspace?.id ?? "", "conversation_volume", "7d")

  const isLoading = overviewQuery.isLoading || trendQuery.isLoading
  const isError = overviewQuery.isError || trendQuery.isError

  return (
    <PermissionGuard checkPermission={canViewAnalytics} featureName="Analytics">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Analytics</h1>
          <p className="text-[var(--color-text-muted)]">
            Deep dive into your conversation volume and agent performance.
          </p>
        </div>

        {isLoading && (
          <div className="flex justify-center py-12 text-[var(--color-text-muted)]">Loading analytics data...</div>
        )}

        {isError && (
          <div className="flex justify-center py-12 text-red-500">Failed to load analytics data.</div>
        )}

        {!isLoading && !isError && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
            <DashboardWidget title="Conversation Volume Trends" description="Total interactions over the last 7 days">
              <ChartContainer minHeight={300}>
                {trendQuery.data && trendQuery.data.length > 0 ? (
                  <AreaChart data={trendQuery.data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorSupport" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--color-primary-start)" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="var(--color-primary-start)" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'var(--color-surface)', 
                        border: '1px solid var(--color-border-strong)',
                        borderRadius: '8px',
                        color: 'var(--color-text-primary)'
                      }} 
                    />
                    <Area type="monotone" dataKey="value" stroke="var(--color-primary-start)" strokeWidth={2} fillOpacity={1} fill="url(#colorSupport)" />
                  </AreaChart>
                ) : (
                  <div className="flex items-center justify-center h-full text-[var(--color-text-muted)]">No trend data available</div>
                )}
              </ChartContainer>
            </DashboardWidget>

            <DashboardWidget title="Overview Metrics" description="High-level performance summary">
              <div className="flex flex-col gap-4 p-4 rounded-xl bg-[var(--color-surface-elevated)]">
                <div className="flex justify-between items-center border-b border-[var(--color-border-subtle)] pb-2">
                  <span className="text-[var(--color-text-muted)]">Total Conversations</span>
                  <span className="font-bold text-xl">{overviewQuery.data?.total_conversations ?? 0}</span>
                </div>
                <div className="flex justify-between items-center border-b border-[var(--color-border-subtle)] pb-2">
                  <span className="text-[var(--color-text-muted)]">Active Users</span>
                  <span className="font-bold text-xl">{overviewQuery.data?.active_users ?? 0}</span>
                </div>
                <div className="flex justify-between items-center border-b border-[var(--color-border-subtle)] pb-2">
                  <span className="text-[var(--color-text-muted)]">Resolution Rate</span>
                  <span className="font-bold text-xl">{overviewQuery.data?.resolution_rate ?? 0}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[var(--color-text-muted)]">CSAT Score</span>
                  <span className="font-bold text-xl">{overviewQuery.data?.csat_score ?? 0}</span>
                </div>
              </div>
            </DashboardWidget>
          </div>
        )}
      </div>
    </PermissionGuard>
  )
}
