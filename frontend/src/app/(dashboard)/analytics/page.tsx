"use client"

import * as React from "react"
import { useAuth } from "@/context/AuthContext"
import { DashboardWidget } from "@/components/dashboard/DashboardWidget"
import { ChartContainer } from "@/components/dashboard/ChartContainer"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { PermissionGuard } from "@/components/layout/PermissionGuard"
import { canViewAnalytics } from "@/lib/permissions"

export default function AnalyticsPage() {
  const { workspace } = useAuth()
  
  // Mock data for the chart layout scaffolding
  const mockData = [
    { date: "Mon", support: 400, sales: 240, handoff: 40 },
    { date: "Tue", support: 300, sales: 139, handoff: 20 },
    { date: "Wed", support: 200, sales: 980, handoff: 60 },
    { date: "Thu", support: 278, sales: 390, handoff: 30 },
    { date: "Fri", support: 189, sales: 480, handoff: 15 },
    { date: "Sat", support: 239, sales: 380, handoff: 25 },
    { date: "Sun", support: 349, sales: 430, handoff: 45 },
  ]

  return (
    <PermissionGuard checkPermission={canViewAnalytics} featureName="Analytics">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">Analytics</h1>
          <p className="text-[var(--color-text-muted)]">
            Deep dive into your conversation volume and agent performance.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
          <DashboardWidget title="Conversation Volume Trends" description="Total interactions over the last 7 days">
            <ChartContainer minHeight={300}>
              <AreaChart data={mockData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
                <Area type="monotone" dataKey="support" stroke="var(--color-primary-start)" strokeWidth={2} fillOpacity={1} fill="url(#colorSupport)" />
              </AreaChart>
            </ChartContainer>
          </DashboardWidget>

          <DashboardWidget title="Agent Category Distribution" description="Breakdown of interactions by agent type">
            <div className="h-[300px] flex items-center justify-center rounded-xl bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]">
              [Pie Chart Placeholder]
            </div>
          </DashboardWidget>
        </div>
      </div>
    </PermissionGuard>
  )
}
